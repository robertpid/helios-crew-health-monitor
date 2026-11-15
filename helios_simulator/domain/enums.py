"""
Domain enumerations for the deep space telemetry system.

Defines normative alert classifications and hazards from the NASA RIDGE framework.
"""

from enum import Enum


class AlertLevel(str, Enum):
    """Operational severity levels for preliminary assessments and alerts."""

    INFORMATIONAL = "INFORMATIONAL"
    CAUTION = "CAUTION"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class RidgeHazard(str, Enum):
    """Official framework of the 5 human spaceflight hazards (NASA HRP)."""

    R_RADIATION = "R - Space radiation"
    I_ISOLATION = "I - Isolation and confinement"
    D_DISTANCE = "D - Distance from Earth"
    G_GRAVITY = "G - Altered gravity fields"
    E_CLOSED_ENVIRONMENT = "E - Hostile and closed environments"


class MissionEnvironment(str, Enum):
    """
    Habitat and operational environment types for a space mission.
    Defines gravity, radiological and link delay conditions.
    """

    SPACE_STATION = "space_station"
    LUNAR_BASE = "lunar_base"
    SPACECRAFT = "spacecraft"
    MARS_BASE = "mars_base"


class ConnectionState(str, Enum):
    """Operational state of the telemetry link with the infrastructure layer."""

    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    RETRYING = "RETRYING"
