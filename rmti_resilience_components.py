# Copyright 2026 Cesar Marolla
# Licensed under the Apache License, Version 2.0 (see ../LICENSE).
"""
rmti_resilience_components.py -- combining biological and care-system
resilience in the Risk Mechanism Theory Index (RMTI).

RESEARCH PROTOTYPE. Nothing here is validated against real outcomes. All
examples are synthetic. Not a medical device.

This module adds NO new equation to R = L * E * V * (1 - rho). It only
combines two components of the resilience term rho:

    rho_bio   -- intrinsic biological capacity to absorb, buffer and recover
                 from harm (the fraction of inherent risk absorbed by biology).
    rho_care  -- care-system capacity (for example, delivery of surveillance
                 or of a program), kept separate from intrinsic biology.

    rho = 1 - (1 - rho_bio) * (1 - rho_care)                       (S5)

Equivalently, 1 - rho = (1 - rho_bio) * (1 - rho_care): the unabsorbed
fractions multiply, so capacity is not counted twice.

Properties (all tested):
  * rho is bounded in [0, 1) when both components lie in [0, 1).
  * rho is monotone non-decreasing in each component.
  * rho is symmetric in its two arguments.
  * rho_bio = 0 returns rho_care exactly, and rho_care = 0 returns rho_bio.
  * Addition would overcount: 0.50 and 0.40 give 0.70, not 0.90.
  * With rho_bio fixed, R is proportional to (1 - rho_care).

Assumptions that must be stated wherever the combined rho is used:
  1. Independence. The combination treats biological and care-system
     absorption as acting independently on the same inherent risk. This is a
     proposition to be tested, not a finding.
  2. No double counting. rho_bio must be built from information that does not
     describe care delivery; rho_care must not include biological (for
     example, hepatic) reserve.
  3. Care-system capacity can also shape the consequence term C (for example,
     stage at detection). C is not modified here; the overlap between rho_care
     and C is a stated limitation of the framework.
"""
from decimal import Decimal

__all__ = ["combine_rho"]


def _check_component(name: str, x: float) -> None:
    if not 0.0 <= x < 1.0:
        raise ValueError(f"{name} must lie in [0, 1); got {x}")


def combine_rho(rho_bio: float, rho_care: float) -> float:
    """rho = 1 - (1 - rho_bio)(1 - rho_care). Bounded in [0, 1), monotone in
    each argument, and equal to rho_care when rho_bio = 0 (and vice versa).
    Example: 0.50 and 0.40 give 0.70, not the 0.90 that simple addition
    would give."""
    _check_component("rho_bio", rho_bio)
    _check_component("rho_care", rho_care)
    # Decimal arithmetic from the string form of each input, so that e.g.
    # rho_bio = 0 returns rho_care exactly (binary floats give
    # 0.44999999999999996 for 1 - (1 - 0) * (1 - 0.45)).
    return float(1 - (1 - Decimal(str(rho_bio))) * (1 - Decimal(str(rho_care))))


def _demo() -> None:
    print("rmti_resilience_components demo -- synthetic inputs, research prototype\n")
    print(f"rho_bio 0.50, rho_care 0.40 -> rho = {combine_rho(0.50, 0.40):.2f}  (addition would give 0.90)")
    print(f"rho_bio 0.30, rho_care 0.20 -> rho = {combine_rho(0.30, 0.20):.2f}")
    print(f"rho_bio 0.30, rho_care 0.50 -> rho = {combine_rho(0.30, 0.50):.2f}")
    r1 = 1 - combine_rho(0.30, 0.20)
    r2 = 1 - combine_rho(0.30, 0.50)
    print(f"with L, E, V fixed, R falls by {100 * (1 - r2 / r1):.1f}% (ratio of 1 - rho = {r2 / r1:.3f})")


if __name__ == "__main__":
    _demo()
