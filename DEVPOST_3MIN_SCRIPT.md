# 3-minute Devpost script (Memory Leakage Watch)

Open: `http://localhost:8080` (Gemini Live Agent Demo)

## 0:00–0:15 — Setup
- “This is Supply Chain Kanban: an ontology + object-graph API + agent actions.”
- “We added a Live Agent demo option called **Memory Leakage Watch**.”

## 0:15–1:00 — Trigger a deterministic market signal burst
1. Click **Run Memory Leakage Burst**
2. Narrate:
   - “This generates a burst of DRAM/NAND ‘leakage’ news evidence.”
   - “The system creates an alert, opens/updates a case, creates a kanban card, and drafts safe actions.”

## 1:00–2:00 — Review alerts and evidence
1. Click **Refresh Alerts**
   - “Top severity item is the strongest signal.”
2. Click **Refresh News**
   - “These are evidence items that support the alert and case.”

## 2:00–2:40 — Show the API surface
Open: `http://localhost:8000/docs`

Show:
- `GET /news/items?topic=memory`
- `GET /news/alerts?topic=memory`
- `POST /demo/run_scenario` with `memory_leakage_news_burst`

## 2:40–3:00 — Close: Live agent roadmap
- “Today is deterministic for repeatable judging.”
- “Next: replace the websocket scaffold with the real Gemini Live API session (mic streaming + tool calls).”
