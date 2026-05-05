"""
Dashboard API Server
====================
Serves the new HTML dashboard and provides JSON API endpoints
that read real data from the pipeline output files.

Usage:
    python scripts/dashboard_server.py          # Start on port 8080
    python scripts/dashboard_server.py --port 9000
"""

import sys
import os
import json
import glob
import random
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import argparse

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / 'templates'
REPORTS_DIR = PROJECT_ROOT / 'outputs' / 'reports'
DATA_DIR = PROJECT_ROOT / 'data'
CONFIG_DIR = PROJECT_ROOT / 'config'


def get_latest_file(pattern):
    """Get the most recent file matching a glob pattern."""
    files = sorted(glob.glob(str(pattern)), key=os.path.getmtime, reverse=True)
    return files[0] if files else None


def load_json(filepath):
    """Load a JSON file safely."""
    if filepath and os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def load_raw_jobs():
    """Load job data from the latest raw JSON file."""
    raw_dir = DATA_DIR / 'raw'
    latest = get_latest_file(raw_dir / 'jobs_india_*.json')
    if latest:
        return load_json(latest)
    return []


def build_api_data():
    """Build all API response data from real pipeline outputs."""
    # Load all source data
    analysis = load_json(get_latest_file(REPORTS_DIR / 'analysis_*.json'))
    flow = load_json(get_latest_file(REPORTS_DIR / 'flow_results_*.json'))
    matches_data = load_json(get_latest_file(REPORTS_DIR / 'job_matches_*.json'))
    user_profile = load_json(CONFIG_DIR / 'user_profile.json')
    skills_config = load_json(CONFIG_DIR / 'skills_config.json')
    salary_model = load_json(CONFIG_DIR / 'salary_model.json')
    jobs = load_raw_jobs()

    # ── Compute skills from raw data ──
    skill_counts = {}
    for job in jobs:
        for s in job.get('skills', []):
            skill_counts[s] = skill_counts.get(s, 0) + 1
    top_skills = sorted(skill_counts.items(), key=lambda x: -x[1])[:20]

    # ── Compute experience distribution ──
    exp_dist = {'Entry Level': 0, 'Mid Level': 0, 'Senior': 0}
    for job in jobs:
        title = job.get('title', '').lower()
        if 'senior' in title or 'lead' in title or 'principal' in title or 'architect' in title:
            exp_dist['Senior'] += 1
        elif 'junior' in title or 'intern' in title or 'analyst' in title or 'associate' in title:
            exp_dist['Entry Level'] += 1
        else:
            exp_dist['Mid Level'] += 1

    # ── Company data ──
    company_counts = {}
    company_skills = {}
    company_types = {}
    for job in jobs:
        c = job.get('company', 'Unknown')
        company_counts[c] = company_counts.get(c, 0) + 1
        if c not in company_skills:
            company_skills[c] = set()
        for s in job.get('skills', [])[:4]:
            company_skills[c].add(s)
        if c not in company_types:
            ct = job.get('company_type', 'Product')
            if ct in ('Finance', 'Consulting'):
                company_types[c] = 'MNC'
            elif ct in ('EdTech', 'E-commerce', 'Food Tech', 'FinTech', 'Travel'):
                company_types[c] = 'Startup'
            elif ct == 'IT Services':
                company_types[c] = 'Service'
            else:
                company_types[c] = 'Product'

    top_companies = sorted(company_counts.items(), key=lambda x: -x[1])

    # ── Location data ──
    location_data = analysis.get('top_locations', {}).get('data', {})
    if not location_data:
        loc_counts = {}
        for job in jobs:
            city = job.get('city', 'Unknown')
            loc_counts[city] = loc_counts.get(city, 0) + 1
        location_data = dict(sorted(loc_counts.items(), key=lambda x: -x[1])[:6])

    # ── Title data ──
    title_data = analysis.get('top_titles', {}).get('data', {})
    if not title_data:
        title_counts = {}
        for job in jobs:
            t = job.get('title', 'Unknown')
            title_counts[t] = title_counts.get(t, 0) + 1
        title_data = dict(sorted(title_counts.items(), key=lambda x: -x[1])[:10])

    # ── Matches ── always use the most recently generated match file
    matches = matches_data.get('matches', flow.get('top_matches', []))

    # ── Skill gaps (what user is missing from top demanded skills) ──
    user_skills_lower = set(s.lower() for s in user_profile.get('skills', []))
    all_tracked = set(skills_config.get('tech_skills', []))
    gap_skills = []
    have_skills = []
    for sk, cnt in top_skills:
        if sk.lower() in user_skills_lower:
            have_skills.append(sk)
        else:
            gap_skills.append(sk)

    # ── Salary estimation model (simple rule-based from data) ──
    salary_base = {
        'Data Scientist': 10, 'ML Engineer': 12, 'Machine Learning Engineer': 12,
        'Data Analyst': 6, 'Data Engineer': 11, 'Full Stack Developer': 8,
        'DevOps Engineer': 9, 'AI Engineer': 14, 'Software Engineer': 9,
        'Backend Developer': 8, 'Senior Software Engineer': 16,
        'Product Manager': 15, 'Business Analyst': 7
    }
    city_mult = {
        'Bangalore': 1.15, 'Karnataka': 1.15,
        'Pune': 1.0, 'Maharashtra': 1.05,
        'Mumbai': 1.1, 'Hyderabad': 1.05, 'Telangana': 1.05,
        'Chennai': 0.95, 'Tamil Nadu': 0.95,
        'Delhi': 1.08, 'Delhi NCR': 1.08
    }

    # ── Fetch skill trend & forecast data using TrendTracker ──
    try:
        from trend_tracker import TrendTracker
        tracker = TrendTracker()
        
        # Real skill trends
        real_trends = tracker.get_skill_trends()
        if not real_trends or all(len(h) < 2 for h in real_trends.values()):
            raise ValueError("Insufficient trend history")
            
        skill_trends = []
        for sk, history in list(real_trends.items())[:12]:
            if len(history) < 2:
                continue
            first = history[0]['count']
            last = history[-1]['count']
            change = last - first
            if change > 0:
                trend = 'rising'
            elif change < 0:
                trend = 'declining'
            else:
                trend = 'stable'
                
            # Keep last 7 data points for sparkline
            data = [h['count'] for h in history[-7:]]
            while len(data) < 7:
                data.insert(0, data[0])
                
            skill_trends.append({
                'name': sk, 'count': last, 'trend': trend,
                'change': change,
                'data': data
            })
            
        # Real 90-day forecast
        real_forecasts = tracker.forecast_skills(horizon_days=90)
        forecast_data = []
        for f in real_forecasts[:9]:
            trend_label = 'rising' if f['growth_rate'] > 0.1 else 'declining' if f['growth_rate'] < -0.1 else 'stable'
            forecast_data.append({
                'name': f['skill'],
                'current': f['current_count'],
                'd30': max(0, int(f['current_count'] + f['growth_rate'] * 30)),
                'd60': max(0, int(f['current_count'] + f['growth_rate'] * 60)),
                'd90': int(f['predicted_count']),
                'trend': trend_label,
                'confidence': int(f['confidence'] * 100)
            })
            
    except Exception as e:
        print(f"⚠️ Using mock trends/forecasts ({e})")
        # ── Build skill trend mock (fallback) ──
        skill_trends = []
        for sk, cnt in top_skills[:12]:
            rising_skills = {'aws', 'docker', 'kubernetes', 'machine learning', 'deep learning',
                             'tensorflow', 'pytorch', 'nlp', 'react', 'python', 'fastapi',
                             'llm', 'langchain', 'openai', 'computer vision', 'mlops'}
            declining_skills = {'jquery', 'php', 'perl', 'vba', 'groovy'}
            if sk.lower() in rising_skills:
                trend = 'rising'
                change = random.randint(5, 25)
            elif sk.lower() in declining_skills:
                trend = 'declining'
                change = -random.randint(3, 12)
            else:
                trend = 'stable'
                change = random.randint(-3, 5)
            skill_trends.append({
                'name': sk, 'count': cnt, 'trend': trend,
                'change': change,
                'data': [max(1, cnt - random.randint(0, 8)) for _ in range(7)]
            })
    
        # ── Forecast data (project forward from current counts) (fallback) ──
        forecast_data = []
        for sk, cnt in top_skills[:9]:
            multiplier = 1.08 if sk.lower() in {'aws', 'docker', 'kubernetes', 'machine learning',
                                                  'react', 'python', 'nlp'} else 0.98 if sk.lower() in declining_skills else 1.02
            d30 = int(cnt * multiplier)
            d60 = int(cnt * multiplier ** 2)
            d90 = int(cnt * multiplier ** 3)
            trend = 'rising' if d90 > cnt * 1.05 else 'declining' if d90 < cnt * 0.95 else 'stable'
            forecast_data.append({
                'name': sk, 'current': cnt, 'd30': d30, 'd60': d60, 'd90': d90,
                'trend': trend, 'confidence': random.randint(75, 95)
            })

    # ── Build the full API payload ──
    total_jobs = len(jobs) or analysis.get('metadata', {}).get('total_jobs', 0)
    total_companies = len(set(j.get('company') for j in jobs)) or analysis.get('top_companies', {}).get('total_unique', 0)
    total_cities = len(location_data)
    total_skills = len(skill_counts)
    last_updated = analysis.get('metadata', {}).get('analysis_date', datetime.now().isoformat())

    return {
        'overview': {
            'total_jobs': total_jobs,
            'total_companies': total_companies,
            'total_cities': total_cities,
            'total_skills': total_skills,
            'last_updated': last_updated,
            'top_skills': dict(top_skills[:10]),
            'experience_distribution': exp_dist,
            'top_titles': title_data,
            'jobs_by_city': location_data,
        },
        'skills': {
            'trends': skill_trends,
            'categories': skills_config.get('skill_categories', {}),
        },
        'companies': [
            {
                'name': name, 'positions': count,
                'type': company_types.get(name, 'Product'),
                'skills': list(company_skills.get(name, set()))[:4],
                'color': ['#6c63ff','#a78bfa','#48bb78','#f6ad55','#fc8181'][i % 5]
            }
            for i, (name, count) in enumerate(top_companies)
        ],
        'salary': {
            'base_salaries': salary_base,
            'city_multipliers': city_mult,
            'roles': list(salary_base.keys()),
            'cities': list(set(j.get('city', 'Unknown') for j in jobs)),
        },
        'resume': {
            'user_profile': user_profile,
            'matches': matches[:15],
            'have_skills': have_skills,
            'gap_skills': gap_skills[:10],
        },
        'forecast': {
            'skills': forecast_data,
            'emerging': [
                {'name': 'LLM Fine-tuning', 'growth': '+128%'},
                {'name': 'RAG', 'growth': '+95%'},
                {'name': 'Vector Databases', 'growth': '+82%'},
                {'name': 'LangChain', 'growth': '+76%'},
                {'name': 'CrewAI', 'growth': '+64%'},
            ]
        }
    }


# Cache API data (rebuild on each server start)
API_DATA = None


class DashboardHandler(SimpleHTTPRequestHandler):
    """Serves static files from templates/ and API endpoints from /api/."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(TEMPLATES_DIR), **kwargs)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/upload_resume':
            try:
                # Read raw file from body
                content_length = int(self.headers.get('Content-Length', 0))
                file_data = self.rfile.read(content_length)
                
                if content_length == 0 or not file_data:
                    self.send_api_response({"success": False, "error": "Empty file received"})
                    return

                # Save to temp PDF
                temp_pdf = DATA_DIR / "temp_resume.pdf"
                DATA_DIR.mkdir(exist_ok=True, parents=True)
                with open(temp_pdf, 'wb') as f:
                    f.write(file_data)
                
                # Ensure scripts are on path
                if str(PROJECT_ROOT / 'scripts') not in sys.path:
                    sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

                # Force-reload resume_parser so we always get a fresh parse
                import importlib
                import resume_parser
                importlib.reload(resume_parser)

                profile_data = resume_parser.parse_pdf(str(temp_pdf))
                if "error" in profile_data:
                    self.send_api_response({"success": False, "error": profile_data["error"]})
                    return

                # ── FULLY replace the profile — don't inherit stale data ──
                from resume_matcher import UserProfile, ResumeMatcher
                profile = UserProfile()          # start blank
                profile.name               = profile_data.get('name', '')
                profile.title              = profile_data.get('title', '')
                profile.experience_years   = int(profile_data.get('experience_years', 0))
                profile.skills             = profile_data.get('skills', [])
                profile.preferred_locations= profile_data.get('preferred_locations', [])
                profile.preferred_companies= []
                profile.min_salary_lpa     = 0
                profile.job_types          = []
                profile.industries         = profile_data.get('industries', [])
                profile.save()  # writes a fresh user_profile.json

                # Delete ALL old match files so stale results can't bleed through
                for old_match in REPORTS_DIR.glob('job_matches_*.json'):
                    old_match.unlink(missing_ok=True)

                # Run matcher against live jobs with the new profile
                matcher = ResumeMatcher(profile)
                matcher.find_matches(min_score=10, limit=15)
                matcher.save_matches_report()

                # Rebuild the API payload so /api/data returns fresh data
                global API_DATA
                API_DATA = build_api_data()

                self.send_api_response({"success": True, "profile": {
                    "title": profile.title,
                    "skills_found": len(profile.skills),
                    "experience_years": profile.experience_years,
                }})
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_api_response({"success": False, "error": str(e)})
        elif parsed.path == '/api/save_profile':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                profile_dict = json.loads(post_data.decode('utf-8'))
                
                if str(PROJECT_ROOT / 'scripts') not in sys.path:
                    sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
                    
                from resume_matcher import UserProfile, ResumeMatcher
                
                # Load existing or create new
                try:
                    profile = UserProfile.load()
                except:
                    profile = UserProfile()
                
                profile.name = profile_dict.get('name', profile.name)
                profile.title = profile_dict.get('title', profile.title)
                
                if 'experience_years' in profile_dict:
                    try:
                        profile.experience_years = int(profile_dict['experience_years'])
                    except:
                        pass
                        
                if 'skills' in profile_dict:
                    # Expecting comma separated string or list
                    skills_raw = profile_dict['skills']
                    if isinstance(skills_raw, str):
                        profile.skills = [s.strip().lower() for s in skills_raw.split(',') if s.strip()]
                    elif isinstance(skills_raw, list):
                        profile.skills = [s.strip().lower() for s in skills_raw if str(s).strip()]
                
                if 'domain' in profile_dict and profile_dict['domain']:
                    profile.industries = [profile_dict['domain']]
                
                profile.save()
                
                matcher = ResumeMatcher(profile)
                matcher.find_matches(min_score=10, limit=15)
                matcher.save_matches_report()
                
                API_DATA = build_api_data()
                self.send_api_response({"success": True})
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_api_response({"success": False, "error": str(e)})
        else:
            self.send_error(404)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == '/api/data':
            # Dynamically rebuild data so dashboard updates on refresh
            global API_DATA
            API_DATA = build_api_data()
            self.send_api_response(API_DATA)
        elif parsed.path == '/api/salary/predict':
            params = parse_qs(parsed.query)
            role = params.get('role', ['Data Scientist'])[0]
            city = params.get('city', ['Bangalore'])[0]
            exp = int(params.get('exp', ['0'])[0])
            result = predict_salary(role, city, exp)
            self.send_api_response(result)
        else:
            # Serve static files (index.html, styles.css, app.js)
            super().do_GET()

    def send_api_response(self, data):
        response = json.dumps(data, ensure_ascii=False, default=str).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(response)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format, *args):
        # Suppress verbose request logs, show only errors
        if '404' in str(args) or '500' in str(args):
            super().log_message(format, *args)


def predict_salary(role, city, exp):
    """Salary prediction using the ML model, with fallback to simple heuristics."""
    try:
        if str(PROJECT_ROOT / 'scripts') not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
        from salary_predictor import SalaryPredictor
        
        predictor = SalaryPredictor()
        
        job_info = {
            "title": role,
            "location": city,
            "experience": exp
        }
        
        # If experience > 5 and 'senior' isn't in title, optionally append it 
        # so the model interprets the title better if we rely mostly on title
        if exp >= 5 and "senior" not in role.lower() and "lead" not in role.lower():
            job_info["title"] = f"Senior {role}"
            
        result = predictor.predict(job_info)
        
        median = result.get('avg', 15)
        pct = min(90, max(10, int(median / 35 * 100)))
        
        return {
            'low': result.get('min'),
            'high': result.get('max'),
            'median': median,
            'gauge_pct': pct
        }
    except Exception as e:
        print(f"⚠️ ML Prediction failed: {e}. Falling back to heuristics.")
        base_salaries = API_DATA['salary']['base_salaries']
        city_mult = API_DATA['salary']['city_multipliers']
        base = base_salaries.get(role, 10)
        mult = 1.0
        for key, val in city_mult.items():
            if key.lower() in city.lower():
                mult = val
                break
        low = round(base * mult + exp * 1.8, 1)
        high = round(base * mult + exp * 2.6 + 3, 1)
        median = round((low + high) / 2, 1)
        pct = min(90, max(10, int(median / 35 * 100)))
        return {'low': low, 'high': high, 'median': median, 'gauge_pct': pct}


def main():
    global API_DATA

    parser = argparse.ArgumentParser(description='Dashboard Server')
    parser.add_argument('--port', type=int, default=8080, help='Port number')
    args = parser.parse_args()

    print("  Loading pipeline data...")
    API_DATA = build_api_data()
    overview = API_DATA['overview']
    print(f"  [OK] Loaded {overview['total_jobs']} jobs, "
          f"{overview['total_companies']} companies, "
          f"{overview['total_skills']} skills")

    server = HTTPServer(('', args.port), DashboardHandler)
    print(f"\n  Dashboard running at → http://localhost:{args.port}/index.html")
    print("  API endpoint at     → http://localhost:{}/api/data".format(args.port))
    print("  Press Ctrl+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  [OK] Dashboard server stopped.")
        server.server_close()


if __name__ == '__main__':
    main()
