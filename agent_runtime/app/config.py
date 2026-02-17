import os
DB_URL = os.getenv("AGENT_DB_URL", "postgresql+psycopg2://demo:demo@db:5432/demo")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
RISK_CREATE_THRESHOLD = int(os.getenv("RISK_CREATE_THRESHOLD", "70"))
ALERT_THRESHOLD = int(os.getenv("ALERT_THRESHOLD", "85"))
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "60"))
INGEST_DIR = os.getenv("INGEST_DIR", "/ingest")

# Kinetic execution (demo defaults)
ERP_CONNECTOR = os.getenv("ERP_CONNECTOR", "mock")  # mock | sap | oracle | ...
ERP_BASE_URL = os.getenv("ERP_BASE_URL", "")
ERP_API_KEY = os.getenv("ERP_API_KEY", "")

# API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))


def _truthy(v: str) -> bool:
    return str(v).strip().lower() in ("1","true","yes","y","on")

DEV_MODE = _truthy(os.getenv("DEV_MODE", "1"))
