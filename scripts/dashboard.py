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
    """Generate the professional dashboard HTML."""
    data = load_latest_analysis()
    profile = load_user_profile()
    matches = load_job_matches()
    alerts = load_alert_matches()
    
    if not data:
        return """<!DOCTYPE html>
<html><head><style>
body{font-family:'Inter',sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
min-height:100vh;display:flex;align-items:center;justify-content:center;}
.error-card{background:white;padding:60px;border-radius:24px;text-align:center;box-shadow:0 25px 50px rgba(0,0,0,0.15);}
h1{color:#1a1a2e;margin-bottom:20px;}p{color:#666;font-size:18px;}
code{background:#f0f0f0;padding:10px 20px;border-radius:8px;display:inline-block;margin-top:20px;}
</style></head><body><div class="error-card">
<h1>No Data Available</h1><p>Run the analysis pipeline first:</p>
<code>python scripts/master_flow.py</code></div></body></html>"""
    
    metadata = data.get('metadata', {})
    skills_data = data.get('skills', {})
    skills = skills_data.get('top_10', {}) if isinstance(skills_data, dict) else {}
    companies = data.get('top_companies', {}).get('data', {})
    locations = data.get('top_locations', {}).get('data', {})
    titles = data.get('top_titles', {}).get('data', {})
    exp_levels = data.get('experience_levels', {})
    
    # If no skills data, use top_titles as a fallback for display
    if not skills and titles:
        skills = titles
    
    # Generate chart data for JavaScript
    skills_labels = json.dumps(list(skills.keys())[:10]) if skills else json.dumps([])
    skills_values = json.dumps(list(skills.values())[:10]) if skills else json.dumps([])
    
    companies_labels = json.dumps(list(companies.keys())[:10])
    companies_values = json.dumps(list(companies.values())[:10])
    
    locations_labels = json.dumps(list(locations.keys())[:10])
    locations_values = json.dumps(list(locations.values())[:10])
    
    titles_labels = json.dumps(list(titles.keys())[:8])
    titles_values = json.dumps(list(titles.values())[:8])
    
    exp_labels = json.dumps(list(exp_levels.keys()) if exp_levels else ['Entry', 'Mid', 'Senior'])
    exp_values = json.dumps(list(exp_levels.values()) if exp_levels else [30, 45, 25])
    
    # Job matches HTML
    matches_html = ""
    if matches:
        for i, m in enumerate(matches[:6], 1):
            score = m.get('score', 0)
            score_color = '#10b981' if score >= 70 else '#f59e0b' if score >= 40 else '#ef4444'
            matches_html += f"""
            <div class="match-item" style="animation-delay: {i * 0.1}s">
                <div class="match-rank">#{i}</div>
                <div class="match-info">
                    <div class="match-title">{m.get('title', 'N/A')}</div>
                    <div class="match-company">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 21h18M5 21V7l8-4v18M19 21V11l-6-4M9 9v.01M9 12v.01M9 15v.01M9 18v.01"/>
                        </svg>
                        {m.get('company', 'N/A')}
                    </div>
                    <div class="match-location">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/>
                        </svg>
                        {m.get('location', 'N/A')}
                    </div>
                </div>
                <div class="match-score" style="background: {score_color}">{score:.0f}%</div>
            </div>"""
    else:
        matches_html = """<div class="empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="1.5">
                <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>
            </svg>
            <p>Create your profile to see job matches</p>
            <code>python scripts/cli.py match --profile</code>
        </div>"""
    
    # Profile HTML
    profile_html = ""
    if profile:
        skills_tags = ''.join([f'<span class="skill-tag">{s}</span>' for s in profile.get('skills', [])[:6]])
        location_tags = ''.join([f'<span class="location-tag">{l}</span>' for l in profile.get('preferred_locations', [])[:3]])
        profile_html = f"""
        <div class="profile-header">
            <div class="profile-avatar">{profile.get('name', 'U')[0].upper()}</div>
            <div class="profile-info">
                <h3>{profile.get('name', 'User')}</h3>
                <p>{profile.get('title', 'Job Seeker')}</p>
            </div>
        </div>
        <div class="profile-section">
            <label>Experience</label>
            <span class="experience-badge">{profile.get('experience_years', 0)} years</span>
        </div>
        <div class="profile-section">
            <label>Skills</label>
            <div class="tags-container">{skills_tags}</div>
        </div>
        <div class="profile-section">
            <label>Preferred Locations</label>
            <div class="tags-container">{location_tags}</div>
        </div>
        """
    else:
        profile_html = """<div class="empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="1.5">
                <circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>
            </svg>
            <p>No profile configured</p>
            <code>python scripts/cli.py match --profile</code>
        </div>"""
    
    # Top titles for the table
    titles_rows = ""
    if titles:
        max_title_count = max(titles.values()) if titles.values() else 1
        for i, (title, count) in enumerate(list(titles.items())[:8], 1):
            bar_width = min(count / max_title_count * 100, 100) if max_title_count > 0 else 0
            titles_rows += f"""<tr>
                <td><span class="rank-badge">{i}</span></td>
                <td>{title}</td>
                <td><div class="bar-cell"><div class="bar-fill" style="width: {bar_width}%"></div><span>{count}</span></div></td>
            </tr>"""
    
    # Pre-compute stats for the template
    total_jobs = metadata.get('total_jobs', 0)
    total_companies = data.get('top_companies', {}).get('total_unique', 0)
    total_locations = data.get('top_locations', {}).get('total_unique', 0)
    skills_data_dict = data.get('skills', {})
    total_skills = len(skills_data_dict.get('data', {})) if isinstance(skills_data_dict, dict) else len(skills) if skills else 0
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Market Analytics Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #1e293b;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --accent: #3b82f6;
            --accent-hover: #2563eb;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --border: #334155;
            --gradient-1: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --gradient-2: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --gradient-3: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.2);
        }}
        
        [data-theme="light"] {{
            --bg-primary: #f8fafc;
            --bg-secondary: #ffffff;
            --bg-card: #ffffff;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border: #e2e8f0;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            transition: all 0.3s ease;
        }}
        
        /* Sidebar */
        .sidebar {{
            position: fixed;
            left: 0;
            top: 0;
            bottom: 0;
            width: 260px;
            background: var(--bg-secondary);
            border-right: 1px solid var(--border);
            padding: 24px 16px;
            z-index: 100;
            transition: transform 0.3s ease;
        }}
        
        .logo {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 0 12px 24px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 24px;
        }}
        
        .logo-icon {{
            width: 40px;
            height: 40px;
            background: var(--gradient-1);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .logo-icon svg {{ color: white; }}
        
        .logo-text {{
            font-size: 18px;
            font-weight: 700;
            color: var(--text-primary);
        }}
        
        .nav-menu {{ list-style: none; }}
        
        .nav-item {{
            margin-bottom: 4px;
        }}
        
        .nav-link {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            border-radius: 10px;
            color: var(--text-secondary);
            text-decoration: none;
            font-weight: 500;
            transition: all 0.2s ease;
            cursor: pointer;
        }}
        
        .nav-link:hover {{
            background: var(--border);
            color: var(--text-primary);
        }}
        
        .nav-link.active {{
            background: var(--accent);
            color: white;
        }}
        
        .nav-link svg {{
            width: 20px;
            height: 20px;
        }}
        
        /* Main Content */
        .main {{
            margin-left: 260px;
            padding: 24px 32px;
            min-height: 100vh;
        }}
        
        /* Header */
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 32px;
        }}
        
        .header-title h1 {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 4px;
        }}
        
        .header-title p {{
            color: var(--text-secondary);
            font-size: 14px;
        }}
        
        .header-actions {{
            display: flex;
            gap: 12px;
            align-items: center;
        }}
        
        .theme-toggle {{
            width: 44px;
            height: 44px;
            border-radius: 12px;
            border: 1px solid var(--border);
            background: var(--bg-card);
            color: var(--text-primary);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }}
        
        .theme-toggle:hover {{
            border-color: var(--accent);
            color: var(--accent);
        }}
        
        .refresh-btn {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px 20px;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        
        .refresh-btn:hover {{
            background: var(--accent-hover);
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }}
        
        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 24px;
        }}
        
        .stat-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-4px);
            box-shadow: var(--shadow-lg);
        }}
        
        .stat-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
        }}
        
        .stat-card:nth-child(1)::before {{ background: var(--gradient-1); }}
        .stat-card:nth-child(2)::before {{ background: var(--gradient-2); }}
        .stat-card:nth-child(3)::before {{ background: var(--gradient-3); }}
        .stat-card:nth-child(4)::before {{ background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); }}
        
        .stat-icon {{
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 16px;
        }}
        
        .stat-card:nth-child(1) .stat-icon {{ background: rgba(102, 126, 234, 0.15); color: #667eea; }}
        .stat-card:nth-child(2) .stat-icon {{ background: rgba(245, 87, 108, 0.15); color: #f5576c; }}
        .stat-card:nth-child(3) .stat-icon {{ background: rgba(79, 172, 254, 0.15); color: #4facfe; }}
        .stat-card:nth-child(4) .stat-icon {{ background: rgba(16, 185, 129, 0.15); color: #10b981; }}
        
        .stat-value {{
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 4px;
        }}
        
        .stat-label {{
            color: var(--text-secondary);
            font-size: 14px;
        }}
        
        /* Content Grid */
        .content-grid {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 24px;
        }}
        
        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
        }}
        
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        
        .card-title {{
            font-size: 16px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .card-title svg {{
            color: var(--accent);
        }}
        
        /* Charts */
        .chart-container {{
            position: relative;
            height: 300px;
        }}
        
        /* Table */
        .data-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .data-table th,
        .data-table td {{
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        
        .data-table th {{
            font-size: 12px;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .data-table tr:hover {{
            background: var(--bg-primary);
        }}
        
        .rank-badge {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            background: var(--accent);
            color: white;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 600;
        }}
        
        .bar-cell {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .bar-fill {{
            height: 8px;
            background: var(--gradient-1);
            border-radius: 4px;
            min-width: 20px;
        }}
        
        /* Match Items */
        .match-item {{
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 16px;
            background: var(--bg-primary);
            border-radius: 12px;
            margin-bottom: 12px;
            animation: slideIn 0.3s ease forwards;
            opacity: 0;
            transform: translateX(-20px);
        }}
        
        @keyframes slideIn {{
            to {{
                opacity: 1;
                transform: translateX(0);
            }}
        }}
        
        .match-rank {{
            font-size: 14px;
            font-weight: 600;
            color: var(--text-secondary);
            min-width: 30px;
        }}
        
        .match-info {{
            flex: 1;
        }}
        
        .match-title {{
            font-weight: 600;
            margin-bottom: 4px;
        }}
        
        .match-company,
        .match-location {{
            font-size: 13px;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        
        .match-score {{
            padding: 8px 16px;
            border-radius: 20px;
            color: white;
            font-weight: 600;
            font-size: 14px;
        }}
        
        /* Profile */
        .profile-header {{
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 24px;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--border);
        }}
        
        .profile-avatar {{
            width: 64px;
            height: 64px;
            background: var(--gradient-1);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            font-weight: 700;
            color: white;
        }}
        
        .profile-info h3 {{
            font-size: 18px;
            margin-bottom: 4px;
        }}
        
        .profile-info p {{
            color: var(--text-secondary);
            font-size: 14px;
        }}
        
        .profile-section {{
            margin-bottom: 20px;
        }}
        
        .profile-section label {{
            display: block;
            font-size: 12px;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        
        .experience-badge {{
            display: inline-block;
            padding: 6px 12px;
            background: var(--accent);
            color: white;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 500;
        }}
        
        .tags-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        
        .skill-tag {{
            padding: 6px 12px;
            background: rgba(59, 130, 246, 0.15);
            color: var(--accent);
            border-radius: 20px;
            font-size: 13px;
            font-weight: 500;
        }}
        
        .location-tag {{
            padding: 6px 12px;
            background: rgba(16, 185, 129, 0.15);
            color: var(--success);
            border-radius: 20px;
            font-size: 13px;
            font-weight: 500;
        }}
        
        /* Empty State */
        .empty-state {{
            text-align: center;
            padding: 40px 20px;
            color: var(--text-secondary);
        }}
        
        .empty-state svg {{
            margin-bottom: 16px;
        }}
        
        .empty-state p {{
            margin-bottom: 12px;
        }}
        
        .empty-state code {{
            display: inline-block;
            padding: 8px 16px;
            background: var(--bg-primary);
            border-radius: 8px;
            font-size: 13px;
        }}
        
        /* Tab Content */
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
            animation: fadeIn 0.3s ease;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        /* Responsive */
        @media (max-width: 1200px) {{
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .content-grid {{ grid-template-columns: 1fr; }}
        }}
        
        @media (max-width: 768px) {{
            .sidebar {{
                transform: translateX(-100%);
            }}
            .main {{
                margin-left: 0;
                padding: 16px;
            }}
            .stats-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <!-- Sidebar -->
    <aside class="sidebar">
        <div class="logo">
            <div class="logo-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/>
                    <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
                    <line x1="12" y1="22.08" x2="12" y2="12"/>
                </svg>
            </div>
            <span class="logo-text">JobAnalytics</span>
        </div>
        
        <nav>
            <ul class="nav-menu">
                <li class="nav-item">
                    <a class="nav-link active" onclick="showTab('overview', this)">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/>
                            <rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/>
                        </svg>
                        Overview
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" onclick="showTab('skills', this)">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                        </svg>
                        Skills Analysis
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" onclick="showTab('companies', this)">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 21h18M5 21V7l8-4v18M19 21V11l-6-4"/>
                        </svg>
                        Companies
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" onclick="showTab('locations', this)">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/>
                        </svg>
                        Locations
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" onclick="showTab('profile', this)">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>
                        </svg>
                        Your Profile
                    </a>
                </li>
            </ul>
        </nav>
    </aside>
    
    <!-- Main Content -->
    <main class="main">
        <header class="header">
            <div class="header-title">
                <h1>Job Market Dashboard</h1>
                <p>Last updated: {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
            </div>
            <div class="header-actions">
                <button class="theme-toggle" onclick="toggleTheme()" title="Toggle theme">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
                    </svg>
                </button>
                <button class="refresh-btn" onclick="location.reload()">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
                    </svg>
                    Refresh
                </button>
            </div>
        </header>
        
        <!-- Overview Tab -->
        <div id="overview" class="tab-content active">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16"/>
                        </svg>
                    </div>
                    <div class="stat-value">{total_jobs:,}</div>
                    <div class="stat-label">Total Jobs</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 21h18M5 21V7l8-4v18M19 21V11l-6-4"/>
                        </svg>
                    </div>
                    <div class="stat-value">{total_companies}</div>
                    <div class="stat-label">Companies Hiring</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/>
                        </svg>
                    </div>
                    <div class="stat-value">{total_locations}</div>
                    <div class="stat-label">Locations</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5"/>
                        </svg>
                    </div>
                    <div class="stat-value">{total_skills}</div>
                    <div class="stat-label">Skills Tracked</div>
                </div>
            </div>
            
            <div class="content-grid">
                <div>
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M12 20V10M18 20V4M6 20v-4"/>
                                </svg>
                                Top Skills in Demand
                            </h3>
                        </div>
                        <div class="chart-container">
                            <canvas id="skillsChart"></canvas>
                        </div>
                    </div>
                    
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16"/>
                                </svg>
                                Top Job Titles
                            </h3>
                        </div>
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Rank</th>
                                    <th>Title</th>
                                    <th>Open Positions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {titles_rows}
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <div>
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
                                </svg>
                                Experience Distribution
                            </h3>
                        </div>
                        <div class="chart-container">
                            <canvas id="expChart"></canvas>
                        </div>
                    </div>
                    
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/>
                                </svg>
                                Jobs by Location
                            </h3>
                        </div>
                        <div class="chart-container">
                            <canvas id="locationsOverviewChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Skills Tab -->
        <div id="skills" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                        </svg>
                        Skills Trending Analysis
                    </h3>
                </div>
                <div style="height: 500px;">
                    <canvas id="skillsTrendChart"></canvas>
                </div>
            </div>
        </div>
        
        <!-- Companies Tab -->
        <div id="companies" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 21h18M5 21V7l8-4v18M19 21V11l-6-4"/>
                        </svg>
                        Top Hiring Companies
                    </h3>
                </div>
                <div style="height: 500px;">
                    <canvas id="companiesChart"></canvas>
                </div>
            </div>
        </div>
        
        <!-- Locations Tab -->
        <div id="locations" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/>
                        </svg>
                        Jobs Distribution by Location
                    </h3>
                </div>
                <div style="height: 500px;">
                    <canvas id="locationsChart"></canvas>
                </div>
            </div>
        </div>
        
        <!-- Profile Tab -->
        <div id="profile" class="tab-content">
            <div class="content-grid">
                <div>
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
                                </svg>
                                Your Job Matches
                            </h3>
                        </div>
                        {matches_html}
                    </div>
                </div>
                <div>
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>
                                </svg>
                                Your Profile
                            </h3>
                        </div>
                        {profile_html}
                    </div>
                </div>
            </div>
        </div>
    </main>
    
    <script>
        // Theme Toggle
        function toggleTheme() {{
            const body = document.body;
            const currentTheme = body.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            body.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateChartColors();
        }}
        
        // Load saved theme
        const savedTheme = localStorage.getItem('theme') || 'dark';
        document.body.setAttribute('data-theme', savedTheme);
        
        // Tab switching
        function showTab(tabId, element) {{
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.nav-link').forEach(t => t.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            element.classList.add('active');
        }}
        
        // Chart colors
        function getChartColors() {{
            const isDark = document.body.getAttribute('data-theme') !== 'light';
            return {{
                text: isDark ? '#f1f5f9' : '#1e293b',
                grid: isDark ? '#334155' : '#e2e8f0',
                gradient1: ['rgba(102, 126, 234, 0.8)', 'rgba(118, 75, 162, 0.8)'],
                gradient2: ['rgba(79, 172, 254, 0.8)', 'rgba(0, 242, 254, 0.8)'],
                gradient3: ['rgba(240, 147, 251, 0.8)', 'rgba(245, 87, 108, 0.8)']
            }};
        }}
        
        // Chart default options
        Chart.defaults.color = getChartColors().text;
        Chart.defaults.borderColor = getChartColors().grid;
        
        // Skills Chart
        const skillsCtx = document.getElementById('skillsChart').getContext('2d');
        const skillsGradient = skillsCtx.createLinearGradient(0, 0, 400, 0);
        skillsGradient.addColorStop(0, 'rgba(102, 126, 234, 0.8)');
        skillsGradient.addColorStop(1, 'rgba(118, 75, 162, 0.8)');
        
        new Chart(skillsCtx, {{
            type: 'bar',
            data: {{
                labels: {skills_labels},
                datasets: [{{
                    label: 'Jobs',
                    data: {skills_values},
                    backgroundColor: skillsGradient,
                    borderRadius: 6,
                    borderSkipped: false
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ grid: {{ display: false }} }},
                    y: {{ grid: {{ display: false }} }}
                }}
            }}
        }});
        
        // Experience Chart
        new Chart(document.getElementById('expChart'), {{
            type: 'doughnut',
            data: {{
                labels: {exp_labels},
                datasets: [{{
                    data: {exp_values},
                    backgroundColor: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444'],
                    borderWidth: 0,
                    cutout: '70%'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{ padding: 20, usePointStyle: true, pointStyle: 'circle' }}
                    }}
                }}
            }}
        }});
        
        // Locations Overview Chart
        new Chart(document.getElementById('locationsOverviewChart'), {{
            type: 'polarArea',
            data: {{
                labels: {locations_labels},
                datasets: [{{
                    data: {locations_values},
                    backgroundColor: [
                        'rgba(102, 126, 234, 0.7)',
                        'rgba(79, 172, 254, 0.7)',
                        'rgba(16, 185, 129, 0.7)',
                        'rgba(245, 158, 11, 0.7)',
                        'rgba(239, 68, 68, 0.7)'
                    ],
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{ padding: 15, usePointStyle: true, pointStyle: 'circle' }}
                    }}
                }}
            }}
        }});
        
        // Skills Trend Chart
        const trendCtx = document.getElementById('skillsTrendChart').getContext('2d');
        const trendGradient = trendCtx.createLinearGradient(0, 0, 0, 500);
        trendGradient.addColorStop(0, 'rgba(102, 126, 234, 0.8)');
        trendGradient.addColorStop(1, 'rgba(79, 172, 254, 0.8)');
        
        new Chart(trendCtx, {{
            type: 'bar',
            data: {{
                labels: {skills_labels},
                datasets: [{{
                    label: 'Demand Score',
                    data: {skills_values},
                    backgroundColor: trendGradient,
                    borderRadius: 8,
                    borderSkipped: false
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    y: {{ beginAtZero: true, grid: {{ color: getChartColors().grid }} }},
                    x: {{ grid: {{ display: false }} }}
                }}
            }}
        }});
        
        // Companies Chart
        const compCtx = document.getElementById('companiesChart').getContext('2d');
        const compGradient = compCtx.createLinearGradient(0, 0, 800, 0);
        compGradient.addColorStop(0, 'rgba(79, 172, 254, 0.8)');
        compGradient.addColorStop(1, 'rgba(0, 242, 254, 0.8)');
        
        new Chart(compCtx, {{
            type: 'bar',
            data: {{
                labels: {companies_labels},
                datasets: [{{
                    label: 'Open Positions',
                    data: {companies_values},
                    backgroundColor: compGradient,
                    borderRadius: 8,
                    borderSkipped: false
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ grid: {{ color: getChartColors().grid }} }},
                    y: {{ grid: {{ display: false }} }}
                }}
            }}
        }});
        
        // Locations Chart
        const locCtx = document.getElementById('locationsChart').getContext('2d');
        const locGradient = locCtx.createLinearGradient(0, 0, 0, 500);
        locGradient.addColorStop(0, 'rgba(240, 147, 251, 0.8)');
        locGradient.addColorStop(1, 'rgba(245, 87, 108, 0.8)');
        
        new Chart(locCtx, {{
            type: 'bar',
            data: {{
                labels: {locations_labels},
                datasets: [{{
                    label: 'Jobs Available',
                    data: {locations_values},
                    backgroundColor: locGradient,
                    borderRadius: 8,
                    borderSkipped: false
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    y: {{ beginAtZero: true, grid: {{ color: getChartColors().grid }} }},
                    x: {{ grid: {{ display: false }} }}
                }}
            }}
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
