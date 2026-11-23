"""Thin gateway to the hash-locked RMTI engine in rmti_python/ (never displayed on the site)."""
import os
import sys

_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rmti_python")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core import rmti_core as core            # noqa: E402
from oncology import rmti_hcc as hcc          # noqa: E402
from oncology import rmti_stage34 as s34      # noqa: E402
from oncology import rmti_elasticity as elas  # noqa: E402

APP_TITLE = "Risk Mechanism Theory Index (RMTI)"
ENGINE_VERSION = core.__version__
DISCLAIMER = ("Research prototype. Not validated against outcomes, not a medical device, and not for "
              "patient-care or emergency decisions. Enter synthetic or published aggregate values only.")

TIER_LABELS = [lbl for _, lbl in core.TIER]
TIER_COLORS = {"Tier 1 - Low": "#16A34A", "Tier 2 - Moderate": "#CA8A04", "Tier 3 - High": "#EA580C",
               "Tier 4 - Severe": "#DC2626", "Tier 5 - Critical": "#7F1D1D"}
TIER_BANDS = [(0.0, 0.05), (0.05, 0.15), (0.15, 0.35), (0.35, 0.60), (0.60, 1.0)]


def tier_of(R: float) -> str:
    return core.tier(R)


def tier_num(label: str) -> int:
    return int(label.split()[1])


def short(label: str) -> str:
    n, _, rest = label.partition(" - ")
    return f"{n.replace('Tier ', '')} {rest}"


def albi(albumin_g_l: float, bilirubin_umol_l: float):
    """ALBI score and grade (Johnson 2015 cut-offs, as in the workbook)."""
    import math
    score = math.log10(max(bilirubin_umol_l, 1e-6)) * 0.66 + albumin_g_l * (-0.085)
    grade = 1 if score <= -2.60 else (2 if score <= -1.39 else 3)
    return round(score, 3), grade
