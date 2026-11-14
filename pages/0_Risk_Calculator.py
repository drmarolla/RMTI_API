"""Risk Calculator page: runs the original main app (app.py.py) unchanged, now that Home.py is the entry page."""
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
runpy.run_path(str(ROOT / "app.py.py"), run_name="__main__")
