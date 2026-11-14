"""
Enumeraciones de dominio para el sistema de telemetría de espacio profundo.

Define clasificaciones normativas de alerta y peligros del marco RIDGE de la NASA.
"""

from enum import Enum


class NivelAlerta(str, Enum):
    """Niveles de severidad operacional para evaluaciones preliminares y alertas."""

    INFORMATIVA = "INFORMATIVA"
    PRECAUCION = "PRECAUCION"
    ADVERTENCIA = "ADVERTENCIA"
    CRITICA = "CRITICA"


class PeligroRidge(str, Enum):
    """Marco oficial de los 5 peligros del vuelo espacial humano (NASA HRP)."""

    R_RADIACION = "R - Radiación espacial"
    I_AISLAMIENTO = "I - Aislamiento y confinamiento"
    D_DISTANCIA = "D - Distancia de la Tierra"
    G_GRAVEDAD = "G - Campos de gravedad alterados"
    E_ENTORNO_CERRADO = "E - Ambientes hostiles y cerrados"


class EstadoConexion(str, Enum):
    """Estado operativo del enlace de telemetría con la capa de infraestructura."""

    CONECTADO = "CONECTADO"
    DESCONECTADO = "DESCONECTADO"
    REINTENTANDO = "REINTENTANDO"
