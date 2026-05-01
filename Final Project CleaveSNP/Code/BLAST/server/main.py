"""
CLEAVE SNP — FastAPI server
Run with:  uvicorn main:app --reload --port 8000
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import paths  # sets BLAST_ROOT on sys.path before any route imports BLAST modules
from .routes import analyze, binding, config_route, crispr, database, sequences

app = FastAPI(
    title="CLEAVE SNP API",
    description="FastAPI wrapper around the BLAST + SNP analysis pipeline.",
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Allow the React dev server (localhost:3000) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(config_route.router, prefix="/api")
app.include_router(analyze.router,      prefix="/api")
app.include_router(sequences.router,    prefix="/api")
app.include_router(database.router,     prefix="/api")
app.include_router(crispr.router,       prefix="/api")
app.include_router(binding.router,      prefix="/api")


@app.get("/")
def root():
    return {"status": "ok", "service": "CLEAVE SNP API"}
