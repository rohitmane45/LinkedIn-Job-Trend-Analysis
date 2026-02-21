"""
Job Analysis API Server — FastAPI
==================================
REST API for accessing job data, analysis, and salary predictions.

Usage:
    uvicorn api_server:app --host 127.0.0.1 --port 8000
    # or:  python api_server.py

Auto-generated docs:
    GET /docs    — Swagger UI
    GET /redoc   — ReDoc

Endpoints:
    GET  /api/jobs              — List jobs (params: limit, offset)
    GET  /api/jobs/search       — Search jobs (params: q, limit)
    GET  /api/stats             — Job market statistics
    GET  /api/skills            — Skill rankings
    GET  /api/companies         — Top companies
    GET  /api/locations         — Top locations
    GET  /api/alerts            — Alert matches
    GET  /api/trends            — Trend data
    POST /api/salary/predict    — ML salary prediction
"""

import sys
import os
import time
import json
import logging
from collections import defaultdict, deque
from pathlib import Path
from datetime import datetime
from typing import Optional

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from fastapi import FastAPI, Query, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ──────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
REPORTS_DIR = PROJECT_ROOT / 'outputs' / 'reports'
DATA_DIR = PROJECT_ROOT / 'data' / 'raw'
LOGS_DIR = PROJECT_ROOT / 'logs'

LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [api] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOGS_DIR / 'api_server.log', encoding='utf-8'),
    ]
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# FastAPI App
# ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="LinkedIn Job Analysis API",
    description="REST API for job market data, analysis insights, and ML salary predictions.",
    version="2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────────
# Rate Limiting
# ──────────────────────────────────────────────────────────────
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX = 120
_request_log: dict = defaultdict(deque)


async def rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    times = _request_log[client_ip]
    cutoff = now - RATE_LIMIT_WINDOW
    while times and times[0] < cutoff:
        times.popleft()
    if len(times) >= RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Retry later.")
    times.append(now)


# ──────────────────────────────────────────────────────────────
# API Key (optional)
# ──────────────────────────────────────────────────────────────
async def check_api_key(request: Request):
    expected = os.getenv("API_KEY", "").strip()
    if not expected:
        return
    provided = request.headers.get("X-API-Key", "").strip()
    if provided != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


# ──────────────────────────────────────────────────────────────
# Pydantic Models
# ──────────────────────────────────────────────────────────────
class SalaryRequest(BaseModel):
    title: str = Field(..., description="Job title, e.g. 'Data Scientist'")
    location: Optional[str] = Field(None, description="City/location, e.g. 'Bangalore'")
    skills: Optional[str] = Field(None, description="Comma-separated skills")
    company_size: Optional[str] = Field(None, description="Enterprise/Large/Medium/Small/Startup")


class SalaryResponse(BaseModel):
    min: float
    max: float
    avg: float
    currency: str = "INR"
    unit: str = "LPA"
    confidence: str
    method: str


# ──────────────────────────────────────────────────────────────
# Data loaders
# ──────────────────────────────────────────────────────────────
def load_latest_analysis() -> dict:
    """Load the most recent analysis JSON file."""
    files = list(REPORTS_DIR.glob('analysis_*.json'))
    if not files:
        return {}
    latest = max(files, key=lambda f: f.stat().st_mtime)
    with open(latest, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_jobs_data() -> list:
    """Load jobs from database, CSV, or JSON."""
    db_file = PROJECT_ROOT / 'data' / 'jobs.db'
    if db_file.exists():
        try:
            from database import JobDatabase
            with JobDatabase() as db:
                return db.get_recent_jobs(days=30, limit=500)
        except Exception as exc:
            logger.exception('Database read failed: %s', exc)

    try:
        import pandas as pd
        csv_files = list(DATA_DIR.glob('jobs_*.csv'))
        if csv_files:
            latest = max(csv_files, key=lambda f: f.stat().st_mtime)
            df = pd.read_csv(latest)
            return df.to_dict('records')
    except Exception as exc:
        logger.exception('CSV read failed: %s', exc)

    json_files = list(DATA_DIR.glob('jobs_*.json'))
    if json_files:
        latest = max(json_files, key=lambda f: f.stat().st_mtime)
        with open(latest, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else data.get('jobs', [])

    return []


# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────
@app.get("/", tags=["Meta"])
@app.get("/api", tags=["Meta"])
async def root():
    """API documentation overview."""
    return {
        "name": "LinkedIn Job Analysis API",
        "version": "2.0",
        "docs": "/docs",
        "endpoints": {
            "/api/jobs": "List jobs (params: limit, offset)",
            "/api/jobs/search": "Search jobs (params: q, limit)",
            "/api/stats": "Get statistics",
            "/api/skills": "Get skill rankings",
            "/api/companies": "Get top companies",
            "/api/locations": "Get top locations",
            "/api/alerts": "Get alert matches",
            "/api/trends": "Get trend data",
            "/api/salary/predict": "POST — ML salary prediction",
        },
    }


@app.get("/api/jobs", tags=["Jobs"], dependencies=[Depends(rate_limit), Depends(check_api_key)])
async def get_jobs(
    limit: int = Query(50, ge=1, le=200, description="Max jobs to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """List jobs with pagination."""
    jobs = load_jobs_data()
    total = len(jobs)
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "jobs": jobs[offset:offset + limit],
    }


@app.get("/api/jobs/search", tags=["Jobs"], dependencies=[Depends(rate_limit), Depends(check_api_key)])
async def search_jobs(
    q: str = Query(..., min_length=1, max_length=120, description="Search query"),
    limit: int = Query(50, ge=1, le=200),
):
    """Search jobs by title, company, or location."""
    search_term = q.strip().lower()
    jobs = load_jobs_data()

    results = []
    for job in jobs:
        title = str(job.get('title', '')).lower()
        company = str(job.get('company', '')).lower()
        location = str(job.get('location', '')).lower()
        desc = str(job.get('description', '')).lower()

        if search_term in title or search_term in company or search_term in location or search_term in desc:
            results.append(job)
            if len(results) >= limit:
                break

    return {"query": search_term, "count": len(results), "jobs": results}


@app.get("/api/stats", tags=["Analysis"], dependencies=[Depends(rate_limit), Depends(check_api_key)])
async def get_stats():
    """Job market statistics overview."""
    analysis = load_latest_analysis()
    return {
        "total_jobs": analysis.get('metadata', {}).get('total_jobs', 0),
        "unique_companies": analysis.get('top_companies', {}).get('total_unique', 0),
        "unique_locations": analysis.get('top_locations', {}).get('total_unique', 0),
        "skills_identified": len(analysis.get('skills', {}).get('data', {})),
        "analysis_date": analysis.get('metadata', {}).get('analysis_date', ''),
        "experience_levels": analysis.get('experience_levels', {}),
        "job_types": analysis.get('job_types', {}),
    }


@app.get("/api/skills", tags=["Analysis"], dependencies=[Depends(rate_limit), Depends(check_api_key)])
async def get_skills():
    """Top skill rankings from analysis."""
    analysis = load_latest_analysis()
    skills = analysis.get('skills', {})
    return {
        "top_10": skills.get('top_10', {}),
        "all_skills": skills.get('data', {}),
    }


@app.get("/api/companies", tags=["Analysis"], dependencies=[Depends(rate_limit), Depends(check_api_key)])
async def get_companies():
    """Top hiring companies."""
    analysis = load_latest_analysis()
    companies = analysis.get('top_companies', {})
    return {
        "total_unique": companies.get('total_unique', 0),
        "top_companies": companies.get('data', {}),
    }


@app.get("/api/locations", tags=["Analysis"], dependencies=[Depends(rate_limit), Depends(check_api_key)])
async def get_locations():
    """Job distribution by location."""
    analysis = load_latest_analysis()
    locations = analysis.get('top_locations', {})
    return {
        "total_unique": locations.get('total_unique', 0),
        "top_locations": locations.get('data', {}),
    }


@app.get("/api/alerts", tags=["Alerts"], dependencies=[Depends(rate_limit), Depends(check_api_key)])
async def get_alerts():
    """Alert matches."""
    matches_file = REPORTS_DIR / 'alert_matches.json'
    if not matches_file.exists():
        return {"message": "No alert matches found", "alerts": {}}
    try:
        with open(matches_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as exc:
        logger.exception('Failed loading alert matches: %s', exc)
        raise HTTPException(status_code=500, detail="Failed to load alert matches")


@app.get("/api/trends", tags=["Analysis"], dependencies=[Depends(rate_limit), Depends(check_api_key)])
async def get_trends():
    """Trend data over time."""
    trends_file = REPORTS_DIR / 'trends_history.json'
    if not trends_file.exists():
        return {"message": "No trend data available", "snapshots": []}
    try:
        with open(trends_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as exc:
        logger.exception('Failed loading trend data: %s', exc)
        raise HTTPException(status_code=500, detail="Failed to load trend data")


@app.post("/api/salary/predict", tags=["Salary"], response_model=SalaryResponse,
          dependencies=[Depends(rate_limit), Depends(check_api_key)])
async def predict_salary(body: SalaryRequest):
    """Predict salary for a job using the ML model."""
    try:
        from salary_predictor import SalaryPredictor
        predictor = SalaryPredictor()
        result = predictor.predict({
            "title": body.title,
            "location": body.location or "",
            "skills": body.skills or "",
            "company_size": body.company_size or "Medium",
        })
        return result
    except Exception as exc:
        logger.exception('Salary prediction failed: %s', exc)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}")


# ──────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────
def main():
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description='Job Analysis API Server (FastAPI)')
    parser.add_argument('--port', type=int, default=8000, help='Port number (default: 8000)')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host address')
    args = parser.parse_args()

    print("=" * 60)
    print("  JOB ANALYSIS API SERVER (FastAPI)")
    print("=" * 60)
    print(f"\n  Server: http://{args.host}:{args.port}")
    print(f"  Docs:   http://{args.host}:{args.port}/docs")
    print("\n  Press Ctrl+C to stop\n")

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
