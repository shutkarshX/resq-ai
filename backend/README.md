# RESQ-AI Backend

A production-quality FastAPI backend that makes the existing RESQ-AI React
frontend fully functional — real risk scoring, real dispatch state, real
dashboard metrics, all backed by SQLite (swap-ready for Postgres).

**No frontend files were changed.** This backend was designed around the
existing `main.tsx` / `api.ts` contract.

---

## 1. Install Python dependencies

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configure environment

```bash
cp .env.example .env
```

You don't need to set `OPENAI_API_KEY` — the system runs entirely on a
deterministic fallback AI engine (see "AI fallback" below). `DATABASE_URL`
defaults to a local SQLite file; `ALLOWED_ORIGINS` should match wherever
your Vite dev server runs (default `http://localhost:5173`).

## 3. Initialize the database

Tables are created automatically on first run (`init_db()` runs on FastAPI
startup), but you can also do it explicitly:

```bash
python -c "from app.database import init_db; init_db()"
```

## 4. Seed demo data

```bash
python seed.py
```

This clears and repopulates the database with the frontend's existing
zones (Riverside Colony, Old Market Ward, Shanti Nagar), 6 rescue teams,
5 incidents, 10 SOS reports, 5 volunteers, and several dispatch actions —
all deterministic (no random values), so every demo run looks the same
until you interact with it.

## 5. Start the backend

```bash
uvicorn main:app --reload --port 8000
```

## 6. Open Swagger

Visit **http://127.0.0.1:8000/docs** for interactive API testing, or
**http://127.0.0.1:8000/redoc** for reference docs.

## 7. Start the existing frontend

In a separate terminal, from the frontend project root:

```bash
cp .env.example .env   # if not already done; set VITE_API_URL=http://127.0.0.1:8000
npm install
npm run dev
```

Open the Vite dev server URL (typically `http://localhost:5173`). The
Command Center will now show live backend data instead of demo-mode
fallback data (watch the "Backend connected" pill in the top-right of the
heading — it should say **online**, not **demo**).

---

## How the frontend connects to the backend

`src/api.ts` reads `VITE_API_URL` and calls:

- `GET  {VITE_API_URL}/api/dashboard` — on load and every 30 seconds
- `POST {VITE_API_URL}/api/actions/assign` — when an "Assign" button or
  "Generate full response plan" button is clicked, or the SOS modal is
  confirmed

Both are implemented with the **exact same response shape** the frontend
already expects, so zero frontend code changes are required. If the
backend is unreachable, `api.ts`'s existing try/catch falls back to demo
data automatically — that fallback behavior is untouched.

---

## Frontend changes required

**None.** `index.html`, `main.tsx`, `api.ts`, and `styles.css` are used
exactly as provided. If you later want the frontend to use the additional
endpoints below (reports list, teams list, volunteers, search, AI panel
wired to real data, etc.), you would extend `api.ts` with more functions
following the same pattern already used for `dashboard()` and `assign()`
— but that's optional and out of scope for "make the existing UI work."

---

## Complete API endpoint list

### Health
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Service + DB connectivity check |

### Dashboard (used by existing frontend)
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/dashboard` | Live metrics, zones, AI summary — matches `DashboardPayload` |

### Reports / SOS
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/reports` | Submit a citizen SOS report → risk scored → incident created |
| GET | `/api/reports` | List reports, filter by `priority`, `status`, `zone_id`, `emergency`, `limit` |

### Zones
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/zones` | List all rescue zones |
| GET | `/api/zones/{zone_id}` | Zone detail incl. active incidents/teams/reports counts |
| GET | `/api/map/zones` | Leaflet-friendly zone/marker payload |

### Teams
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/teams` | List all rescue teams |
| GET | `/api/teams/available` | List only `AVAILABLE` teams |
| GET | `/api/teams/{team_id}` | Single team detail |
| POST | `/api/teams` | Register a new team |

### Actions / Dispatch (used by existing frontend)
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/actions/assign` | Assign/deploy a team to a zone — matches existing `resqApi.assign()` call |
| GET | `/api/actions` | List all dispatch actions |
| GET | `/api/actions/{action_id}` | Single action detail |
| PATCH | `/api/actions/{action_id}` | Update status (`QUEUED`→`DEPLOYED`→`IN_PROGRESS`→`COMPLETED`/`CANCELLED`) |

### AI decision support
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/ai/analyze` | Situation summary + recommendations for an incident |
| POST | `/api/ai/response-plan` | Full response plan for a zone (powers "Generate full response plan") |

### Volunteers
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/volunteers` | List volunteers |
| POST | `/api/volunteers` | Register a volunteer |
| PATCH | `/api/volunteers/{id}` | Update status/availability |

### Search
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/search?q=...` | Search zones, incidents, reports, teams |

### Real-time (optional)
| Protocol | Path | Purpose |
|---|---|---|
| WS | `/ws` | Broadcast channel for future live-update UI (dashboard currently polls instead) |

---

## The complete SOS → Risk → AI → Dispatch flow

This is the core loop the whole system is built around:

1. **Citizen submits SOS** — `POST /api/reports` with emergency type,
   people affected, medical flag, location, and severity inputs.
2. **Deterministic risk scoring** — `app/risk_engine.py` computes a 0–100
   score from fixed point allocations (people ≤30, flood ≤25, medical
   flat 20, infrastructure ≤15, weather ≤10) and maps it to
   LOW/MEDIUM/HIGH/CRITICAL. This is pure arithmetic — the AI never
   touches this number.
3. **Incident + report persisted** — a new `Incident` row is created
   (or the nearest zone's data is updated), the `SOSReport` row is
   stored and linked to both the incident and the nearest `RescueZone`
   (found via haversine distance, or the highest-risk zone if no
   coordinates are given).
4. **Zone refresh** — the zone's `risk_score`, `people_at_risk`, `color`,
   and `status` are recalculated from its active incidents, so the map
   and dashboard immediately reflect the new situation.
5. **Dashboard updates** — `GET /api/dashboard` recomputes
   `active_incidents`, `people_at_risk`, `teams_deployed`, and
   `cases_resolved` directly from the database every time it's called —
   nothing is cached or hardcoded.
6. **AI decision support** — `POST /api/ai/analyze` (or
   `/api/ai/response-plan` for a full zone-level plan) takes the
   deterministic risk_score/priority and generates a situation summary,
   recommendations, potential risks, and required resources using the
   fallback engine in `app/ai_engine.py`. Every response carries an
   `advisory_notice` making clear this is decision support only — no
   real dispatch, evacuation, or emergency contact has occurred.
7. **Human clicks Assign** — `POST /api/actions/assign` looks up the
   zone, finds (or validates) a rescue team, and — only if that team is
   currently `AVAILABLE` — creates a `DispatchAction` and flips the team
   to `DEPLOYED`, associating it with the zone. If no team is available,
   the action is stored as `QUEUED` instead of silently failing.
8. **Team state changes persist** — this isn't cosmetic: the team really
   is unavailable for other assignments until the action completes.
9. **Completing the action** — `PATCH /api/actions/{id}` with
   `status: "COMPLETED"` frees the team back to `AVAILABLE`, resolves
   the zone's most recent active incident, and resets the zone status —
   after which dashboard metrics (`cases_resolved`, `active_incidents`)
   immediately reflect the change on the next `GET /api/dashboard` call.

---

## How the AI fallback works

`app/ai_engine.py` contains a fully deterministic recommendation engine
that requires **no external API key**. It is the primary engine, not a
degraded backup:

- **Situation summary**: templated from emergency type, people count,
  medical flag, weather, and area.
- **Recommendations**: rule-based, keyed off priority level (dispatch
  urgency), emergency keywords (flood → boats, fire → suppression units,
  earthquake → structural teams), medical flag, and population size.
- **Potential risks** and **required resources**: same rule-based
  approach, deduplicated and capped to a readable list.
- **Confidence**: a deterministic function of priority level plus bonus
  for having weather/area context (never random).

If `OPENAI_API_KEY` is set in `.env`, that's simply available for a future
enhancement (e.g. richer natural-language phrasing) — the current
implementation does not require it and works identically either way,
which is exactly what's needed for a reliable hackathon demo.

Every AI response includes an `advisory_notice` field and is designed to
only use imperative/recommending language ("Deploy...", "Consider...",
"Prioritize...") — never past-tense claims like "has been dispatched" or
"has contacted emergency services." Actual dispatch only ever happens
through the deterministic `/api/actions/assign` endpoint, gated by a real
human clicking Assign.

---

## Hackathon demo flow

1. Start backend (`uvicorn main:app --reload --port 8000`) and seed data
   (`python seed.py`).
2. Start frontend (`npm run dev`), confirm the header shows **"Backend
   connected"**.
3. Click **Trigger Citizen SOS** → confirm the broadcast. This calls
   `assign()` under the hood in the current frontend wiring, which hits
   `/api/actions/assign` and shows the toast.
4. Open Swagger (`/docs`) alongside the UI and call `POST /api/reports`
   with a flood emergency (`people: 400+`, `medical_emergency: true`) to
   show a CRITICAL risk score being computed live.
5. Call `GET /api/dashboard` (or just wait ~30s / click **Refresh** in
   the UI) — watch `active_incidents` and `people_at_risk` increase.
6. Call `POST /api/ai/analyze` with the returned `incident_id` — show the
   recommendations and the advisory notice.
7. Back in the UI, click **Assign** on a recommended action — this calls
   `/api/actions/assign`, which deploys a real team.
8. In Swagger, `GET /api/teams` — show the team's status is now
   `DEPLOYED`.
9. `PATCH /api/actions/{action_id}` with `status: "COMPLETED"` — show the
   team flip back to `AVAILABLE` and `cases_resolved` increment on the
   next dashboard fetch.

---

## Testing

```bash
pytest
```

Tests cover: health, dashboard math (including live updates after SOS),
risk engine boundaries and point allocation, report filtering, zone/team
listing and 404s, the full assign → deploy → complete → free-team dispatch
lifecycle, team-unavailable 409 handling, AI fallback (explicitly with
`OPENAI_API_KEY` unset), AI safety-language checks, response-plan
generation, volunteers CRUD, and search.

Each test run uses an isolated `test_resq_ai.db` SQLite file (see
`tests/conftest.py`), so it never touches your real demo database.

---

## Error handling conventions

- `404` — zone/team/report/action/volunteer/incident not found
- `400` / `422` — invalid input (Pydantic validation)
- `409` — attempting to assign a team that isn't `AVAILABLE`
- `500` — reserved for genuinely unexpected server errors (not used to
  paper over bad input)

## Project structure

```
backend/
├── main.py                  # FastAPI app, CORS, health, WebSocket
├── requirements.txt
├── .env.example
├── .gitignore
├── pytest.ini
├── seed.py                  # Deterministic demo data
├── app/
│   ├── database.py          # Engine/session, works with SQLite or Postgres
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic request/response models
│   ├── risk_engine.py       # Deterministic 0-100 risk scoring
│   ├── ai_engine.py         # Advisory-only AI decision support (no API key needed)
│   ├── services.py          # Shared logic: metrics, geo lookup, team pick, zone refresh
│   └── routers/
│       ├── dashboard.py
│       ├── reports.py
│       ├── zones.py
│       ├── teams.py
│       ├── actions.py
│       ├── ai.py
│       ├── volunteers.py
│       └── search.py
└── tests/
    ├── conftest.py
    ├── test_health_dashboard.py
    ├── test_risk_engine.py
    ├── test_reports_zones_teams.py
    ├── test_actions.py
    ├── test_ai.py
    └── test_volunteers_search.py
```
