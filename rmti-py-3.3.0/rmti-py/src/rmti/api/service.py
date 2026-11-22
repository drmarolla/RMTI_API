# Copyright 2025-2026 Cesar Marolla. Apache-2.0.
"""Vectorised assessment math and tabular ingestion shared by the JSON, upload and FHIR endpoints.
All tiering goes through rmti.core so the API can never disagree with the library or the papers."""
from __future__ import annotations

import io
import re
from typing import Dict, List, Optional, Sequence

import numpy as np

from .. import __version__
from ..core import (C_INFRA, TIER_NAMES, TIER_POSTURE, TIER_RANGES, boundary_margins, score_array)
from .schemas import (AssessmentResult, Engine, ID_PATTERN, Margin, CohortSummary, TierBin)

_C = np.array([C_INFRA[i] for i in range(1, 6)])
REQUIRED = ("likelihood", "exposure", "vulnerability", "resilience")
OPTIONAL = ("record_id", "domain", "resilience_after", "consequence_level", "population")
_ID = re.compile(ID_PATTERN)


def engine() -> Engine:
    return Engine(version=__version__)


def assess_arrays(L, E, V, rho, rho_after=None, C=None, N=None) -> Dict[str, np.ndarray]:
    L, E, V, rho = (np.asarray(x, dtype=float) for x in (L, E, V, rho))
    s = score_array(L, E, V, rho)
    out = {"IR": s["IR"], "R": s["R"], "tier": s["tier_index"] + 1}
    cl = None if C is None else np.asarray(C, dtype=float)
    if cl is not None:
        ok = np.isfinite(cl)
        c = np.where(ok, _C[np.clip(np.nan_to_num(cl, nan=1).astype(int), 1, 5) - 1], np.nan)
        out["EAL"] = np.where(ok, L * c * (1 - rho), np.nan)
        if N is not None:
            n = np.asarray(N, dtype=float)
            out["equity"] = np.where(ok & np.isfinite(n) & (n > 0), out["EAL"] / (n / 1e6), np.nan)
    if rho_after is not None:
        ra = np.asarray(rho_after, dtype=float)
        ok = np.isfinite(ra)
        Ra = np.where(ok, s["IR"] * (1 - np.where(ok, ra, 0)), np.nan)
        out["R_after"] = Ra
        out["tier_after"] = np.where(ok, np.searchsorted((0.05, 0.15, 0.35, 0.60), np.nan_to_num(Ra), side="right") + 1, 0)
        with np.errstate(divide="ignore", invalid="ignore"):
            out["reduction"] = np.where(ok, (1 - (1 - np.where(ok, ra, 0)) / (1 - rho)) * 100, np.nan)
    return out


def _f(x, nd=6):
    return None if x is None or not np.isfinite(x) else round(float(x), nd)


def build_results(records: Sequence[dict], a: Dict[str, np.ndarray], with_margin: bool = False) -> List[AssessmentResult]:
    out = []
    for i, r in enumerate(records):
        t = int(a["tier"][i])
        res = AssessmentResult(
            record_id=r.get("record_id"), domain=r.get("domain"), inherent_risk=_f(a["IR"][i]), residual_risk=_f(a["R"][i]),
            tier=t, tier_label=TIER_NAMES[t - 1], posture=TIER_POSTURE[t - 1],
            expected_annual_loss=_f(a["EAL"][i]) if "EAL" in a else None,
            equity_rate_per_million=_f(a["equity"][i]) if "equity" in a else None)
        if "R_after" in a and np.isfinite(a["R_after"][i]):
            res.residual_risk_after = _f(a["R_after"][i])
            res.tier_after = int(a["tier_after"][i])
            res.risk_reduction_pct = _f(a["reduction"][i], 2)
        if with_margin:
            m = boundary_margins(r["likelihood"], r["exposure"], r["vulnerability"], r["resilience"])
            res.margin = Margin(lower_threshold=m["lower_threshold"], upper_threshold=m["upper_threshold"],
                                relative_change_to_lower=_f(m["rel_change_LEV_to_lower"]),
                                relative_change_to_upper=_f(m["rel_change_LEV_to_upper"]))
        out.append(res)
    return out


def summarize(R: np.ndarray, tiers: np.ndarray) -> CohortSummary:
    n = len(R)
    bins = [TierBin(tier=k + 1, label=TIER_NAMES[k], posture=TIER_POSTURE[k], range=TIER_RANGES[k],
                    count=int((tiers == k + 1).sum()), share=round(float((tiers == k + 1).mean()), 6)) for k in range(5)]
    return CohortSummary(n=n, residual_risk_mean=_f(R.mean()), residual_risk_median=_f(np.median(R)),
                         residual_risk_p90=_f(np.percentile(R, 90)), residual_risk_max=_f(R.max()), tier_distribution=bins)


def columns_from_models(records) -> Dict[str, np.ndarray]:
    def col(name, default=np.nan):
        return np.array([getattr(r, name) if getattr(r, name) is not None else default for r in records], dtype=float)
    return dict(L=col("likelihood"), E=col("exposure"), V=col("vulnerability"), rho=col("resilience"),
                rho_after=col("resilience_after") if any(r.resilience_after is not None for r in records) else None,
                C=col("consequence_level") if any(r.consequence_level is not None for r in records) else None,
                N=col("population") if any(r.population is not None for r in records) else None)


class TableError(ValueError):
    def __init__(self, message: str, errors: Optional[List[dict]] = None, status: int = 422):
        super().__init__(message)
        self.errors, self.status = errors or [], status


def read_table(blob: bytes, filename: str, max_rows: int):
    """Parse an uploaded CSV/Parquet. Row limits are enforced BEFORE materialising a Parquet file."""
    import pandas as pd
    name = (filename or "").lower()
    try:
        if name.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(blob), nrows=max_rows + 1, encoding="utf-8")
        elif name.endswith(".parquet"):
            import pyarrow.parquet as pq
            n = pq.ParquetFile(io.BytesIO(blob)).metadata.num_rows
            if n > max_rows:
                raise TableError(f"file has {n} rows; the limit is {max_rows}", status=413)
            df = pd.read_parquet(io.BytesIO(blob))
        else:
            raise TableError("unsupported file type; upload .csv or .parquet", status=415)
    except TableError:
        raise
    except Exception as exc:                                   # parser detail may quote file content: do not echo it
        raise TableError(f"could not parse file ({type(exc).__name__})", status=400)
    if len(df) > max_rows:
        raise TableError(f"file has more than {max_rows} rows", status=413)
    if len(df) == 0:
        raise TableError("file contains no rows")
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def validate_assessment_table(df, max_errors: int = 20):
    """Strict, all-or-nothing validation; returns (records, columns). Errors cite row/column, never cell values."""
    import pandas as pd
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise TableError("missing required columns: " + ", ".join(missing))
    errs: List[dict] = []

    def num(c, lo, hi, optional=False):
        s = pd.to_numeric(df[c], errors="coerce")
        bad = s.isna() & ((~df[c].isna()) if optional else True)
        bad |= (s < lo) | (s > hi)
        for i in np.flatnonzero(bad.to_numpy())[: max_errors - len(errs)]:
            errs.append({"row": int(i) + 1, "column": c, "problem": f"must be a number in [{lo}, {hi}]"})
        return s.to_numpy(dtype=float)

    cols = {k: num(c, 0, 1) for k, c in zip(("L", "E", "V", "rho"), REQUIRED)}
    cols["rho_after"] = num("resilience_after", 0, 1, True) if "resilience_after" in df else None
    cols["C"] = num("consequence_level", 1, 5, True) if "consequence_level" in df else None
    cols["N"] = num("population", 1e-12, 1e15, True) if "population" in df else None
    ids = None
    if "record_id" in df:
        ids = df["record_id"].astype(object).where(df["record_id"].notna(), None).tolist()
        for i, v in enumerate(ids):
            if v is not None and not _ID.match(str(v)) and len(errs) < max_errors:
                errs.append({"row": i + 1, "column": "record_id", "problem": "must match [A-Za-z0-9._:-]{1,64}"})
    if errs:
        raise TableError(f"{len(errs)} validation problem(s) (first {max_errors} shown)", errs)
    records = [{"record_id": None if ids is None or ids[i] is None else str(ids[i]),
                "domain": None, "likelihood": cols["L"][i], "exposure": cols["E"][i],
                "vulnerability": cols["V"][i], "resilience": cols["rho"][i]} for i in range(len(df))]
    return records, cols
