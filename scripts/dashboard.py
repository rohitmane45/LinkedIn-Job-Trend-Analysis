"""
Professional Job Analysis Dashboard
====================================
Modern web dashboard with real-time job market insights and analytics.

Features:
- Interactive charts with animations
- Dark/Light mode toggle
- Responsive design
- Real-time data refresh
- Profile matching & skill gaps

Now powered by Jinja2 templates for maintainability.

Usage:
    python dashboard.py
    
Then open http://127.0.0.1:5000 in your browser.
"""

import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from dashboard_data import (
    load_latest_analysis,
    load_user_profile,
    load_job_matches,
    load_alert_matches,
)

# ──────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"

# ──────────────────────────────────────────────────────────────
# Jinja2 Environment
# ──────────────────────────────────────────────────────────────
_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
)


def render_dashboard() -> str:
    """Render the dashboard HTML using Jinja2 templates."""
    data = load_latest_analysis()
    profile = load_user_profile()
    matches = load_job_matches()
    alerts = load_alert_matches()

    if not data:
        try:
            template = _jinja_env.get_template("no_data.html")
            return template.render()
        except TemplateNotFound:
            return "<h1>No Data Available</h1><p>Run: python scripts/master_flow.py</p>"

    # ── Extract data for template context ──
    metadata = data.get('metadata', {})
    skills_data = data.get('skills', {})
    skills = skills_data.get('top_10', {}) if isinstance(skills_data, dict) else {}
    companies = data.get('top_companies', {}).get('data', {})
    locations = data.get('top_locations', {}).get('data', {})
    titles = data.get('top_titles', {}).get('data', {})
    exp_levels = data.get('experience_levels', {})

    # Fallback: use titles as skill data if skills are empty
    if not skills and titles:
        skills = titles

    # Chart data (JSON-serialized for JavaScript)
    skills_labels = json.dumps(list(skills.keys())[:10]) if skills else json.dumps([])
    skills_values = json.dumps(list(skills.values())[:10]) if skills else json.dumps([])
    companies_labels = json.dumps(list(companies.keys())[:10])
    companies_values = json.dumps(list(companies.values())[:10])
    locations_labels = json.dumps(list(locations.keys())[:10])
    locations_values = json.dumps(list(locations.values())[:10])
    exp_labels = json.dumps(list(exp_levels.keys()) if exp_levels else ['Entry', 'Mid', 'Senior'])
    exp_values = json.dumps(list(exp_levels.values()) if exp_levels else [30, 45, 25])

    # Stats
    total_jobs = metadata.get('total_jobs', 0)
    total_companies = data.get('top_companies', {}).get('total_unique', 0)
    total_locations = data.get('top_locations', {}).get('total_unique', 0)
    skills_data_dict = data.get('skills', {})
    total_skills = (
        len(skills_data_dict.get('data', {}))
        if isinstance(skills_data_dict, dict)
        else len(skills) if skills else 0
    )

    # Titles table rows
    titles_table = []
    if titles:
        max_title_count = max(titles.values()) if titles.values() else 1
        for i, (title, count) in enumerate(list(titles.items())[:8], 1):
            bar_width = min(count / max_title_count * 100, 100) if max_title_count > 0 else 0
            titles_table.append({
                "rank": i,
                "title": title,
                "count": count,
                "bar_width": bar_width,
            })

    # Build template context
    context = {
        "last_updated": datetime.now().strftime('%B %d, %Y at %H:%M'),
        "total_jobs": total_jobs,
        "total_companies": total_companies,
        "total_locations": total_locations,
        "total_skills": total_skills,
        "titles_table": titles_table,
        "matches": matches,
        "profile": profile,
        "skills_labels": skills_labels,
        "skills_values": skills_values,
        "companies_labels": companies_labels,
        "companies_values": companies_values,
        "locations_labels": locations_labels,
        "locations_values": locations_values,
        "exp_labels": exp_labels,
        "exp_values": exp_values,
    }

    template = _jinja_env.get_template("dashboard.html")
    return template.render(**context)


class DashboardHandler(BaseHTTPRequestHandler):
    """Handle dashboard requests."""

    def do_GET(self):
        if self.path == '/' or self.path == '/dashboard':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = render_dashboard()
            self.wfile.write(html.encode('utf-8'))
        elif self.path == '/api/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            data = load_latest_analysis()
            self.wfile.write(json.dumps(data).encode('utf-8'))
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass


def main():
    host = '127.0.0.1'
    port = 5000

    server = HTTPServer((host, port), DashboardHandler)

    print("=" * 60)
    print("  LinkedIn Job Analysis Dashboard")
    print("=" * 60)
    print(f"\n  Dashboard: http://{host}:{port}")
    print("\n  Press Ctrl+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Dashboard stopped")
        server.shutdown()


if __name__ == "__main__":
    main()
