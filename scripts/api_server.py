"""
Job Analysis API Server
=======================
REST API for accessing job data and analysis.

Usage:
    python api_server.py
    
Endpoints:
    GET  /api/jobs              - List all jobs
    GET  /api/jobs/search?q=    - Search jobs
    GET  /api/stats             - Get statistics
    GET  /api/skills            - Get skill rankings
    GET  /api/companies         - Get top companies
    GET  /api/alerts            - Get alert matches
"""

import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
REPORTS_DIR = PROJECT_ROOT / 'outputs' / 'reports'
DATA_DIR = PROJECT_ROOT / 'data' / 'raw'


class APIHandler(BaseHTTPRequestHandler):
    """Handle API requests."""
    
    def _send_json(self, data: dict, status: int = 200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def _send_error(self, message: str, status: int = 400):
        """Send error response."""
        self._send_json({'error': message, 'status': status}, status)
    
    def _load_latest_analysis(self) -> dict:
        """Load most recent analysis file."""
        files = list(REPORTS_DIR.glob('analysis_*.json'))
        if not files:
            return {}
        latest = max(files, key=lambda f: f.stat().st_mtime)
        with open(latest, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_jobs_data(self) -> list:
        """Load jobs from data files."""
        # Try database first
        db_file = PROJECT_ROOT / 'data' / 'jobs.db'
        if db_file.exists():
            try:
                from database import JobDatabase
                with JobDatabase() as db:
                    return db.get_recent_jobs(days=30, limit=500)
            except:
                pass
        
        # Fall back to CSV/JSON
        try:
            import pandas as pd
            csv_files = list(DATA_DIR.glob('jobs_*.csv'))
            if csv_files:
                latest = max(csv_files, key=lambda f: f.stat().st_mtime)
                df = pd.read_csv(latest)
                return df.to_dict('records')
        except:
            pass
        
        # Try JSON
        json_files = list(DATA_DIR.glob('jobs_*.json'))
        if json_files:
            latest = max(json_files, key=lambda f: f.stat().st_mtime)
            with open(latest, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else data.get('jobs', [])
        
        return []
    
    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        
        # API Routes
        if path == '/api/jobs':
            self._handle_jobs(query)
        elif path == '/api/jobs/search':
            self._handle_search(query)
        elif path == '/api/stats':
            self._handle_stats()
        elif path == '/api/skills':
            self._handle_skills()
        elif path == '/api/companies':
            self._handle_companies()
        elif path == '/api/locations':
            self._handle_locations()
        elif path == '/api/alerts':
            self._handle_alerts()
        elif path == '/api/trends':
            self._handle_trends()
        elif path == '/' or path == '/api':
            self._handle_root()
        else:
            self._send_error('Not found', 404)
    
    def _handle_root(self):
        """Handle root endpoint - API documentation."""
        docs = {
            'name': 'LinkedIn Job Analysis API',
            'version': '1.0',
            'endpoints': {
                '/api/jobs': 'List jobs (params: limit, offset)',
                '/api/jobs/search': 'Search jobs (params: q, limit)',
                '/api/stats': 'Get statistics',
                '/api/skills': 'Get skill rankings',
                '/api/companies': 'Get top companies',
                '/api/locations': 'Get top locations',
                '/api/alerts': 'Get alert matches',
                '/api/trends': 'Get trend data'
            }
        }
        self._send_json(docs)
    
    def _handle_jobs(self, query: dict):
        """Handle /api/jobs endpoint."""
        limit = int(query.get('limit', [50])[0])
        offset = int(query.get('offset', [0])[0])
        
        jobs = self._load_jobs_data()
        total = len(jobs)
        jobs = jobs[offset:offset + limit]
        
        self._send_json({
            'total': total,
            'limit': limit,
            'offset': offset,
            'jobs': jobs
        })
    
    def _handle_search(self, query: dict):
        """Handle /api/jobs/search endpoint."""
        search_term = query.get('q', [''])[0].lower()
        limit = int(query.get('limit', [50])[0])
        
        if not search_term:
            self._send_error('Missing search query parameter: q')
            return
        
        jobs = self._load_jobs_data()
        
        # Filter jobs
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
        
        self._send_json({
            'query': search_term,
            'count': len(results),
            'jobs': results
        })
    
    def _handle_stats(self):
        """Handle /api/stats endpoint."""
        analysis = self._load_latest_analysis()
        
        stats = {
            'total_jobs': analysis.get('metadata', {}).get('total_jobs', 0),
            'unique_companies': analysis.get('top_companies', {}).get('total_unique', 0),
            'unique_locations': analysis.get('top_locations', {}).get('total_unique', 0),
            'skills_identified': len(analysis.get('skills', {}).get('data', {})),
            'analysis_date': analysis.get('metadata', {}).get('analysis_date', ''),
            'experience_levels': analysis.get('experience_levels', {}),
            'job_types': analysis.get('job_types', {})
        }
        
        self._send_json(stats)
    
    def _handle_skills(self):
        """Handle /api/skills endpoint."""
        analysis = self._load_latest_analysis()
        skills = analysis.get('skills', {})
        
        self._send_json({
            'top_10': skills.get('top_10', {}),
            'all_skills': skills.get('data', {})
        })
    
    def _handle_companies(self):
        """Handle /api/companies endpoint."""
        analysis = self._load_latest_analysis()
        companies = analysis.get('top_companies', {})
        
        self._send_json({
            'total_unique': companies.get('total_unique', 0),
            'top_companies': companies.get('data', {})
        })
    
    def _handle_locations(self):
        """Handle /api/locations endpoint."""
        analysis = self._load_latest_analysis()
        locations = analysis.get('top_locations', {})
        
        self._send_json({
            'total_unique': locations.get('total_unique', 0),
            'top_locations': locations.get('data', {})
        })
    
    def _handle_alerts(self):
        """Handle /api/alerts endpoint."""
        matches_file = REPORTS_DIR / 'alert_matches.json'
        
        if not matches_file.exists():
            self._send_json({'message': 'No alert matches found', 'alerts': {}})
            return
        
        with open(matches_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self._send_json(data)
    
    def _handle_trends(self):
        """Handle /api/trends endpoint."""
        trends_file = REPORTS_DIR / 'trends_history.json'
        
        if not trends_file.exists():
            self._send_json({'message': 'No trend data available', 'snapshots': []})
            return
        
        with open(trends_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self._send_json(data)
    
    def log_message(self, format, *args):
        """Custom log format."""
        print(f"[API] {args[0]}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Job Analysis API Server')
    parser.add_argument('--port', type=int, default=8000, help='Port number (default: 8000)')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host address')
    
    args = parser.parse_args()
    
    server = HTTPServer((args.host, args.port), APIHandler)
    
    print("=" * 60)
    print("JOB ANALYSIS API SERVER")
    print("=" * 60)
    print(f"\nServer running at: http://{args.host}:{args.port}")
    print(f"API documentation: http://{args.host}:{args.port}/api")
    print("\nEndpoints:")
    print("  GET /api/jobs           - List all jobs")
    print("  GET /api/jobs/search?q= - Search jobs")
    print("  GET /api/stats          - Statistics")
    print("  GET /api/skills         - Skill rankings")
    print("  GET /api/companies      - Top companies")
    print("  GET /api/locations      - Top locations")
    print("  GET /api/alerts         - Alert matches")
    print("  GET /api/trends         - Trend data")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[i] Server stopped")
        server.shutdown()


if __name__ == "__main__":
    main()
