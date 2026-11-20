"""Write docs/openapi.json from the FastAPI app (needs the API dependencies). Run from the repository root: python tools/export_openapi.py"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import api  # noqa: E402

out = ROOT / "docs" / "openapi.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(api.app.openapi(), indent=2), encoding="utf-8")
print("wrote", out)
