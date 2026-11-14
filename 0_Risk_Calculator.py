"""Risk Calculator page: runs the original calculator, now saved as risk_calculator_app.py (app.py.py is the home page)."""
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
runpy.run_path(str(ROOT / "risk_calculator_app.py"), run_name="__main__")
