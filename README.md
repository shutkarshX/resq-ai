# RESQ-AI

## Windows Quick Start

After cloning the repository:

1. Open a terminal in the project folder.
2. Run `setup.bat` once to install dependencies and create demo data.
3. Run `run.bat` whenever you want to start RESQ-AI.
4. Open http://localhost:5173 in your browser.

`run.bat` starts both the FastAPI backend and React frontend automatically.

Disaster Response Intelligence Platform

RESQ-AI is an AI-assisted disaster response command-center prototype that helps emergency teams understand incidents, prioritize high-risk zones, coordinate rescue teams, and track response operations from one dashboard.

The current prototype uses a simulated Bhopal flood-response scenario with deterministic demo data.

==================================================
KEY FEATURES
==================================================

1. Command Center
   - Live incident metrics
   - People-at-risk metrics
   - Rescue team deployment metrics
   - Cases resolved
   - AI-assisted operational summary
   - Recommended next actions

2. Geospatial Intelligence
   - Interactive Leaflet map
   - Rescue zones with risk scores
   - Population-at-risk information
   - Priority visualization

3. Citizen SOS Reports
   - Backend-backed SOS reports
   - Emergency type
   - People affected
   - Medical emergency indicator
   - Location and zone
   - Risk score and priority
   - Report status and source

4. AI Decision Support
   - Risk-based prioritization
   - Evacuation recommendations
   - Medical extraction recommendations
   - Supply movement recommendations
   - Rescue-team assignment recommendations
   - Deterministic fallback AI engine

5. Rescue Operations
   - Real backend-backed operations
   - Rescue team assignment
   - Operation tracking
   - Status updates

   Operation lifecycle:

   QUEUED
      |
      v
   DEPLOYED
      |
      v
   IN_PROGRESS
      |
      v
   COMPLETED

6. Rescue Teams and Volunteers
   - Rescue teams
   - Team types
   - Team members
   - Volunteers
   - Volunteer skills
   - Volunteer locations


==================================================
SYSTEM ARCHITECTURE
==================================================

Citizen SOS
     |
     v
FastAPI Backend
     |
     v
Risk Engine
     |
     v
AI Decision Support
     |
     v
Response Action
     |
     v
Rescue Team Assignment
     |
     v
Rescue Operation
     |
     v
Status Tracking
     |
     v
SQLite Database


==================================================
TECHNOLOGY STACK
==================================================

Frontend:
- React
- TypeScript
- Vite
- React Leaflet
- Recharts
- Lucide React

Backend:
- Python
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite
- Uvicorn

Development:
- Git
- npm
- Python virtual environment


==================================================
PROJECT STRUCTURE
==================================================

resq-ai/
|
+-- backend/
|   +-- app/
|   |   +-- routers/
|   |   +-- services/
|   |   +-- models.py
|   |   +-- schemas.py
|   |   +-- database.py
|   |   +-- risk_engine.py
|   |
|   +-- main.py
|   +-- seed.py
|   +-- requirements.txt
|   +-- tests/
|
+-- frontend/
|   +-- src/
|   |   +-- main.tsx
|   |   +-- api.ts
|   |   +-- styles.css
|   |
|   +-- package.json
|   +-- index.html
|
+-- .gitignore
+-- README.md


==================================================
BACKEND SETUP
==================================================

From the project root:

cd backend

Create a virtual environment:

python -m venv .venv

Activate it on Windows:

.venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Create the environment file:

copy .env.example .env

Create the deterministic demo database:

python seed.py

Start the backend:

uvicorn main:app --reload --port 8000


Backend:
http://127.0.0.1:8000

Swagger API documentation:
http://127.0.0.1:8000/docs


==================================================
FRONTEND SETUP
==================================================

Open a second terminal.

From the project root:

cd frontend

Install dependencies:

npm install

Create the environment file:

copy .env.example .env

Set:

VITE_API_URL=http://127.0.0.1:8000

Start the frontend:

npm run dev

Open the Vite URL shown in the terminal.

Usually:

http://localhost:5173


==================================================
MAIN API ENDPOINTS
==================================================

Dashboard:

GET /api/dashboard

Citizen SOS:

POST /api/reports
GET /api/reports

Rescue Assignment:

POST /api/actions/assign

Rescue Operations:

GET /api/actions
GET /api/actions/{action_id}
PATCH /api/actions/{action_id}


==================================================
END-TO-END DEMONSTRATION
==================================================

1. Citizen emergency is reported.

2. SOS report is sent to the backend.

3. Backend calculates the risk score.

4. Report receives a priority classification.

5. RESQ-AI generates recommended response actions.

6. Operator assigns a rescue action.

7. Backend selects an available rescue team.

8. A rescue operation is created.

9. Operator deploys the operation.

10. Operator starts the operation.

11. Operator completes the operation.

This demonstrates a functional disaster-response decision-support workflow rather than only a static dashboard.


==================================================
DEMO SCENARIO
==================================================

The included demonstration represents a flood emergency around Bhopal.

Riverside Colony
Risk: 96
People at risk: 420
Status: Immediate evacuation

Old Market Ward
Risk: 81
People at risk: 185
Status: Rescue in progress

Shanti Nagar
Risk: 68
People at risk: 96
Status: Shelter activated

The disaster information, locations, weather values and citizen reports are simulated/seeded demonstration data.


==================================================
DATABASE
==================================================

The SQLite database is intentionally excluded from Git.

The database can be recreated at any time using:

cd backend
python seed.py

The seed script creates deterministic demo data for:

- Rescue zones
- Rescue teams
- Volunteers
- Incidents
- Citizen SOS reports
- Dispatch actions


==================================================
CURRENT PROTOTYPE STATUS
==================================================

Working:

- React/Vite dashboard
- FastAPI backend
- SQLite persistence
- Deterministic demo database
- Risk calculation
- Citizen SOS reports
- Rescue-team assignment
- Rescue operations
- Operation status updates
- Interactive map
- AI-assisted recommendations
- REST API integration


==================================================
FUTURE EXTENSIONS
==================================================

- Real-time weather feeds
- Live GIS and satellite data
- WebSocket or Server-Sent Events
- Real emergency-service integrations
- Advanced ML risk prediction
- Authentication and role-based access
- PostgreSQL deployment
- Mobile citizen SOS application
- Advanced AI resource optimization


==================================================
SCOPE
==================================================

RESQ-AI is a disaster-response decision-support prototype.

It does not replace emergency authorities or professional rescue services.

It does not independently dispatch real emergency services.

All included disaster information is intended for demonstration and development.


==================================================
HACKATHON
==================================================

RESQ-AI
Disaster Intelligence

A hackathon prototype focused on improving disaster-response coordination through data, AI-assisted decision support, risk prioritization, rescue-team coordination and operational tracking.