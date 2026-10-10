"""
Online Learning Portal – FastAPI Application
Serves the REST API and the Frontend Single Page Application.
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Add root directory to python path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.db_config import get_mongo_client, get_neo4j_driver, close_connections
from app.routers import (
    health,
    dashboard,
    students,
    courses,
    materials,
    quizzes,
    analytics,
    graph
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager: verify connections on startup, close on shutdown."""
    print("[Portal App] Starting Online Learning Portal API...")
    try:
        get_mongo_client()
        get_neo4j_driver()
        print("[Portal App] MongoDB and Neo4j connections verified.")
    except Exception as e:
        print(f"[Portal App] Warning during startup connection check: {e}")
    yield
    print("[Portal App] Shutting down application...")
    close_connections()

app = FastAPI(
    title="Online Learning Portal – Hybrid NoSQL System",
    description="Full-stack hybrid database portal integrating MongoDB (Document Store) and Neo4j (Graph Database)",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for local client flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health.router)
app.include_router(dashboard.router)
app.include_router(students.router)
app.include_router(courses.router)
app.include_router(materials.router)
app.include_router(quizzes.router)
app.include_router(analytics.router)
app.include_router(graph.router)

# Mount Static Files
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

@app.get("/", include_in_schema=False)
async def serve_index():
    """Serve the frontend single-page application."""
    index_file = TEMPLATES_DIR / "index.html"
    if not index_file.exists():
        return JSONResponse(
            status_code=404,
            content={"error": "Frontend template index.html not found"}
        )
    return FileResponse(str(index_file))

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Ensure unhandled errors return clean JSON envelopes without crashing."""
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "error": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
