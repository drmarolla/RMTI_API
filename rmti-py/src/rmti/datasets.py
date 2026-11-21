"""Bundled datasets. ``paper`` sets are the published inputs; ``sample`` sets are SYNTHETIC demos."""
import csv
from importlib import resources
from pathlib import Path


def data_dir() -> Path:
    return Path(str(resources.files("rmti") / "data"))


def sample_path(name: str) -> str:
    p = data_dir() / "sample" / name
    if not p.exists():
        raise FileNotFoundError(f"{name}; available: {sorted(x.name for x in (data_dir() / 'sample').iterdir())}")
    return str(p)


def _read(name):
    with open(data_dir() / name, newline="") as f:
        rows = list(csv.DictReader(f))
    out = {}
    for r in rows:
        n = r.pop("name")
        out[n] = {k: (int(v) if k in ("N", "C") else float(v)) for k, v in r.items() if v != ""}
    return out


def load_urban_cohort():      return _read("urban_cohort_paper.csv")
def load_hcc_published():     return _read("hcc_published_cohorts.csv")
def load_hcc_pearl():         return _read("hcc_pearl_cohorts.csv")
