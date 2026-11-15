"""
H.E.L.I.O.S. compact telemetry record (persistence and link format).

This is the format that is STORED and TRANSMITTED. It carries exclusively stable
codes and numeric values; all descriptive text is reconstructed on the client
from the codebook (`telemetry_codebook.py`), which is downloaded once per session.

The keys are deliberately short: at 0.5 Hz over 120 days, every byte of a field
name is repeated 5,184,000 times.
"""

from pydantic import BaseModel, ConfigDict, Field

from helios_inference.domain.telemetry_codebook import SCHEMA_VERSION


class CompactTelemetryRecord(BaseModel):
    """One inference cycle expressed in codes and numbers."""

    model_config = ConfigDict(frozen=True)

    v: int = Field(default=SCHEMA_VERSION, description="Version of the code schema.")
    ts: int = Field(..., description="UTC timestamp in seconds since the Unix epoch.")
    mis: str = Field(..., description="Mission identifier.")
    ast: str = Field(..., description="Astronaut identifier.")
    day: int = Field(..., description="Operational mission day.")

    # Decision vectors of Brains 1 and 2 (0/1 flags)
    amb: list[int] = Field(..., description="Environmental vector R^3 [co2, radiation, pressure].")
    bio: list[int] = Field(..., description="Biometric vector R^4 [pulse, sleep, bone, sans].")
    sol: int = Field(default=0, description="Solar event active (selects the radiation template).")

    # Raw metrics in the canonical order of METRIC_ORDER
    met: list[float] = Field(..., description="Positional numeric values per metric_order.")

    # Brain 3: dominant edge of the Kronecker graph
    kr: int = Field(..., description="Argmax index of the critical edge (-1 = nominal).")
    krs: float = Field(..., description="Weighted severity score of the edge.")
    krx: int = Field(default=0, description="Severe physiological stress (exceeds the threshold).")

    # Brain 4: ASTRA
    cos: float = Field(..., description="Cosine similarity against the cognitive baseline.")
    inc: int = Field(default=0, description="Cognitive incongruence detected.")

    # Decision matrix: rule codes. A '!' suffix indicates a level escalation.
    rg: list[str] = Field(default_factory=list, description="Active rule codes (e.g. 'CX-03!').")

    ms: float = Field(..., description="Cycle compute time in milliseconds.")
