"""
Dashboard data loaders.

Extracted from dashboard.py to keep data access separate from HTML rendering.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
REPORTS_DIR = PROJECT_ROOT / 'outputs' / 'reports'
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
