"""RMTI / Oncoclastics entry point. Main file path in Streamlit Cloud: app.py.py (or streamlit_app.py, both do the same).
All navigation, the disclaimer bar and the API-access button live in rmti_nav.py; the landing page is Home.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rmti_nav  # noqa: E402

rmti_nav.run()
