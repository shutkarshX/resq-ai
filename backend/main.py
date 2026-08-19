"""RESQ-AI FastAPI application entrypoint.

Run with: uvicorn main:app --reload --port 8000
"""
import os
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("resq-ai")

from app.database import init_db, engine
from app.schemas import HealthResponse
from app.routers import dashboard, reports, zones, teams, actions, ai, volunteers, search as search_router

app = FastAPI(
    title="RESQ-AI API",
    description="Disaster response intelligence backend for the RESQ-AI command center.",
    version="1.0.0",
)

allowed_origins = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    logger.info("Starting RESQ-AI API...")
    init_db()
    logger.info("Database initialized at %s", engine.url)


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
def health():
    db_status = "connected"
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
    except Exception as e:  # pragma: no cover - defensive
        logger.error("Database health check failed: %s", e)
        db_status = "disconnected"

    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        service="resq-ai",
        database=db_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(zones.router)
app.include_router(teams.router)
app.include_router(actions.router)
app.include_router(ai.router)
app.include_router(volunteers.router)
app.include_router(search_router.router)


# ---------- Lightweight WebSocket broadcast (optional real-time layer) ----------
#
# The frontend currently polls /api/dashboard every 30s, which works fine
# without this. This /ws endpoint is provided so a future frontend update
# can subscribe to live events instead of polling. Routers can call
# `await ws_manager.broadcast(event_name, payload)` to push updates.

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, event: str, payload: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json({"event": event, "data": payload})
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


ws_manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # We don't require inbound messages; just keep the connection open.
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
