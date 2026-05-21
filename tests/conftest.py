import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
api_runtime = repo_root / "apps" / "api"
if str(api_runtime) not in sys.path:
    sys.path.insert(0, str(api_runtime))
