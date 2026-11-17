"""
Mathematical and stochastic modeling utilities (DRY).

Centralizes the routines for Gaussian noise generation, physiological fluctuations
and decay models in accordance with aerospace simulation guidelines.
"""

import math
import random


def generate_gaussian_noise(
    mean_value: float,
    standard_deviation: float,
    lower_bound: float | None = None,
    upper_bound: float | None = None,
) -> float:
    """
    Generates a normally distributed value, optionally clamped between bounds.

    Args:
        mean_value: Mean of the distribution.
        standard_deviation: Standard deviation of the noise.
        lower_bound: Optional lower bound.
        upper_bound: Optional upper bound.

    Returns:
        Adjusted and clamped float value.
    """
    value = random.gauss(mean_value, standard_deviation)
    if lower_bound is not None and value < lower_bound:
        value = lower_bound
    if upper_bound is not None and value > upper_bound:
        value = upper_bound
    return round(value, 3)


def evaluate_event_probability(probability: float) -> bool:
    """
    Determines whether a stochastic event occurs given its uniform probability.

    Args:
        probability: Value between 0.0 and 1.0 defining the occurrence rate.

    Returns:
        True if the event triggered, False otherwise.
    """
    if probability <= 0.0:
        return False
    if probability >= 1.0:
        return True
    return random.random() < probability


def compute_cumulative_bone_loss(
    mission_day: int,
    monthly_rate_pct: float = 1.5,
) -> float:
    """
    Computes the estimated cumulative bone loss per the studies of NASA's
    Human System Risk Board and Mir cosmonaut data (1.0% to 1.5% monthly).

    Formula: (mission_day / 30) * monthly_rate_pct

    Args:
        mission_day: Days elapsed in a microgravity environment.
        monthly_rate_pct: Average loss percentage per month (30 days).

    Returns:
        Estimated percentage of bone mass loss.
    """
    if mission_day <= 0:
        return 0.0
    loss = (mission_day / 30.0) * monthly_rate_pct
    return round(loss, 3)


def round_telemetry(value: float, decimals: int = 2) -> float:
    """
    Normalizes and rounds telemetry values for serialized transmission.

    Args:
        value: Raw decimal number.
        decimals: Number of significant decimal digits.

    Returns:
        Rounded float.
    """
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return round(value, decimals)
