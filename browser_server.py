"""RAGEWARE — Local HTTP server for browser extension communication."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
import config

app = FastAPI(title="RAGEWARE Browser Server")

# Allow CORS from Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)


class DomainPing(BaseModel):
    domain: str
    timestamp: float | None = None


# Reference to activity monitor — set by main.py at startup
_activity_monitor = None


def set_activity_monitor(monitor):
    """Called by main.py to wire the activity monitor."""
    global _activity_monitor
    _activity_monitor = monitor


@app.post("/activity")
async def receive_activity(ping: DomainPing):
    """Receive domain ping from Chrome extension."""
    domain = ping.domain.strip().lower() if ping.domain else ""
    ts = ping.timestamp or time.time()
    
    if _activity_monitor and domain:
        _activity_monitor.update_domain(domain)
    
    return {"status": "ok", "domain": domain, "timestamp": ts}


@app.get("/status")
async def status():
    """Health check endpoint."""
    return {"status": "running", "port": config.SERVER_PORT}


def run_server():
    """Run the FastAPI server. Call this in a background thread."""
    import uvicorn
    uvicorn.run(app, host=config.SERVER_HOST, port=config.SERVER_PORT, 
                log_level="warning")
