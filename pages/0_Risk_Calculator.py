"""Risk Calculator page: runs the original calculator (calculator_app.py) unchanged; the router adds the look, notices and evidence panel."""
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
runpy.run_path(str(ROOT / "calculator_app.py"), run_name="__main__")
