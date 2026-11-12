# RESQ-AI — Disaster Response Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Async%20REST-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18%20%7C%20TypeScript-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5-646CFF.svg)](https://vitejs.dev/)
[![Leaflet](https://img.shields.io/badge/Maps-Leaflet%20Geospatial-199900.svg)](https://leafletjs.com/)
[![AI](https://img.shields.io/badge/AI%20Engine-Google%20Gemini-4285F4.svg)](https://ai.google.dev/)
[![SQLite](https://img.shields.io/badge/Storage-SQLite%20Async-003B57.svg)](https://www.sqlite.org/)

An AI-assisted disaster response intelligence and emergency rescue coordination command center. RESQ-AI integrates multi-channel citizen SOS intake, automated risk triage, geospatial hazard mapping, AI-generated evacuation recommendations (via Google Gemini), and dynamic rescue team dispatch into a cohesive operational dashboard.

---

## 🏛️ System Architecture

```mermaid
graph TD
    Citizen([Citizen SOS Reporter]) -->|"1. Submit SOS / Distress Data"| Frontend["React + TypeScript Command Dashboard"]
    
    subgraph APILayer["FastAPI Backend Engine (Async REST)"]
        Router["API Gateway (/api/v1)"]
        TriageEngine["Multi-Factor Risk Scoring Engine<br/>(Severity, Vulnerability, Urgency)"]
        AIEngine["Gemini AI Recommendation Engine<br/>(Evacuation, Medical & Resource Directives)"]
        DispatchService["Rescue Dispatch & Team Tracker"]
    end

    subgraph DataStore["State Persistence Layer"]
        DB[("SQLite Database<br/>(Incidents, Teams, Routes)")]
        GeoData[("GeoJSON Zone Layers<br/>(Flood & Hazard Heatmaps)")]
    end

    Frontend -->|"JSON REST Requests"| Router
    Router --> TriageEngine
    TriageEngine -->|"Priority Weighted Incidents"| AIEngine
    AIEngine -->|"Actionable Tactics"| DispatchService
    DispatchService -->|"Audit Trail & Status Updates"| DB
    DB -->|"Live Telemetry & GeoJSON"| Frontend
```

---

## 🚨 Incident Triage & Operational Lifecycle

```mermaid
stateDiagram-v2
    [*] --> SOS_Submitted: Citizen Reports Distress
    SOS_Submitted --> Triage_Scoring: Extract Severity, Medical Need & Location
    Triage_Scoring --> High_Priority: Risk Score >= 75
    Triage_Scoring --> Medium_Priority: Risk Score 40-74
    Triage_Scoring --> Standard_Queue: Risk Score < 40

    High_Priority --> AI_Action_Generation: Gemini Generates Tactical Directives
    AI_Action_Generation --> Team_Assigned: Dispatch Nearest Available Team
    Team_Assigned --> En_Route: Telemetry Tracking
    En_Route --> On_Scene: Medical Triage / Evacuation
    On_Scene --> Resolved: Citizens Rescued & Logged
    Resolved --> [*]
```

---

## ✨ Core Capabilities

| Module | Technical Implementation | Operational Role |
| :--- | :--- | :--- |
| **Command Center HUD** | React 18, Tailwind CSS, Lucide Icons | Real-time overview of active SOS signals, casualties prevented, available teams, and bottleneck alerts. |
| **Geospatial Intelligence** | Leaflet, OpenStreetMap, GeoJSON | Interactive zone-level inundation maps, high-risk sector overlays, and safe evacuation corridors. |
| **Citizen SOS Intake** | Async FastAPI Form Validator | Mobile-friendly emergency reporting capturing distress category, medical vulnerabilities, and GPS coordinates. |
| **AI Decision Support** | Google Gemini API integration | Converts unstructured incident telemetry into prioritized supply, medical triage, and helicopter dispatch recommendations. |
| **Resource Management** | SQLite, SQLAlchemy ORM | Live operational status tracking for NDRF teams, volunteer squads, inflatable boats, and medical shelters. |

---

## 🚀 Quickstart: Local Setup

### Prerequisites
* **Python**: 3.10+
* **Node.js**: 18+ and `npm`

### 1. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1 | Linux/macOS: source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Populate demo scenario (Bhopal urban flood simulation)
python seed.py

# Launch FastAPI server
python main.py
```
*Backend API will listen at `http://127.0.0.1:8000` with interactive Swagger docs at `/docs`.*

### 2. Frontend Setup

In a separate terminal:

```bash
cd frontend

# Install packages
npm install

# Start Vite development server
npm run dev
```
*Open `http://localhost:5173` in your browser to access the RESQ-AI Command Center.*

---

## 📂 Repository Structure

```text
resq-ai/
├── backend/
│   ├── app/
│   │   ├── routers/           # Incident, team, SOS, and AI recommendation endpoints
│   │   ├── models/            # SQLAlchemy database schemas
│   │   ├── schemas/           # Pydantic request & response validators
│   │   └── services/          # Gemini AI integration & triage scoring
│   ├── main.py                # FastAPI application entrypoint
│   ├── seed.py                # Seed script for realistic demo incident records
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/        # MapView, SOSModal, StatsCards, TeamManager
│   │   ├── services/          # Axios API communication layer
│   │   └── App.tsx            # Central dashboard composition
│   ├── vite.config.ts
│   └── package.json
└── README.md
```

---

## 📜 Ethical & Simulation Notice
* Developed as an academic and hackathon demonstration for AI-assisted emergency response.
* All incident data, citizen identities, and coordinates are deterministic synthetic simulations.
