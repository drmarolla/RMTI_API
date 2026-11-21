"""Command line: ``rmti selfcheck`` reproduces the published tables."""
import argparse
import sys

from . import __version__
from .domains import hcc, urban


def _report(title, rows, ok):
    print(f"\n{title}")
    for r in rows:
        name, field, exp, got, good = r
        print(f"  {name:<32} {field:<8} paper={exp:<6} code={got:<6} {'OK' if good else 'MISMATCH'}")
    print(f"  -> {'all match' if ok else 'MISMATCHES FOUND'}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="rmti", description="Risk Mechanism Theory Index")
    ap.add_argument("command", choices=["selfcheck", "version"])
    cmd = ap.parse_args(argv).command
    if cmd == "version":
        print(__version__)
        return 0
    rows, ok1 = urban.selfcheck()
    _report("Urban (IJMADA 2026, Tables 4-5)", rows, ok1)
    rows, ok2 = hcc.selfcheck()
    _report("HCC (preprint, Tables 1-2)", rows, ok2)
    return 0 if ok1 and ok2 else 1


if __name__ == "__main__":
    sys.exit(main())
