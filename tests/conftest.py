import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
agent_runtime = repo_root / "agent_runtime"
if str(agent_runtime) not in sys.path:
    sys.path.insert(0, str(agent_runtime))
