"""
Infrastructure contracts and interfaces for telemetry delivery (DIP).

Defines the abstract publisher interface to decouple the orchestrator and the
business logic from the underlying transport technology.
"""

from abc import ABC, abstractmethod
from helios_simulator.domain.enums import ConnectionState
from helios_simulator.domain.models import TelemetryPayload


class TelemetryPublisherInterface(ABC):
    """
    Formal contract for any component emitting telemetry toward Earth.
    Allows replacing Redis with MQTT, ZeroMQ or test stubs without altering the domain.
    """

    @abstractmethod
    def connect(self) -> bool:
        """
        Establishes the connection with the messaging server or bus.

        Returns:
            True if the connection succeeded, False if unavailable.
        """
        raise NotImplementedError

    @abstractmethod
    def publish_telemetry(self, payload: TelemetryPayload) -> bool:
        """
        Serializes and transmits the payload to the configured channel or queue.

        Args:
            payload: Consolidated instance with the crew member and cabin data.

        Returns:
            True if transmitted or enqueued successfully, False on critical loss.
        """
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """Gracefully releases network descriptors and connection resources."""
        raise NotImplementedError

    @abstractmethod
    def get_connection_state(self) -> ConnectionState:
        """
        Queries the current health state of the transport link.

        Returns:
            Operational state (CONNECTED, DISCONNECTED or RETRYING).
        """
        raise NotImplementedError
