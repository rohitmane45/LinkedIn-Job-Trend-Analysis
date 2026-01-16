"""
Salary Predictor
================
Predict salary range based on job title, skills, location, and experience.

Usage:
    python salary_predictor.py --predict "Python Developer" --location "Bangalore" --exp 3
    python salary_predictor.py --analyze                    # Analyze salary data
    python salary_predictor.py --train                      # Train/update model
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
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import argparse

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data' / 'raw'
MODEL_FILE = PROJECT_ROOT / 'config' / 'salary_model.json'
REPORTS_DIR = PROJECT_ROOT / 'outputs' / 'reports'

# Ensure directories exist
MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)


class SalaryPredictor:
    """Predict salary based on job attributes."""
    
    # Base salaries by role level (in LPA)
    BASE_SALARIES = {
        'intern': (2, 4),
        'fresher': (3, 6),
        'junior': (4, 8),
        'mid': (8, 15),
        'senior': (15, 30),
        'lead': (20, 40),
        'manager': (25, 50),
        'director': (40, 80),
        'vp': (60, 120)
    }
    
    # Location multipliers
    LOCATION_MULTIPLIERS = {
        'bangalore': 1.15,
        'bengaluru': 1.15,
        'mumbai': 1.10,
        'delhi': 1.05,
        'ncr': 1.05,
        'gurgaon': 1.08,
        'gurugram': 1.08,
        'noida': 1.02,
        'hyderabad': 1.05,
        'pune': 1.00,
        'chennai': 0.98,
        'kolkata': 0.92,
        'remote': 1.05,
        'usa': 5.0,
        'uk': 3.5,
        'singapore': 4.0,
        'dubai': 3.0
    }
    
    # Skill premium (additional % on top)
    SKILL_PREMIUMS = {
        'machine learning': 15,
        'deep learning': 18,
        'ai': 15,
        'kubernetes': 12,
        'aws': 10,
        'azure': 10,
        'gcp': 10,
        'python': 5,
        'java': 5,
        'golang': 12,
        'rust': 15,
        'scala': 10,
        'react': 8,
        'node': 7,
        'blockchain': 20,
        'devops': 10,
        'data science': 12,
        'security': 12,
        'cloud': 10
    }
    
    # Role keywords to level mapping
    ROLE_LEVELS = {
        'intern': ['intern', 'trainee', 'apprentice'],
        'fresher': ['fresher', 'entry', 'graduate', 'associate'],
        'junior': ['junior', 'jr', 'i ', ' 1'],
        'mid': ['mid', 'intermediate', 'ii ', ' 2', ' 3'],
        'senior': ['senior', 'sr', 'iii ', ' 4', ' 5'],
        'lead': ['lead', 'principal', 'staff', 'tech lead'],
        'manager': ['manager', 'engineering manager'],
        'director': ['director', 'head of'],
        'vp': ['vp', 'vice president', 'cto', 'cio']
    }
    
    def __init__(self):
        self.model_data = self._load_model()
        self.jobs_analyzed = 0
    
    def _load_model(self) -> Dict:
        """Load trained model data."""
        if MODEL_FILE.exists():
            with open(MODEL_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'salary_samples': [],
            'role_averages': {},
            'location_averages': {},
            'trained_at': None
        }
    
    def _save_model(self):
        """Save model data."""
        with open(MODEL_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.model_data, f, indent=2)
        print(f"[OK] Model saved to {MODEL_FILE}")
    
    def _detect_level(self, title: str) -> str:
        """Detect job level from title."""
        title_lower = title.lower()
        
        for level, keywords in self.ROLE_LEVELS.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return level
        
        # Default based on common patterns
        if any(word in title_lower for word in ['architect', 'principal']):
            return 'lead'
        
        return 'mid'  # Default to mid-level
    
    def _get_location_multiplier(self, location: str) -> float:
        """Get salary multiplier for location."""
        location_lower = location.lower()
        
        for loc, mult in self.LOCATION_MULTIPLIERS.items():
            if loc in location_lower:
                return mult
        
        return 1.0  # Default multiplier
    
    def _calculate_skill_premium(self, skills: List[str]) -> float:
        """Calculate total skill premium percentage."""
        total_premium = 0
        
        for skill in skills:
            skill_lower = skill.lower()
            for premium_skill, premium in self.SKILL_PREMIUMS.items():
                if premium_skill in skill_lower:
                    total_premium += premium
                    break
        
        # Cap premium at 50%
        return min(total_premium, 50)
    
    def _extract_salary_from_text(self, text: str) -> Optional[Tuple[float, float]]:
        """Extract salary range from text."""
        if not text:
            return None
        
        text = text.lower()
        
        # Patterns for Indian salaries (LPA)
        patterns = [
            r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*(?:lpa|lakh|lac)',
            r'(\d+(?:\.\d+)?)\s*(?:lpa|lakh|lac)\s*-\s*(\d+(?:\.\d+)?)',
            r'(?:rs\.?|inr|₹)\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*(?:lpa|lakh|lac)',
            r'(\d+(?:\.\d+)?)\s*(?:to|–)\s*(\d+(?:\.\d+)?)\s*(?:lpa|lakh|lac)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                low = float(match.group(1))
                high = float(match.group(2))
                return (low, high)
        
        # Single value
        single_pattern = r'(\d+(?:\.\d+)?)\s*(?:lpa|lakh|lac)'
        match = re.search(single_pattern, text)
        if match:
            value = float(match.group(1))
            return (value * 0.9, value * 1.1)
        
        return None
    
    def predict(self, title: str, location: str = "", skills: List[str] = None, 
                experience_years: int = 0) -> Dict:
        """
        Predict salary for given job attributes.
        
        Returns dict with min, max, median salary and confidence.
        """
        skills = skills or []
        
        # Detect job level
        level = self._detect_level(title)
        
        # Adjust level by experience
        if experience_years:
            if experience_years <= 1:
                level = 'fresher'
            elif experience_years <= 3:
                level = 'junior'
            elif experience_years <= 6:
                level = 'mid'
            elif experience_years <= 10:
                level = 'senior'
            else:
                level = 'lead'
        
        # Get base salary range
        base_min, base_max = self.BASE_SALARIES.get(level, (8, 15))
        
        # Apply location multiplier
        loc_mult = self._get_location_multiplier(location)
        
        # Apply skill premium
        skill_premium = self._calculate_skill_premium(skills)
        skill_mult = 1 + (skill_premium / 100)
        
        # Calculate final range
        final_min = base_min * loc_mult * skill_mult
        final_max = base_max * loc_mult * skill_mult
        final_median = (final_min + final_max) / 2
        
        # Check against trained data if available
        confidence = 'medium'
        if self.model_data.get('role_averages'):
            # Adjust based on historical data
            role_key = title.lower().split()[0] if title else ''
            if role_key in self.model_data['role_averages']:
                historical = self.model_data['role_averages'][role_key]
                # Blend prediction with historical
                final_min = (final_min + historical.get('min', final_min)) / 2
                final_max = (final_max + historical.get('max', final_max)) / 2
                confidence = 'high'
        
        return {
            'title': title,
            'level': level,
            'location': location,
            'location_multiplier': loc_mult,
            'skill_premium_percent': skill_premium,
            'salary_range': {
                'min': round(final_min, 1),
                'max': round(final_max, 1),
                'median': round(final_median, 1)
            },
            'confidence': confidence,
            'currency': 'INR (LPA)'
        }
    
    def train_from_jobs(self):
        """Train model from job data with salaries."""
        # Load jobs
        jobs = []
        try:
            import pandas as pd
            csv_files = list(DATA_DIR.glob('jobs_*.csv'))
            if csv_files:
                latest = max(csv_files, key=lambda f: f.stat().st_mtime)
                df = pd.read_csv(latest)
                jobs = df.to_dict('records')
        except:
            pass
        
        if not jobs:
            json_files = list(DATA_DIR.glob('jobs_*.json'))
            if json_files:
                latest = max(json_files, key=lambda f: f.stat().st_mtime)
                with open(latest, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    jobs = data if isinstance(data, list) else data.get('jobs', [])
        
        if not jobs:
            print("[X] No job data found for training")
            return
        
        print(f"[i] Analyzing {len(jobs)} jobs for salary data...")
        
        # Extract salaries
        role_salaries = defaultdict(list)
        location_salaries = defaultdict(list)
        samples = []
        
        for job in jobs:
            # Try to extract salary
            salary_text = job.get('salary', '') or job.get('description', '')
            salary_range = self._extract_salary_from_text(str(salary_text))
            
            if salary_range:
                title = job.get('title', '')
                location = job.get('location', '')
                
                # Extract first word of title as role
                role = title.lower().split()[0] if title else 'unknown'
                
                # Store sample
                samples.append({
                    'title': title,
                    'location': location,
                    'salary_min': salary_range[0],
                    'salary_max': salary_range[1]
                })
                
                avg_salary = (salary_range[0] + salary_range[1]) / 2
                role_salaries[role].append(avg_salary)
                
                for loc in self.LOCATION_MULTIPLIERS.keys():
                    if loc in location.lower():
                        location_salaries[loc].append(avg_salary)
                        break
        
        # Calculate averages
        role_averages = {}
        for role, salaries in role_salaries.items():
            if salaries:
                role_averages[role] = {
                    'min': min(salaries),
                    'max': max(salaries),
                    'avg': sum(salaries) / len(salaries),
                    'count': len(salaries)
                }
        
        location_averages = {}
        for loc, salaries in location_salaries.items():
            if salaries:
                location_averages[loc] = {
                    'avg': sum(salaries) / len(salaries),
                    'count': len(salaries)
                }
        
        # Update model
        self.model_data = {
            'salary_samples': samples[:100],  # Keep last 100 samples
            'role_averages': role_averages,
            'location_averages': location_averages,
            'trained_at': datetime.now().isoformat(),
            'jobs_analyzed': len(jobs),
            'salaries_found': len(samples)
        }
        
        self._save_model()
        
        print(f"[OK] Model trained on {len(samples)} salary samples")
        return self.model_data
    
    def analyze_market(self) -> Dict:
        """Analyze salary market data."""
        if not self.model_data.get('role_averages'):
            print("[!] No trained data. Running training first...")
            self.train_from_jobs()
        
        analysis = {
            'trained_at': self.model_data.get('trained_at'),
            'samples_count': len(self.model_data.get('salary_samples', [])),
            'top_paying_roles': [],
            'location_comparison': [],
            'overall_range': {}
        }
        
        # Top paying roles
        role_avgs = self.model_data.get('role_averages', {})
        sorted_roles = sorted(role_avgs.items(), key=lambda x: x[1].get('avg', 0), reverse=True)
        analysis['top_paying_roles'] = [
            {'role': role, **data} for role, data in sorted_roles[:10]
        ]
        
        # Location comparison
        loc_avgs = self.model_data.get('location_averages', {})
        sorted_locs = sorted(loc_avgs.items(), key=lambda x: x[1].get('avg', 0), reverse=True)
        analysis['location_comparison'] = [
            {'location': loc, **data} for loc, data in sorted_locs
        ]
        
        # Overall range
        if role_avgs:
            all_avgs = [d['avg'] for d in role_avgs.values()]
            analysis['overall_range'] = {
                'min': round(min(all_avgs), 1),
                'max': round(max(all_avgs), 1),
                'median': round(sorted(all_avgs)[len(all_avgs)//2], 1)
            }
        
        return analysis


def main():
    parser = argparse.ArgumentParser(description='Salary Predictor')
    parser.add_argument('--predict', type=str, metavar='TITLE', help='Job title to predict salary for')
    parser.add_argument('--location', type=str, default='', help='Job location')
    parser.add_argument('--skills', type=str, default='', help='Skills (comma-separated)')
    parser.add_argument('--exp', type=int, default=0, help='Years of experience')
    parser.add_argument('--train', action='store_true', help='Train model from job data')
    parser.add_argument('--analyze', action='store_true', help='Analyze salary market')
    
    args = parser.parse_args()
    
    predictor = SalaryPredictor()
    
    if args.train:
        predictor.train_from_jobs()
    
    elif args.analyze:
        analysis = predictor.analyze_market()
        
        print("\n" + "=" * 60)
        print("SALARY MARKET ANALYSIS")
        print("=" * 60)
        
        print(f"\nData from: {analysis.get('trained_at', 'N/A')[:10]}")
        print(f"Salary samples: {analysis.get('samples_count', 0)}")
        
        if analysis.get('overall_range'):
            r = analysis['overall_range']
            print(f"\nOverall Range: {r['min']} - {r['max']} LPA (Median: {r['median']})")
        
        print("\nTop Paying Roles:")
        for item in analysis.get('top_paying_roles', [])[:8]:
            print(f"  {item['role'].upper()}: {item['avg']:.1f} LPA (n={item['count']})")
        
        print("\nBy Location:")
        for item in analysis.get('location_comparison', [])[:6]:
            print(f"  {item['location'].upper()}: {item['avg']:.1f} LPA avg")
        
        print("\n" + "=" * 60)
    
    elif args.predict:
        skills = [s.strip() for s in args.skills.split(',') if s.strip()]
        
        result = predictor.predict(
            title=args.predict,
            location=args.location,
            skills=skills,
            experience_years=args.exp
        )
        
        print("\n" + "=" * 60)
        print("SALARY PREDICTION")
        print("=" * 60)
        print(f"\nJob Title: {result['title']}")
        print(f"Level: {result['level'].upper()}")
        print(f"Location: {result['location'] or 'Not specified'}")
        print(f"Location Multiplier: {result['location_multiplier']}x")
        print(f"Skill Premium: +{result['skill_premium_percent']}%")
        print(f"\nPredicted Salary Range:")
        salary = result['salary_range']
        print(f"  Min:    {salary['min']} LPA")
        print(f"  Max:    {salary['max']} LPA")
        print(f"  Median: {salary['median']} LPA")
        print(f"\nConfidence: {result['confidence'].upper()}")
        print("=" * 60)
    
    else:
        parser.print_help()
        print("\n" + "=" * 60)
        print("EXAMPLES:")
        print("=" * 60)
        print('  python salary_predictor.py --predict "Python Developer" --location Bangalore --exp 3')
        print('  python salary_predictor.py --predict "Senior Data Scientist" --skills "python,ml,aws"')
        print('  python salary_predictor.py --train')
        print('  python salary_predictor.py --analyze')


if __name__ == "__main__":
    main()
