"""Risk Calculator page: runs the original main app (app.py.py) unchanged, then applies the shared look."""
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
try:
    runpy.run_path(str(ROOT / "app.py.py"), run_name="__main__")
finally:
    import oncoclastic_style as ui
    ui.apply()
