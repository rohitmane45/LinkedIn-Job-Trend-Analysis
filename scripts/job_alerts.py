"""
Job Alerts System
=================
Get notified when jobs match your criteria.

Usage:
    python job_alerts.py --check                    # Check for matching jobs
    python job_alerts.py --add-alert "Python Developer in Bangalore"
    python job_alerts.py --list-alerts              # Show all alerts
    python job_alerts.py --test                     # Test with sample data
"""

import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import argparse

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data' / 'raw'
ALERTS_DIR = PROJECT_ROOT / 'config' / 'alerts'
ALERTS_FILE = ALERTS_DIR / 'job_alerts.json'
MATCHES_FILE = PROJECT_ROOT / 'outputs' / 'reports' / 'alert_matches.json'

# Ensure directories exist
ALERTS_DIR.mkdir(parents=True, exist_ok=True)


class JobAlert:
    """Represents a single job alert with matching criteria."""
    
    def __init__(self, name: str, criteria: Dict):
        self.name = name
        self.criteria = criteria
        self.created_at = datetime.now().isoformat()
        self.last_checked = None
        self.match_count = 0
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'criteria': self.criteria,
            'created_at': self.created_at,
            'last_checked': self.last_checked,
            'match_count': self.match_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'JobAlert':
        alert = cls(data['name'], data['criteria'])
        alert.created_at = data.get('created_at', datetime.now().isoformat())
        alert.last_checked = data.get('last_checked')
        alert.match_count = data.get('match_count', 0)
        return alert


class JobAlertManager:
    """Manage job alerts and check for matches."""
    
    def __init__(self):
        self.alerts: List[JobAlert] = []
        self.load_alerts()
    
    def load_alerts(self):
        """Load alerts from file."""
        if ALERTS_FILE.exists():
            with open(ALERTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.alerts = [JobAlert.from_dict(a) for a in data.get('alerts', [])]
        print(f"[i] Loaded {len(self.alerts)} existing alerts")
    
    def save_alerts(self):
        """Save alerts to file."""
        data = {'alerts': [a.to_dict() for a in self.alerts]}
        with open(ALERTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[OK] Saved {len(self.alerts)} alerts")
    
    def add_alert(self, name: str, criteria: Dict) -> JobAlert:
        """Add a new job alert."""
        alert = JobAlert(name, criteria)
        self.alerts.append(alert)
        self.save_alerts()
        print(f"[+] Added alert: {name}")
        return alert
    
    def remove_alert(self, name: str) -> bool:
        """Remove an alert by name."""
        for i, alert in enumerate(self.alerts):
            if alert.name.lower() == name.lower():
                del self.alerts[i]
                self.save_alerts()
                print(f"[-] Removed alert: {name}")
                return True
        print(f"[X] Alert not found: {name}")
        return False
    
    def list_alerts(self):
        """Display all alerts."""
        print("\n" + "="*60)
        print("JOB ALERTS")
        print("="*60)
        
        if not self.alerts:
            print("\n[i] No alerts configured.")
            print("    Add one with: python job_alerts.py --add-alert \"name\"")
            return
        
        for i, alert in enumerate(self.alerts, 1):
            print(f"\n[{i}] {alert.name}")
            print(f"    Created: {alert.created_at[:10]}")
            print(f"    Matches: {alert.match_count}")
            print(f"    Criteria:")
            for key, value in alert.criteria.items():
                print(f"      - {key}: {value}")
        
        print("\n" + "="*60)
    
    def create_alert_interactive(self) -> JobAlert:
        """Create an alert interactively."""
        print("\n" + "="*60)
        print("CREATE NEW JOB ALERT")
        print("="*60)
        
        name = input("\nAlert name: ").strip()
        if not name:
            print("[X] Name cannot be empty")
            return None
        
        criteria = {}
        
        print("\nEnter criteria (leave blank to skip):\n")
        
        # Keywords in title
        keywords = input("Job title keywords (comma-separated): ").strip()
        if keywords:
            criteria['title_keywords'] = [k.strip().lower() for k in keywords.split(',')]
        
        # Skills required
        skills = input("Required skills (comma-separated): ").strip()
        if skills:
            criteria['skills'] = [s.strip().lower() for s in skills.split(',')]
        
        # Location
        location = input("Location (city name): ").strip()
        if location:
            criteria['location'] = location.lower()
        
        # Company
        company = input("Company name (partial match): ").strip()
        if company:
            criteria['company'] = company.lower()
        
        # Minimum salary (LPA)
        salary = input("Minimum salary (LPA, e.g., 10): ").strip()
        if salary:
            try:
                criteria['min_salary_lpa'] = float(salary)
            except ValueError:
                print("[!] Invalid salary, skipping")
        
        # Job type
        job_type = input("Job type (remote/hybrid/onsite): ").strip()
        if job_type:
            criteria['job_type'] = job_type.lower()
        
        # Experience level
        exp = input("Experience level (entry/mid/senior): ").strip()
        if exp:
            criteria['experience'] = exp.lower()
        
        if not criteria:
            print("[X] No criteria specified")
            return None
        
        return self.add_alert(name, criteria)
    
    def _match_job(self, job: Dict, criteria: Dict) -> tuple:
        """
        Check if a job matches the given criteria.
        Returns (is_match, match_reasons)
        """
        match_reasons = []
        is_match = True
        
        # Title keywords
        if 'title_keywords' in criteria:
            title = job.get('title', '').lower()
            matched_keywords = [k for k in criteria['title_keywords'] if k in title]
            if matched_keywords:
                match_reasons.append(f"Title contains: {', '.join(matched_keywords)}")
            else:
                is_match = False
        
        # Skills
        if 'skills' in criteria and is_match:
            description = job.get('description', '').lower()
            matched_skills = [s for s in criteria['skills'] if s in description]
            if matched_skills:
                match_reasons.append(f"Skills found: {', '.join(matched_skills)}")
            else:
                is_match = False
        
        # Location
        if 'location' in criteria and is_match:
            location = job.get('location', '').lower()
            if criteria['location'] in location:
                match_reasons.append(f"Location: {job.get('location')}")
            else:
                is_match = False
        
        # Company
        if 'company' in criteria and is_match:
            company = job.get('company', '').lower()
            if criteria['company'] in company:
                match_reasons.append(f"Company: {job.get('company')}")
            else:
                is_match = False
        
        # Job type
        if 'job_type' in criteria and is_match:
            description = job.get('description', '').lower()
            job_type = job.get('job_type', '').lower()
            if criteria['job_type'] in description or criteria['job_type'] in job_type:
                match_reasons.append(f"Job type: {criteria['job_type']}")
            else:
                is_match = False
        
        # Salary
        if 'min_salary_lpa' in criteria and is_match:
            salary_text = job.get('salary', '') or job.get('description', '')
            salary_match = self._extract_salary_lpa(salary_text)
            if salary_match and salary_match >= criteria['min_salary_lpa']:
                match_reasons.append(f"Salary: {salary_match} LPA")
            elif salary_match:
                is_match = False
            # If no salary found, don't disqualify
        
        return is_match, match_reasons
    
    def _extract_salary_lpa(self, text: str) -> Optional[float]:
        """Extract salary in LPA from text."""
        if not text:
            return None
        
        text = text.lower()
        
        # Pattern for LPA/Lakh
        patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:lpa|lakh|lac)',
            r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*(?:lpa|lakh|lac)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # Return highest value if range
                values = [float(g) for g in match.groups() if g]
                return max(values)
        
        return None
    
    def check_alerts(self, jobs: List[Dict] = None) -> Dict:
        """
        Check all alerts against jobs data.
        Returns dict of matches per alert.
        """
        print("\n" + "="*60)
        print("CHECKING JOB ALERTS")
        print("="*60)
        
        if not self.alerts:
            print("\n[i] No alerts configured")
            return {}
        
        # Load jobs if not provided
        if jobs is None:
            jobs = self._load_latest_jobs()
        
        if not jobs:
            print("[X] No job data found")
            return {}
        
        print(f"\n[i] Checking {len(self.alerts)} alerts against {len(jobs)} jobs...\n")
        
        all_matches = {}
        
        for alert in self.alerts:
            matches = []
            
            for job in jobs:
                is_match, reasons = self._match_job(job, alert.criteria)
                if is_match:
                    matches.append({
                        'job': job,
                        'reasons': reasons
                    })
            
            alert.last_checked = datetime.now().isoformat()
            alert.match_count = len(matches)
            all_matches[alert.name] = matches
            
            # Display results
            if matches:
                print(f"[!] ALERT: {alert.name} - {len(matches)} matches found!")
                for i, match in enumerate(matches[:5], 1):  # Show first 5
                    job = match['job']
                    print(f"\n    [{i}] {job.get('title', 'N/A')}")
                    print(f"        Company: {job.get('company', 'N/A')}")
                    print(f"        Location: {job.get('location', 'N/A')}")
                    print(f"        Match: {', '.join(match['reasons'])}")
                
                if len(matches) > 5:
                    print(f"\n    ... and {len(matches) - 5} more matches")
            else:
                print(f"[_] {alert.name} - No matches")
        
        # Save updated alerts and matches
        self.save_alerts()
        self._save_matches(all_matches)
        
        # Summary
        total_matches = sum(len(m) for m in all_matches.values())
        print("\n" + "="*60)
        print(f"SUMMARY: {total_matches} total matches across {len(self.alerts)} alerts")
        print("="*60)
        
        return all_matches
    
    def _load_latest_jobs(self) -> List[Dict]:
        """Load the most recent jobs data."""
        # Try CSV first
        try:
            import pandas as pd
            csv_files = list(DATA_DIR.glob('jobs_*.csv'))
            if csv_files:
                latest = max(csv_files, key=lambda f: f.stat().st_mtime)
                df = pd.read_csv(latest)
                print(f"[i] Loaded {len(df)} jobs from {latest.name}")
                return df.to_dict('records')
        except ImportError:
            pass
        
        # Try JSON
        json_files = list(DATA_DIR.glob('jobs_*.json'))
        if json_files:
            latest = max(json_files, key=lambda f: f.stat().st_mtime)
            with open(latest, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    print(f"[i] Loaded {len(data)} jobs from {latest.name}")
                    return data
                elif 'jobs' in data:
                    print(f"[i] Loaded {len(data['jobs'])} jobs from {latest.name}")
                    return data['jobs']
        
        return []
    
    def _save_matches(self, matches: Dict):
        """Save matches to file."""
        MATCHES_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        output = {
            'checked_at': datetime.now().isoformat(),
            'alerts': {}
        }
        
        for alert_name, alert_matches in matches.items():
            output['alerts'][alert_name] = {
                'count': len(alert_matches),
                'jobs': [
                    {
                        'title': m['job'].get('title'),
                        'company': m['job'].get('company'),
                        'location': m['job'].get('location'),
                        'reasons': m['reasons']
                    }
                    for m in alert_matches[:20]  # Save top 20 per alert
                ]
            }
        
        with open(MATCHES_FILE, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n[OK] Matches saved to: {MATCHES_FILE}")


def create_sample_alerts():
    """Create sample alerts for testing."""
    manager = JobAlertManager()
    
    # Sample alerts
    samples = [
        {
            'name': 'Python Developer in Bangalore',
            'criteria': {
                'title_keywords': ['python', 'developer', 'engineer'],
                'location': 'bangalore',
                'skills': ['python', 'django', 'flask']
            }
        },
        {
            'name': 'Remote Data Science Jobs',
            'criteria': {
                'title_keywords': ['data', 'scientist', 'analyst'],
                'skills': ['python', 'sql', 'machine learning'],
                'job_type': 'remote'
            }
        },
        {
            'name': 'High Paying Tech Jobs',
            'criteria': {
                'title_keywords': ['senior', 'lead', 'architect'],
                'min_salary_lpa': 25
            }
        }
    ]
    
    for sample in samples:
        # Check if alert already exists
        exists = any(a.name == sample['name'] for a in manager.alerts)
        if not exists:
            manager.add_alert(sample['name'], sample['criteria'])
    
    print("\n[OK] Sample alerts created!")


def main():
    parser = argparse.ArgumentParser(description='Job Alerts System')
    parser.add_argument('--check', action='store_true', help='Check for matching jobs')
    parser.add_argument('--add-alert', type=str, metavar='NAME', help='Add new alert interactively')
    parser.add_argument('--remove-alert', type=str, metavar='NAME', help='Remove an alert')
    parser.add_argument('--list-alerts', action='store_true', help='List all alerts')
    parser.add_argument('--create-samples', action='store_true', help='Create sample alerts')
    parser.add_argument('--test', action='store_true', help='Test with sample data')
    
    args = parser.parse_args()
    
    manager = JobAlertManager()
    
    if args.list_alerts:
        manager.list_alerts()
    elif args.add_alert:
        manager.create_alert_interactive()
    elif args.remove_alert:
        manager.remove_alert(args.remove_alert)
    elif args.create_samples:
        create_sample_alerts()
    elif args.check or args.test:
        if args.test:
            # Create sample data for testing
            sample_jobs = [
                {
                    'title': 'Senior Python Developer',
                    'company': 'Tech Corp',
                    'location': 'Bangalore, India',
                    'description': 'Looking for Python Django Flask developer. 20-30 LPA. Remote friendly.',
                    'salary': '25 LPA'
                },
                {
                    'title': 'Data Scientist',
                    'company': 'AI Startup',
                    'location': 'Remote',
                    'description': 'ML engineer with Python SQL experience. Work from home.',
                },
                {
                    'title': 'Java Developer',
                    'company': 'Enterprise Inc',
                    'location': 'Mumbai',
                    'description': 'Spring Boot microservices developer needed.'
                }
            ]
            create_sample_alerts()
            manager = JobAlertManager()  # Reload
            manager.check_alerts(sample_jobs)
        else:
            manager.check_alerts()
    else:
        parser.print_help()
        print("\n" + "="*60)
        print("EXAMPLES:")
        print("="*60)
        print("  python job_alerts.py --create-samples   # Create sample alerts")
        print("  python job_alerts.py --list-alerts      # View all alerts")
        print("  python job_alerts.py --add-alert        # Add new alert")
        print("  python job_alerts.py --check            # Check for matches")
        print("  python job_alerts.py --test             # Test with sample data")


if __name__ == "__main__":
    main()
