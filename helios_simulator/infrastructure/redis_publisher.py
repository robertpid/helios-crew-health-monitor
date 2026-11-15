"""
Infrastructure implementation for fault-tolerant Redis publishing.

Manages the persistent connection, automatic reconnection and local buffering
(Store-and-Forward) toward the Earth telemetry mailbox ('earth_telemetry_mailbox').
"""

from collections import deque
import logging
import socket
import time
import redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError, TimeoutError as RedisTimeoutError

from helios_simulator.config import RedisConfig
from helios_simulator.domain.enums import ConnectionState
from helios_simulator.domain.models import TelemetryPayload
from helios_simulator.infrastructure.publisher_interface import TelemetryPublisherInterface

logger = logging.getLogger(__name__)


class RedisTelemetryPublisher(TelemetryPublisherInterface):
    """
    Robust telemetry publisher over Redis.
    Applies the Single Responsibility Principle (SRP): it neither generates data nor
    evaluates rules, it only ensures reliable delivery of the serialized payload.
    """

    def __init__(self, config: RedisConfig | None = None) -> None:
        """
        Initializes the Redis publisher.

        Args:
            config: Network parameters and retry policies.
        """
        self._config = config or RedisConfig()
        self._client: redis.Redis | None = None
        self._state: ConnectionState = ConnectionState.DISCONNECTED
        self._memory_buffer_queue: deque[str] = deque(
            maxlen=self._config.memory_buffer_queue_limit
        )
        self._last_reconnect_attempt: float = 0.0

    def _probe_port_availability(self, timeout_seconds: float = 0.15) -> bool:
        """Fast preliminary socket open test to avoid TCP stalls on Windows."""
        try:
            with socket.create_connection(
                (self._config.host, self._config.port),
                timeout=timeout_seconds,
            ):
                return True
        except (OSError, socket.error):
            return False

    def connect(self) -> bool:
        """
        Starts the connection to the local Redis server and verifies availability via PING.

        Returns:
            True if the server responded successfully, False if unreachable.
        """
        # Immediate preliminary check without network stalls
        if not self._probe_port_availability():
            self._state = ConnectionState.DISCONNECTED
            self._last_reconnect_attempt = time.time()
            logger.info(
                "Redis server inactive at %s:%d. Link in resilient mode (Store-and-Forward active).",
                self._config.host,
                self._config.port,
            )
            return False

        try:
            logger.info(
                "Attempting to establish link with Redis server at %s:%d (Mailbox: %s)...",
                self._config.host,
                self._config.port,
                self._config.publish_channel,
            )
            self._client = redis.Redis(
                host=self._config.host,
                port=self._config.port,
                db=self._config.db,
                password=self._config.password,
                socket_timeout=self._config.connection_timeout_seconds,
                socket_connect_timeout=self._config.connection_timeout_seconds,
                decode_responses=True,
            )
            self._client.ping()
            self._state = ConnectionState.CONNECTED
            logger.info("Link successfully established with Redis at %s:%d", self._config.host, self._config.port)
            self._flush_memory_buffer()
            return True
        except (RedisConnectionError, RedisTimeoutError, RedisError) as error:
            self._state = ConnectionState.DISCONNECTED
            self._last_reconnect_attempt = time.time()
            logger.error(
                "Could not connect to Redis at %s:%d. Resilience mode activated: %s",
                self._config.host,
                self._config.port,
                str(error),
            )
            return False

    def _attempt_automatic_reconnect(self) -> bool:
        """
        Evaluates whether it is time to retry the connection, respecting the cooldown interval.

        Returns:
            True if the connection was restored, False otherwise.
        """
        now = time.time()
        if now - self._last_reconnect_attempt < self._config.reconnect_retry_interval_seconds:
            return False

        self._last_reconnect_attempt = now
        self._state = ConnectionState.RETRYING
        logger.info("Retrying automatic reconnection with the local Redis server...")
        return self.connect()

    def publish_telemetry(self, payload: TelemetryPayload) -> bool:
        """
        Serializes the payload to JSON and injects it into the Redis channel and queue.
        If Redis is unreachable, the message is retained in internal memory (Store-and-Forward)
        for later dispatch without losing mission information.

        Args:
            payload: Validated TelemetryPayload instance.

        Returns:
            True if published to Redis or secured in the local buffer, False on saturation.
        """
        payload_json = payload.model_dump_json()

        # If the link is down, try to reconnect
        if self._state != ConnectionState.CONNECTED:
            self._attempt_automatic_reconnect()

        # If the link is active, try to transmit
        if self._state == ConnectionState.CONNECTED and self._client is not None:
            try:
                # Reactive publication over Pub/Sub
                active_receivers = self._client.publish(
                    self._config.publish_channel,
                    payload_json,
                )
                # Persistent storage in a FIFO queue/list
                self._client.rpush(
                    self._config.publish_queue,
                    payload_json,
                )
                logger.info(
                    "Telemetry transmitted to '%s' (Subscribers: %d, Size: %d bytes). Day %d.",
                    self._config.publish_channel,
                    active_receivers,
                    len(payload_json),
                    payload.mission_day,
                )
                return True
            except (RedisConnectionError, RedisTimeoutError, RedisError) as send_error:
                self._state = ConnectionState.DISCONNECTED
                logger.error(
                    "Redis connection interrupted during transmission: %s. Buffering in memory...",
                    str(send_error),
                )
                self._enqueue_in_buffer(payload_json)
                return True

        # Link disconnected: buffer locally
        self._enqueue_in_buffer(payload_json)
        return True

    def _enqueue_in_buffer(self, payload_json: str) -> None:
        """Stores a payload in the in-memory FIFO safety queue."""
        self._memory_buffer_queue.append(payload_json)
        logger.warning(
            "Payload preserved in the local safety buffer. Messages waiting: %d/%d",
            len(self._memory_buffer_queue),
            self._config.memory_buffer_queue_limit,
        )

    def _flush_memory_buffer(self) -> None:
        """Transmits the messages held in the buffer once the link is restored."""
        if not self._memory_buffer_queue or self._client is None:
            return

        logger.info(
            "Restoring link: sending %d payloads accumulated in the buffer to Redis...",
            len(self._memory_buffer_queue),
        )
        successfully_sent = 0
        while self._memory_buffer_queue:
            message = self._memory_buffer_queue.popleft()
            try:
                self._client.publish(self._config.publish_channel, message)
                self._client.rpush(self._config.publish_queue, message)
                successfully_sent += 1
            except (RedisConnectionError, RedisTimeoutError, RedisError) as error:
                logger.error("Failed flushing buffer on a pending message: %s", str(error))
                self._memory_buffer_queue.appendleft(message)
                self._state = ConnectionState.DISCONNECTED
                break

        logger.info("Buffer transmission completed successfully: %d messages processed.", successfully_sent)

    def close(self) -> None:
        """Closes the connection with the Redis server."""
        if self._client is not None:
            try:
                self._client.close()
                logger.info("Redis connection closed gracefully.")
            except (RedisConnectionError, RedisTimeoutError, RedisError) as error:
                logger.error("Error closing the Redis connection: %s", str(error))
            finally:
                self._client = None
                self._state = ConnectionState.DISCONNECTED

    def get_connection_state(self) -> ConnectionState:
        """Returns the current connectivity state."""
        return self._state

    @property
    def buffered_messages(self) -> int:
        """Number of messages pending delivery in the local buffer."""
        return len(self._memory_buffer_queue)
