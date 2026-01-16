"""
Enhanced Job Analysis Dashboard
===============================
Web dashboard showing all job analysis visualizations and insights.

Features:
- Job trends & market overview
- Skill trending analysis
- Jobs by company
- Jobs by company role
- Market numbers
- User profile matching
- Skill gap analysis

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
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
REPORTS_DIR = PROJECT_ROOT / 'outputs' / 'reports'
DATA_DIR = PROJECT_ROOT / 'data' / 'raw'
CONFIG_DIR = PROJECT_ROOT / 'config'


def load_latest_analysis():
    """Load the most recent analysis results."""
    files = list(REPORTS_DIR.glob('analysis_*.json'))
    if not files:
        return {}
    latest = max(files, key=lambda f: f.stat().st_mtime)
    with open(latest, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_user_profile():
    """Load user profile if exists."""
    profile_file = CONFIG_DIR / 'user_profile.json'
    if profile_file.exists():
        with open(profile_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def load_job_matches():
    """Load latest job matches."""
    files = list(REPORTS_DIR.glob('job_matches_*.json'))
    if not files:
        return []
    latest = max(files, key=lambda f: f.stat().st_mtime)
    with open(latest, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('matches', [])


def load_alert_matches():
    """Load alert matches."""
    alerts_file = REPORTS_DIR / 'alert_matches.json'
    if alerts_file.exists():
        with open(alerts_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def generate_dashboard_html():
    """Generate the enhanced dashboard HTML."""
    data = load_latest_analysis()
    profile = load_user_profile()
    matches = load_job_matches()
    alerts = load_alert_matches()
    
    if not data:
        return """<html><body style="font-family:Arial;padding:50px;text-align:center;">
            <h1>No Data Available</h1><p>Run: python scripts/master_flow.py</p></body></html>"""
    
    metadata = data.get('metadata', {})
    skills = data.get('skills', {}).get('top_10', {})
    companies = data.get('top_companies', {}).get('data', {})
    locations = data.get('top_locations', {}).get('data', {})
    exp_levels = data.get('experience_levels', {})
    job_types = data.get('job_types', {})
    
    # Generate chart data for JavaScript
    skills_labels = json.dumps(list(skills.keys())[:10])
    skills_values = json.dumps(list(skills.values())[:10])
    
    companies_labels = json.dumps(list(companies.keys())[:10])
    companies_values = json.dumps(list(companies.values())[:10])
    
    locations_labels = json.dumps(list(locations.keys())[:10])
    locations_values = json.dumps(list(locations.values())[:10])
    
    exp_labels = json.dumps(list(exp_levels.keys()))
    exp_values = json.dumps(list(exp_levels.values()))
    
    # Job matches HTML
    matches_html = ""
    if matches:
        for i, m in enumerate(matches[:5], 1):
            score = m.get('score', 0)
            matches_html += f"""
            <div class="match-card">
                <div class="match-score">{score:.0f}%</div>
                <div class="match-details">
                    <strong>{m.get('title', 'N/A')}</strong><br>
                    <span>{m.get('company', 'N/A')} - {m.get('location', 'N/A')}</span>
                </div>
            </div>"""
    else:
        matches_html = "<p>No matches yet. Create a profile first.</p>"
    
    # Profile HTML
    profile_html = ""
    if profile:
        profile_html = f"""
        <p><strong>Name:</strong> {profile.get('name', 'N/A')}</p>
        <p><strong>Title:</strong> {profile.get('title', 'N/A')}</p>
        <p><strong>Skills:</strong> {', '.join(profile.get('skills', [])[:5])}</p>
        """
    else:
        profile_html = "<p>No profile created. Run: python scripts/cli.py match --profile</p>"
    
    # Alerts HTML
    alerts_html = ""
    if alerts.get('alerts'):
        for name, info in alerts['alerts'].items():
            count = info.get('count', 0)
            if count > 0:
                alerts_html += f'<div class="alert-item"><span class="alert-count">{count}</span> {name}</div>'
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LinkedIn Job Analysis Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f0f2f5;
            color: #333;
        }}
        .header {{
            background: linear-gradient(135deg, #0077b5 0%, #00a0dc 100%);
            color: white;
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header h1 {{ font-size: 24px; }}
        .header .date {{ opacity: 0.8; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stat-number {{
            font-size: 36px;
            font-weight: bold;
            color: #0077b5;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 20px;
        }}
        .chart-card {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .chart-card h3 {{
            margin-bottom: 15px;
            color: #333;
            border-bottom: 2px solid #0077b5;
            padding-bottom: 10px;
        }}
        .sidebar-grid {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
        }}
        .profile-card, .matches-card, .alerts-card {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .profile-card h3, .matches-card h3, .alerts-card h3 {{
            color: #0077b5;
            margin-bottom: 15px;
        }}
        .match-card {{
            display: flex;
            align-items: center;
            padding: 10px;
            border-bottom: 1px solid #eee;
        }}
        .match-score {{
            background: #0077b5;
            color: white;
            padding: 8px 12px;
            border-radius: 8px;
            font-weight: bold;
            margin-right: 15px;
        }}
        .match-details {{ flex: 1; }}
        .match-details strong {{ color: #333; }}
        .match-details span {{ color: #666; font-size: 14px; }}
        .alert-item {{
            padding: 10px;
            background: #fff3cd;
            border-radius: 8px;
            margin-bottom: 10px;
        }}
        .alert-count {{
            background: #ff6b6b;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            margin-right: 10px;
        }}
        .nav-tabs {{
            display: flex;
            background: white;
            border-radius: 12px;
            padding: 5px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .nav-tab {{
            flex: 1;
            padding: 12px;
            text-align: center;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.3s;
        }}
        .nav-tab:hover {{ background: #f0f2f5; }}
        .nav-tab.active {{
            background: #0077b5;
            color: white;
        }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        .refresh-btn {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #0077b5;
            color: white;
            border: none;
            padding: 15px 25px;
            border-radius: 50px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,119,181,0.4);
        }}
        .refresh-btn:hover {{ background: #005885; }}
        @media (max-width: 1200px) {{
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .charts-grid {{ grid-template-columns: 1fr; }}
            .sidebar-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>LinkedIn Job Analysis Dashboard</h1>
        <div class="date">Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
    </div>
    
    <div class="container">
        <!-- Navigation Tabs -->
        <div class="nav-tabs">
            <div class="nav-tab active" onclick="showTab('overview')">Overview</div>
            <div class="nav-tab" onclick="showTab('skills')">Skills Trending</div>
            <div class="nav-tab" onclick="showTab('companies')">By Company</div>
            <div class="nav-tab" onclick="showTab('locations')">By Location</div>
            <div class="nav-tab" onclick="showTab('profile')">Your Profile</div>
        </div>
        
        <!-- Overview Tab -->
        <div id="overview" class="tab-content active">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{metadata.get('total_jobs', 0)}</div>
                    <div class="stat-label">Total Jobs</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{data.get('top_companies', {}).get('total_unique', 0)}</div>
                    <div class="stat-label">Companies Hiring</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{data.get('top_locations', {}).get('total_unique', 0)}</div>
                    <div class="stat-label">Locations</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(data.get('skills', {}).get('data', {}))}</div>
                    <div class="stat-label">Skills Tracked</div>
                </div>
            </div>
            
            <div class="charts-grid">
                <div class="chart-card">
                    <h3>Top Skills in Demand</h3>
                    <canvas id="skillsChart"></canvas>
                </div>
                <div class="chart-card">
                    <h3>Experience Level Distribution</h3>
                    <canvas id="expChart"></canvas>
                </div>
            </div>
        </div>
        
        <!-- Skills Tab -->
        <div id="skills" class="tab-content">
            <div class="chart-card">
                <h3>Skills Trending Analysis</h3>
                <canvas id="skillsTrendChart" height="400"></canvas>
            </div>
        </div>
        
        <!-- Companies Tab -->
        <div id="companies" class="tab-content">
            <div class="chart-card">
                <h3>Jobs by Company</h3>
                <canvas id="companiesChart" height="400"></canvas>
            </div>
        </div>
        
        <!-- Locations Tab -->
        <div id="locations" class="tab-content">
            <div class="chart-card">
                <h3>Jobs by Location</h3>
                <canvas id="locationsChart" height="400"></canvas>
            </div>
        </div>
        
        <!-- Profile Tab -->
        <div id="profile" class="tab-content">
            <div class="sidebar-grid">
                <div>
                    <div class="matches-card">
                        <h3>Your Top Job Matches</h3>
                        {matches_html}
                    </div>
                    
                    <div class="alerts-card">
                        <h3>Job Alerts</h3>
                        {alerts_html if alerts_html else '<p>No alerts configured</p>'}
                    </div>
                </div>
                <div>
                    <div class="profile-card">
                        <h3>Your Profile</h3>
                        {profile_html}
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <button class="refresh-btn" onclick="location.reload()">Refresh</button>
    
    <script>
        // Tab switching
        function showTab(tabId) {{
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
        }}
        
        // Skills Chart
        new Chart(document.getElementById('skillsChart'), {{
            type: 'bar',
            data: {{
                labels: {skills_labels},
                datasets: [{{
                    label: 'Job Count',
                    data: {skills_values},
                    backgroundColor: 'rgba(0, 119, 181, 0.8)'
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                plugins: {{ legend: {{ display: false }} }}
            }}
        }});
        
        // Skills Trend Chart
        new Chart(document.getElementById('skillsTrendChart'), {{
            type: 'bar',
            data: {{
                labels: {skills_labels},
                datasets: [{{
                    label: 'Demand Score',
                    data: {skills_values},
                    backgroundColor: [
                        '#0077b5', '#00a0dc', '#0073b1', '#004182',
                        '#0077b5', '#00a0dc', '#0073b1', '#004182',
                        '#0077b5', '#00a0dc'
                    ]
                }}]
            }},
            options: {{ responsive: true }}
        }});
        
        // Experience Chart
        new Chart(document.getElementById('expChart'), {{
            type: 'doughnut',
            data: {{
                labels: {exp_labels},
                datasets: [{{
                    data: {exp_values},
                    backgroundColor: ['#28a745', '#17a2b8', '#ffc107', '#dc3545']
                }}]
            }},
            options: {{ responsive: true }}
        }});
        
        // Companies Chart
        new Chart(document.getElementById('companiesChart'), {{
            type: 'bar',
            data: {{
                labels: {companies_labels},
                datasets: [{{
                    label: 'Open Positions',
                    data: {companies_values},
                    backgroundColor: 'rgba(0, 160, 220, 0.8)'
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true
            }}
        }});
        
        // Locations Chart
        new Chart(document.getElementById('locationsChart'), {{
            type: 'bar',
            data: {{
                labels: {locations_labels},
                datasets: [{{
                    label: 'Jobs Available',
                    data: {locations_values},
                    backgroundColor: 'rgba(0, 115, 177, 0.8)'
                }}]
            }},
            options: {{ responsive: true }}
        }});
    </script>
</body>
</html>"""
    
    return html


class DashboardHandler(BaseHTTPRequestHandler):
    """Handle dashboard requests."""
    
    def do_GET(self):
        if self.path == '/' or self.path == '/dashboard':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = generate_dashboard_html()
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
