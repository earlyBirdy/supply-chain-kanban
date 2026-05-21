# Release Notes

## Supply Chain Kanban AI Agent — Operations Basis

This release resets the repo language from patch-oriented notes to professional release notes.

### Product positioning

Kanban is the regular supply-chain operations basis. It is used for daily planning, purchasing, supplier follow-up, logistics/container tracking, approval routing, governed execution, and audit evidence. Crisis operations is a dashboard/view over the same Kanban case model.

### Removed from professional core

```text
Devpost submission copy
Gemini/model-specific live demo scaffolding
historical v0.6 demo notes
```

### Kept for future use

```text
BI/dashboard definitions
analytics SQL
executive reporting concepts
ERP-adjacent reporting and integration docs
```

BI is kept as an optional analytics and reporting layer, similar to ERP/WMS/TMS integrations. It must not become the operational database or the main workflow.

### Running commands

Browser Kanban UI:

```bash
cp .env.example .env
make demo-web
```

Open:

```text
http://localhost:8080
http://localhost:8000/docs
```

Manager-agent mode:

```bash
cp .env.example .env
make demo-agent
```

News/market-signal mode:

```bash
cp .env.example .env
make demo-web
make demo-signals
```

Streamlit AI-agent debug cockpit:

```bash
pip install -r requirements-debug.txt
make debug-ui
```

Open:

```text
http://localhost:8501
```

Quality gate:

```bash
make test
```

### Architecture summary

```text
ERP / WMS / TMS / SiteTrack / market signals
  -> canonical events
  -> Kanban operating case
  -> AI recommendation
  -> approval gate
  -> governed execution
  -> receipt + audit / blockchain evidence
  -> Kanban command board / BI reporting view
```
