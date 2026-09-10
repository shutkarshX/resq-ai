# RESQ-AI

> **Disaster-response intelligence for faster, more informed coordination.**

RESQ-AI is a full-stack disaster-response command-center prototype that combines incident intake, risk prioritization, geospatial awareness, AI-assisted recommendations, rescue-team assignment, and operation tracking in one workflow.

The current build demonstrates a **simulated Bhopal flood-response scenario** using deterministic seeded data. It is a decision-support prototype, not an autonomous emergency-dispatch system.

---

## What it does

| Capability | Purpose |
| --- | --- |
| **Command center** | Surface incidents, people at risk, deployments, resolved cases, and recommended actions |
| **Geospatial intelligence** | Visualize rescue zones, risk scores, and affected populations on an interactive map |
| **Citizen SOS** | Capture emergency type, affected people, medical need, location, risk, priority, and status |
| **AI decision support** | Turn incident/risk information into evacuation, medical, supply, and rescue recommendations |
| **Rescue operations** | Assign available teams and track an operation from queue to completion |
| **Teams & volunteers** | Maintain operational information about rescue teams and volunteer capabilities |

---

## The core workflow

```text
Citizen SOS
    ↓
FastAPI API
    ↓
Risk calculation
    ↓
AI-assisted recommendations
    ↓
Response action
    ↓
Rescue-team assignment
    ↓
Operation tracking
    ↓
Completed response
```

The important part is that the dashboard is backed by a real application flow: reports are persisted, risk is calculated, actions can be assigned, and rescue operations move through their lifecycle.

### Operation lifecycle

```text
QUEUED → DEPLOYED → IN_PROGRESS → COMPLETED
```

---

## Architecture

```text
┌───────────────────────┐
│   React / TypeScript  │
│  Dashboard + Map UI   │
└───────────┬───────────┘
            │ REST API
            ▼
┌───────────────────────┐
│   FastAPI Backend     │
├───────────────────────┤
│ Routers / Services    │
│ Risk Engine           │
│ AI Decision Support   │
│ Assignment Logic      │
└───────────┬───────────┘
            │ SQLAlchemy
            ▼
┌───────────────────────┐
│    SQLite Database    │
│ seeded demo scenario  │
└───────────────────────┘
```

---

## Tech stack

**Frontend**  
`React` · `TypeScript` · `Vite` · `React Leaflet` · `Recharts` · `Lucide React`

**Backend**  
`Python` · `FastAPI` · `SQLAlchemy` · `Pydantic` · `SQLite` · `Uvicorn`

**Development**  
`Git` · `npm` · `Python virtual environment`

---

## Run it on Windows

The repository includes scripts for a quick local demo.

```text
1. Clone the repository
2. Run setup.bat once
3. Run run.bat
4. Open http://localhost:5173
```

`setup.bat` installs dependencies and prepares the deterministic demo data. `run.bat` starts the FastAPI backend and React frontend.

### Manual setup

**Backend**

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python seed.py
uvicorn main:app --reload --port 8000
```

**Frontend** — in a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

The frontend normally runs at `http://localhost:5173` and the backend at `http://127.0.0.1:8000`.

API documentation is available at `http://127.0.0.1:8000/docs` when the backend is running.

---

## Demo scenario

The seeded demonstration models a flood emergency around Bhopal:

| Zone | Risk | People at risk | Example status |
| --- | ---: | ---: | --- |
| Riverside Colony | 96 | 420 | Immediate evacuation |
| Old Market Ward | 81 | 185 | Rescue in progress |
| Shanti Nagar | 68 | 96 | Shelter activated |

**All disaster information, locations, weather values, and citizen reports in the demo are simulated/seeded data.**

---

## API surface

| Area | Endpoints |
| --- | --- |
| Dashboard | `GET /api/dashboard` |
| Citizen SOS | `POST /api/reports` · `GET /api/reports` |
| Assignment | `POST /api/actions/assign` |
| Operations | `GET /api/actions` · `GET /api/actions/{action_id}` · `PATCH /api/actions/{action_id}` |

---

## Project structure

```text
resq-ai/
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   ├── services/
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── database.py
│   │   └── risk_engine.py
│   ├── main.py
│   ├── seed.py
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── api.ts
│   │   └── styles.css
│   ├── package.json
│   └── index.html
├── setup.bat
├── run.bat
└── README.md
```

---

## Demo data & database

The SQLite database is intentionally excluded from Git. It can be recreated with:

```powershell
cd backend
python seed.py
```

The seed process creates deterministic data for rescue zones, teams, volunteers, incidents, citizen SOS reports, and dispatch actions.

---

## Current prototype status

The current build includes:

- React/Vite command-center UI
- FastAPI REST backend
- SQLite persistence
- deterministic demo seeding
- risk calculation
- citizen SOS reporting
- rescue-team assignment
- rescue-operation tracking
- operation status updates
- interactive map
- AI-assisted recommendations

---

## Roadmap

Possible next steps include:

- real-time weather and GIS feeds
- live satellite / geospatial data
- WebSocket or Server-Sent Events updates
- authentication and role-based access
- PostgreSQL deployment
- mobile citizen SOS client
- advanced ML-based risk prediction
- deeper resource-optimization models
- integrations with real emergency-service systems

---

## Scope & safety

RESQ-AI is a **disaster-response decision-support prototype**.

It does **not** replace emergency authorities or professional rescue services, and it does **not independently dispatch real emergency services**. The included scenario is intended for demonstration and development only.

---

## Hackathon prototype

RESQ-AI explores how software can turn fragmented emergency information into a clearer operational workflow — from **incident → risk → recommendation → assignment → response tracking**.

**Built as a practical full-stack prototype, with the emphasis on making the workflow actually work.**
