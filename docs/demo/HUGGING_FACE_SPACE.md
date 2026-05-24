# Run the Supply Chain AI Agent demo on Hugging Face Spaces

Use a **Docker Space** so the demo can run the API, seeded Postgres database, and static UI in one container.

## Files used

- `Dockerfile.hf` — single-container Space image.
- `scripts/hf_start.sh` — starts Postgres, seeds demo data, then starts FastAPI on port `7860`.
- `apps/web/public/*` — served by the API container when `SUPPLY_CHAIN_SERVE_WEB=1`.

## Space setup

1. Create a new Hugging Face Space.
2. Choose **SDK: Docker**.
3. Push this repo.
4. Rename or copy `Dockerfile.hf` to `Dockerfile` in the Space repo, or configure the Space to build from `Dockerfile.hf`.
5. Open the Space URL.

The UI should load at `/` and call the API through `/api/*`, so no separate Nginx or Docker Compose stack is needed.

## Demo behavior

The Space starts with seeded supply-chain data and keeps the main page focused on the top major issues. Optional live-news monitoring can still be demonstrated from the **Templates + news** subpage.

## Local smoke test

```bash
docker build -f Dockerfile.hf -t supply-chain-ai-agent-hf .
docker run --rm -p 7860:7860 supply-chain-ai-agent-hf
```

Then open `http://localhost:7860`.
