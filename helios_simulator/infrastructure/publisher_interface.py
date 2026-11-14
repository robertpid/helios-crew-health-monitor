"""
Contratos e interfaces de infraestructura para el envío de telemetría (DIP).

Define la interfaz abstracta del publicador para desacoplar el orquestador
y la lógica de negocio de la tecnología de transporte subyacente.
"""

from abc import ABC, abstractmethod
from helios_simulator.domain.enums import EstadoConexion
from helios_simulator.domain.models import TelemetriaPayload


class TelemetryPublisherInterface(ABC):
    """
    Contrato formal para cualquier componente emisor de telemetría hacia Tierra.
    Permite el reemplazo de Redis por MQTT, ZeroMQ o stubs de pruebas sin alterar el dominio.
    """

    @abstractmethod
    def conectar(self) -> bool:
        """
        Establece la conexión con el servidor o bus de mensajería.

        Returns:
            True si la conexión fue exitosa, False en caso de indisponibilidad.
        """
        raise NotImplementedError

    @abstractmethod
    def publicar_telemetria(self, payload: TelemetriaPayload) -> bool:
        """
        Serializa y transmite el payload al canal o cola configurada.

        Args:
            payload: Instancia consolidada con los datos del tripulante y cabina.

        Returns:
            True si se transmitió o encoló exitosamente, False si hubo pérdida crítica.
        """
        raise NotImplementedError

    @abstractmethod
    def cerrar(self) -> None:
        """Libera de forma ordenada los descriptores de red y recursos de conexión."""
        raise NotImplementedError

    @abstractmethod
    def obtener_estado_conexion(self) -> EstadoConexion:
        """
        Consulta el estado de salud actual del enlace de transporte.

        Returns:
            Estado operacional (CONECTADO, DESCONECTADO o REINTENTANDO).
        """
        raise NotImplementedError
