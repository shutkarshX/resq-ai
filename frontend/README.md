# RESQ-AI

AI-powered disaster response intelligence platform prototype for the AI-01 problem statement.

## Run the interactive frontend

```bash
cd resq-ai
npm install
npm run dev
```

## Run the API

```bash
cd resq-ai
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn pydantic
uvicorn backend.main:app --reload --port 8000
```

The UI is intentionally usable in demo mode without the API. The FastAPI service provides the integration seam for live feeds, AI orchestration, GIS layers, reports and dispatch actions.

## Connect the frontend to your backend

Copy `.env.example` to `.env` and set `VITE_API_URL` to the URL where your FastAPI service is running.

```bash
cp .env.example .env
```

The frontend automatically:

- Loads `/api/dashboard` on startup and every 30 seconds
- Uses live metrics, zones and AI summary returned by the backend
- Sends rescue assignments to `/api/actions/assign`
- Falls back to polished demo data if the API is unavailable

For a production deployment, replace the demo API methods in `src/api.ts` with your authenticated API client and add WebSocket or Server-Sent Events for live incident updates.
