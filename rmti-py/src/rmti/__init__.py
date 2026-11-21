"""RMTI-Py: Risk Mechanism Theory Index (Marolla)."""
from .core import (  # noqa: F401
    C_INFRA, TIER_LABELS, TIER_THRESHOLDS, assess, assess_multi, boundary_margins, e_log,
    e_log_clipped, pct_reduction, rank_cohort, score, score_array, score_multi, tier, tier_index,
)
from .stochastic import UncertainParam, WOE_CONCENTRATION, simulate_rmti, woe_sensitivity  # noqa: F401
from .optimizer import Project, optimize_portfolio, project_from_inputs, budget_frontier  # noqa: F401
from . import elasticity  # noqa: F401

__version__ = "3.2.0"
# geospatial and domains are imported on demand:  rmti.geospatial, rmti.domains.urban, rmti.domains.hcc
