"""
Resume Matcher
==============
Match your resume/skills to job listings and find best fits.

Usage:
    python resume_matcher.py --profile           # Create/edit your profile
    python resume_matcher.py --match             # Find matching jobs
    python resume_matcher.py --gaps              # Show skill gaps
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
from typing import List, Dict, Tuple
from collections import Counter
import argparse

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / 'config'
PROFILE_FILE = CONFIG_DIR / 'user_profile.json'
DATA_DIR = PROJECT_ROOT / 'data' / 'raw'
REPORTS_DIR = PROJECT_ROOT / 'outputs' / 'reports'

# Ensure directories exist
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


class UserProfile:
    """User's professional profile for job matching."""
    
    def __init__(self):
        self.name = ""
        self.title = ""
        self.experience_years = 0
        self.skills = []
        self.preferred_locations = []
        self.preferred_companies = []
        self.min_salary_lpa = 0
        self.job_types = []  # remote, hybrid, onsite
        self.industries = []
        
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'title': self.title,
            'experience_years': self.experience_years,
            'skills': self.skills,
            'preferred_locations': self.preferred_locations,
            'preferred_companies': self.preferred_companies,
            'min_salary_lpa': self.min_salary_lpa,
            'job_types': self.job_types,
            'industries': self.industries,
            'updated_at': datetime.now().isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserProfile':
        profile = cls()
        profile.name = data.get('name', '')
        profile.title = data.get('title', '')
        profile.experience_years = data.get('experience_years', 0)
        profile.skills = data.get('skills', [])
        profile.preferred_locations = data.get('preferred_locations', [])
        profile.preferred_companies = data.get('preferred_companies', [])
        profile.min_salary_lpa = data.get('min_salary_lpa', 0)
        profile.job_types = data.get('job_types', [])
        profile.industries = data.get('industries', [])
        return profile
    
    def save(self):
        """Save profile to file."""
        with open(PROFILE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"[OK] Profile saved to {PROFILE_FILE}")
    
    @classmethod
    def load(cls) -> 'UserProfile':
        """Load profile from file."""
        if PROFILE_FILE.exists():
            with open(PROFILE_FILE, 'r', encoding='utf-8') as f:
                return cls.from_dict(json.load(f))
        return cls()


class ResumeMatcher:
    """Match user profile to job listings."""
    
    # Skill categories for better matching
    SKILL_CATEGORIES = {
        'programming': ['python', 'java', 'javascript', 'c++', 'c#', 'go', 'rust', 'scala', 'ruby', 'php'],
        'frontend': ['react', 'angular', 'vue', 'html', 'css', 'typescript', 'jquery', 'bootstrap'],
        'backend': ['node', 'django', 'flask', 'spring', 'fastapi', 'express', '.net', 'rails'],
        'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'oracle'],
        'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins'],
        'data': ['pandas', 'numpy', 'spark', 'hadoop', 'tableau', 'power bi', 'excel'],
        'ml_ai': ['machine learning', 'deep learning', 'tensorflow', 'pytorch', 'nlp', 'computer vision'],
        'devops': ['ci/cd', 'git', 'linux', 'ansible', 'puppet', 'monitoring', 'grafana']
    }
    
    def __init__(self, profile: UserProfile = None):
        self.profile = profile or UserProfile.load()
        self.jobs = []
        self.matches = []
    
    def load_jobs(self) -> List[Dict]:
        """Load jobs from data files."""
        # Try CSV first
        try:
            import pandas as pd
            csv_files = list(DATA_DIR.glob('jobs_*.csv'))
            if csv_files:
                latest = max(csv_files, key=lambda f: f.stat().st_mtime)
                df = pd.read_csv(latest)
                self.jobs = df.to_dict('records')
                print(f"[i] Loaded {len(self.jobs)} jobs from {latest.name}")
                return self.jobs
        except ImportError:
            pass
        
        # Try JSON
        json_files = list(DATA_DIR.glob('jobs_*.json'))
        if json_files:
            latest = max(json_files, key=lambda f: f.stat().st_mtime)
            with open(latest, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.jobs = data if isinstance(data, list) else data.get('jobs', [])
                print(f"[i] Loaded {len(self.jobs)} jobs from {latest.name}")
                return self.jobs
        
        print("[X] No job data found")
        return []
    
    def calculate_match_score(self, job: Dict) -> Tuple[float, Dict]:
        """
        Calculate match score between profile and job.
        Returns (score, breakdown)
        """
        score = 0
        max_score = 0
        breakdown = {}
        
        title = str(job.get('title', '')).lower()
        company = str(job.get('company', '')).lower()
        location = str(job.get('location', '')).lower()
        description = str(job.get('description', '')).lower()
        
        # 1. Skills match (40% weight)
        max_score += 40
        if self.profile.skills:
            matched_skills = []
            for skill in self.profile.skills:
                skill_lower = skill.lower()
                if skill_lower in description or skill_lower in title:
                    matched_skills.append(skill)
            
            skill_match_pct = len(matched_skills) / len(self.profile.skills) if self.profile.skills else 0
            skill_score = skill_match_pct * 40
            score += skill_score
            breakdown['skills'] = {
                'score': round(skill_score, 1),
                'matched': matched_skills,
                'total': len(self.profile.skills)
            }
        
        # 2. Title match (25% weight)
        max_score += 25
        if self.profile.title:
            title_words = self.profile.title.lower().split()
            matched_words = sum(1 for word in title_words if word in title)
            title_match_pct = matched_words / len(title_words) if title_words else 0
            title_score = title_match_pct * 25
            score += title_score
            breakdown['title'] = {
                'score': round(title_score, 1),
                'match_percent': round(title_match_pct * 100, 1)
            }
        
        # 3. Location match (15% weight)
        max_score += 15
        if self.profile.preferred_locations:
            location_match = any(loc.lower() in location for loc in self.profile.preferred_locations)
            if location_match:
                score += 15
            breakdown['location'] = {
                'score': 15 if location_match else 0,
                'matched': location_match
            }
        
        # 4. Company preference (10% weight)
        max_score += 10
        if self.profile.preferred_companies:
            company_match = any(comp.lower() in company for comp in self.profile.preferred_companies)
            if company_match:
                score += 10
            breakdown['company'] = {
                'score': 10 if company_match else 0,
                'matched': company_match
            }
        
        # 5. Job type match (10% weight)
        max_score += 10
        if self.profile.job_types:
            job_type_match = any(jt.lower() in description for jt in self.profile.job_types)
            if job_type_match:
                score += 10
            breakdown['job_type'] = {
                'score': 10 if job_type_match else 0,
                'matched': job_type_match
            }
        
        # Normalize score to 100
        final_score = (score / max_score * 100) if max_score > 0 else 0
        breakdown['total_score'] = round(final_score, 1)
        
        return final_score, breakdown
    
    def find_matches(self, min_score: float = 50, limit: int = 20) -> List[Dict]:
        """Find jobs matching the profile."""
        if not self.jobs:
            self.load_jobs()
        
        if not self.jobs:
            return []
        
        print(f"\n[i] Matching profile against {len(self.jobs)} jobs...")
        
        matches = []
        for job in self.jobs:
            score, breakdown = self.calculate_match_score(job)
            if score >= min_score:
                matches.append({
                    'job': job,
                    'score': score,
                    'breakdown': breakdown
                })
        
        # Sort by score descending
        matches.sort(key=lambda x: x['score'], reverse=True)
        self.matches = matches[:limit]
        
        return self.matches
    
    def analyze_skill_gaps(self) -> Dict:
        """Analyze skill gaps based on job market demand."""
        if not self.jobs:
            self.load_jobs()
        
        # Count skills in all jobs
        market_skills = Counter()
        for job in self.jobs:
            desc = str(job.get('description', '')).lower()
            title = str(job.get('title', '')).lower()
            text = desc + ' ' + title
            
            for category, skills in self.SKILL_CATEGORIES.items():
                for skill in skills:
                    if skill in text:
                        market_skills[skill] += 1
        
        # User's skills (lowercase)
        user_skills = set(s.lower() for s in self.profile.skills)
        
        # Find gaps
        top_market_skills = [skill for skill, _ in market_skills.most_common(30)]
        
        skill_gaps = []
        skills_have = []
        
        for skill in top_market_skills:
            demand = market_skills[skill]
            if skill in user_skills or any(skill in us for us in user_skills):
                skills_have.append({'skill': skill, 'demand': demand})
            else:
                skill_gaps.append({'skill': skill, 'demand': demand})
        
        # Categorize gaps
        categorized_gaps = {}
        for gap in skill_gaps:
            for category, skills in self.SKILL_CATEGORIES.items():
                if gap['skill'] in skills:
                    if category not in categorized_gaps:
                        categorized_gaps[category] = []
                    categorized_gaps[category].append(gap)
                    break
        
        return {
            'skills_you_have': skills_have[:15],
            'skills_to_learn': skill_gaps[:15],
            'categorized_gaps': categorized_gaps,
            'market_top_skills': top_market_skills[:20],
            'your_skill_count': len(user_skills),
            'coverage_percent': round(len(skills_have) / len(top_market_skills) * 100, 1) if top_market_skills else 0
        }
    
    def display_matches(self):
        """Display matching jobs."""
        if not self.matches:
            print("\n[i] No matches found. Try lowering the minimum score.")
            return
        
        print("\n" + "=" * 70)
        print(f"TOP {len(self.matches)} JOB MATCHES FOR: {self.profile.name or 'You'}")
        print("=" * 70)
        
        for i, match in enumerate(self.matches, 1):
            job = match['job']
            score = match['score']
            breakdown = match['breakdown']
            
            # Score bar
            bar_len = int(score / 5)
            bar = "[" + "#" * bar_len + "-" * (20 - bar_len) + "]"
            
            print(f"\n[{i}] {job.get('title', 'N/A')} - {score:.0f}% Match {bar}")
            print(f"    Company:  {job.get('company', 'N/A')}")
            print(f"    Location: {job.get('location', 'N/A')}")
            
            # Show matched skills
            if 'skills' in breakdown and breakdown['skills']['matched']:
                skills_str = ', '.join(breakdown['skills']['matched'][:5])
                print(f"    Skills:   {skills_str}")
            
            if job.get('url'):
                print(f"    URL:      {job.get('url')}")
        
        print("\n" + "=" * 70)
    
    def display_skill_gaps(self, gaps: Dict):
        """Display skill gap analysis."""
        print("\n" + "=" * 70)
        print("SKILL GAP ANALYSIS")
        print("=" * 70)
        
        print(f"\nYour Skills: {gaps['your_skill_count']}")
        print(f"Market Coverage: {gaps['coverage_percent']}%")
        
        print("\n[+] Skills You Have (In Demand):")
        for item in gaps['skills_you_have'][:10]:
            print(f"    [OK] {item['skill'].upper()} - {item['demand']} jobs")
        
        print("\n[-] Skills to Learn (High Demand):")
        for item in gaps['skills_to_learn'][:10]:
            print(f"    [!!] {item['skill'].upper()} - {item['demand']} jobs")
        
        print("\n[i] Gaps by Category:")
        for category, skills in gaps['categorized_gaps'].items():
            if skills:
                skill_names = [s['skill'] for s in skills[:3]]
                print(f"    {category.upper()}: {', '.join(skill_names)}")
        
        print("\n" + "=" * 70)
    
    def save_matches_report(self):
        """Save matches to report file."""
        if not self.matches:
            return
        
        report_file = REPORTS_DIR / f"job_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        output = {
            'profile': self.profile.to_dict(),
            'generated_at': datetime.now().isoformat(),
            'total_matches': len(self.matches),
            'matches': [
                {
                    'rank': i + 1,
                    'score': m['score'],
                    'title': m['job'].get('title'),
                    'company': m['job'].get('company'),
                    'location': m['job'].get('location'),
                    'url': m['job'].get('url'),
                    'matched_skills': m['breakdown'].get('skills', {}).get('matched', [])
                }
                for i, m in enumerate(self.matches)
            ]
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n[OK] Matches saved to: {report_file}")


def create_profile_interactive() -> UserProfile:
    """Create user profile interactively."""
    print("\n" + "=" * 60)
    print("CREATE YOUR PROFILE")
    print("=" * 60)
    
    profile = UserProfile()
    
    profile.name = input("\nYour name: ").strip()
    profile.title = input("Current/Desired job title: ").strip()
    
    exp = input("Years of experience: ").strip()
    profile.experience_years = int(exp) if exp.isdigit() else 0
    
    skills = input("Your skills (comma-separated): ").strip()
    profile.skills = [s.strip() for s in skills.split(',') if s.strip()]
    
    locations = input("Preferred locations (comma-separated): ").strip()
    profile.preferred_locations = [l.strip() for l in locations.split(',') if l.strip()]
    
    companies = input("Preferred companies (comma-separated, optional): ").strip()
    profile.preferred_companies = [c.strip() for c in companies.split(',') if c.strip()]
    
    salary = input("Minimum salary (LPA, optional): ").strip()
    profile.min_salary_lpa = float(salary) if salary else 0
    
    job_types = input("Job types (remote/hybrid/onsite, comma-separated): ").strip()
    profile.job_types = [j.strip() for j in job_types.split(',') if j.strip()]
    
    profile.save()
    return profile


def main():
    parser = argparse.ArgumentParser(description='Resume Matcher - Find jobs that match your profile')
    parser.add_argument('--profile', action='store_true', help='Create/edit your profile')
    parser.add_argument('--match', action='store_true', help='Find matching jobs')
    parser.add_argument('--gaps', action='store_true', help='Analyze skill gaps')
    parser.add_argument('--min-score', type=int, default=40, help='Minimum match score (default: 40)')
    parser.add_argument('--limit', type=int, default=15, help='Maximum results (default: 15)')
    
    args = parser.parse_args()
    
    if args.profile:
        create_profile_interactive()
    
    elif args.match:
        profile = UserProfile.load()
        if not profile.skills:
            print("[X] No profile found. Create one first with --profile")
            return
        
        matcher = ResumeMatcher(profile)
        matcher.find_matches(min_score=args.min_score, limit=args.limit)
        matcher.display_matches()
        matcher.save_matches_report()
    
    elif args.gaps:
        profile = UserProfile.load()
        if not profile.skills:
            print("[X] No profile found. Create one first with --profile")
            return
        
        matcher = ResumeMatcher(profile)
        gaps = matcher.analyze_skill_gaps()
        matcher.display_skill_gaps(gaps)
    
    else:
        parser.print_help()
        print("\n" + "=" * 60)
        print("EXAMPLES:")
        print("=" * 60)
        print("  python resume_matcher.py --profile      # Create your profile")
        print("  python resume_matcher.py --match        # Find matching jobs")
        print("  python resume_matcher.py --gaps         # Analyze skill gaps")
        print("  python resume_matcher.py --match --min-score 60 --limit 10")


if __name__ == "__main__":
    main()
