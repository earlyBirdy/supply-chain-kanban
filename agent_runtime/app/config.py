import os
DB_URL = os.getenv("AGENT_DB_URL", "postgresql+psycopg2://demo:demo@db:5432/demo")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
RISK_CREATE_THRESHOLD = int(os.getenv("RISK_CREATE_THRESHOLD", "70"))
ALERT_THRESHOLD = int(os.getenv("ALERT_THRESHOLD", "85"))
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "60"))
INGEST_DIR = os.getenv("INGEST_DIR", "/ingest")
