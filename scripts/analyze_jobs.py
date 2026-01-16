"""
Job Analysis Module
===================
Analyze scraped LinkedIn job data to extract insights.

Usage:
    python analyze_jobs.py --input data/raw/jobs_latest.csv
"""

import sys

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd
import re
from pathlib import Path
from collections import Counter
from datetime import datetime
import json

class JobAnalyzer:
    """Analyze job listings data."""
    
    # Common tech skills to look for
    TECH_SKILLS = [
        'python', 'java', 'javascript', 'sql', 'aws', 'azure', 'docker',
        'kubernetes', 'react', 'node', 'angular', 'vue', 'mongodb', 'postgresql',
        'mysql', 'git', 'linux', 'machine learning', 'deep learning', 'ai',
        'data science', 'tensorflow', 'pytorch', 'spark', 'hadoop', 'tableau',
        'power bi', 'excel', 'r', 'scala', 'go', 'rust', 'c++', 'c#', '.net',
        'django', 'flask', 'fastapi', 'spring', 'microservices', 'api', 'rest',
        'graphql', 'agile', 'scrum', 'jira', 'jenkins', 'ci/cd', 'devops'
    ]
    
    def __init__(self, data_path: str = None):
        self.data_path = Path(data_path) if data_path else None
        self.df = None
        self.analysis_results = {}
        
    def load_data(self, file_path: str = None):
        """Load job data from CSV or JSON file."""
        path = Path(file_path) if file_path else self.data_path
        
        if not path or not path.exists():
            raise FileNotFoundError(f"Data file not found: {path}")
        
        if path.suffix == '.csv':
            self.df = pd.read_csv(path)
        elif path.suffix == '.json':
            self.df = pd.read_json(path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
        
        print(f"✅ Loaded {len(self.df)} job listings from {path.name}")
        return self
    
    def analyze_job_titles(self, top_n: int = 15):
        """Analyze most common job titles."""
        if 'title' not in self.df.columns:
            return {}
        
        title_counts = self.df['title'].value_counts().head(top_n)
        
        self.analysis_results['top_titles'] = {
            'data': title_counts.to_dict(),
            'total_unique': self.df['title'].nunique()
        }
        
        print(f"📊 Found {self.df['title'].nunique()} unique job titles")
        return self.analysis_results['top_titles']
    
    def analyze_companies(self, top_n: int = 15):
        """Analyze top hiring companies."""
        if 'company' not in self.df.columns:
            return {}
        
        company_counts = self.df['company'].value_counts().head(top_n)
        
        self.analysis_results['top_companies'] = {
            'data': company_counts.to_dict(),
            'total_unique': self.df['company'].nunique()
        }
        
        print(f"🏢 Found {self.df['company'].nunique()} unique companies")
        return self.analysis_results['top_companies']
    
    def analyze_locations(self, top_n: int = 15):
        """Analyze job distribution by location."""
        if 'location' not in self.df.columns:
            return {}
        
        location_counts = self.df['location'].value_counts().head(top_n)
        
        self.analysis_results['top_locations'] = {
            'data': location_counts.to_dict(),
            'total_unique': self.df['location'].nunique()
        }
        
        print(f"📍 Found jobs in {self.df['location'].nunique()} locations")
        return self.analysis_results['top_locations']
    
    def extract_skills(self, description_col: str = 'description'):
        """Extract skills from job descriptions."""
        if description_col not in self.df.columns:
            print(f"⚠️ Column '{description_col}' not found")
            return {}
        
        skill_counts = Counter()
        
        for desc in self.df[description_col].dropna():
            desc_lower = desc.lower()
            for skill in self.TECH_SKILLS:
                if skill in desc_lower:
                    skill_counts[skill] += 1
        
        # Sort by count
        sorted_skills = dict(sorted(skill_counts.items(), key=lambda x: x[1], reverse=True))
        
        self.analysis_results['skills'] = {
            'data': sorted_skills,
            'top_10': dict(list(sorted_skills.items())[:10])
        }
        
        print(f"🔧 Extracted {len(sorted_skills)} different skills")
        return self.analysis_results['skills']
    
    def extract_salary_info(self):
        """Extract and analyze salary information."""
        salary_col = None
        for col in ['salary', 'salary_range', 'compensation']:
            if col in self.df.columns:
                salary_col = col
                break
        
        if not salary_col:
            # Try to extract from description
            if 'description' in self.df.columns:
                return self._extract_salary_from_text()
            return {}
        
        salaries = self.df[salary_col].dropna()
        
        self.analysis_results['salary'] = {
            'total_with_salary': len(salaries),
            'percentage_with_salary': round(len(salaries) / len(self.df) * 100, 1)
        }
        
        return self.analysis_results['salary']
    
    def _extract_salary_from_text(self):
        """Extract salary patterns from job descriptions."""
        salary_pattern = r'(?:₹|INR|Rs\.?|USD|\$)\s*[\d,]+(?:\s*-\s*[\d,]+)?(?:\s*(?:LPA|lakh|K|k|per\s*(?:month|annum|year)))?'
        
        salaries_found = []
        for desc in self.df['description'].dropna():
            matches = re.findall(salary_pattern, desc, re.IGNORECASE)
            salaries_found.extend(matches)
        
        self.analysis_results['salary'] = {
            'samples_found': salaries_found[:20],
            'total_mentions': len(salaries_found)
        }
        
        print(f"💰 Found {len(salaries_found)} salary mentions")
        return self.analysis_results['salary']
    
    def analyze_experience_levels(self):
        """Analyze required experience levels."""
        exp_patterns = {
            'Entry Level (0-2 yrs)': r'\b(?:0|1|2)\+?\s*(?:years?|yrs?)|fresher|entry\s*level|junior',
            'Mid Level (3-5 yrs)': r'\b(?:3|4|5)\+?\s*(?:years?|yrs?)|mid\s*level',
            'Senior (6-10 yrs)': r'\b(?:6|7|8|9|10)\+?\s*(?:years?|yrs?)|senior|lead',
            'Expert (10+ yrs)': r'\b(?:1[0-9]|[2-9][0-9])\+?\s*(?:years?|yrs?)|principal|architect|director'
        }
        
        if 'description' not in self.df.columns:
            return {}
        
        exp_counts = {level: 0 for level in exp_patterns}
        
        for desc in self.df['description'].dropna():
            desc_lower = desc.lower()
            for level, pattern in exp_patterns.items():
                if re.search(pattern, desc_lower):
                    exp_counts[level] += 1
                    break  # Count each job once
        
        self.analysis_results['experience_levels'] = exp_counts
        print(f"📈 Analyzed experience requirements")
        return self.analysis_results['experience_levels']
    
    def analyze_job_types(self):
        """Analyze job types (full-time, part-time, remote, etc.)."""
        job_type_patterns = {
            'Full-time': r'full\s*-?\s*time',
            'Part-time': r'part\s*-?\s*time',
            'Contract': r'contract|freelance',
            'Remote': r'remote|work\s*from\s*home|wfh',
            'Hybrid': r'hybrid',
            'On-site': r'on\s*-?\s*site|office'
        }
        
        # Check if job_type column exists
        if 'job_type' in self.df.columns:
            type_counts = self.df['job_type'].value_counts().to_dict()
        elif 'description' in self.df.columns:
            type_counts = {jtype: 0 for jtype in job_type_patterns}
            for desc in self.df['description'].dropna():
                desc_lower = desc.lower()
                for jtype, pattern in job_type_patterns.items():
                    if re.search(pattern, desc_lower):
                        type_counts[jtype] += 1
        else:
            return {}
        
        self.analysis_results['job_types'] = type_counts
        print(f"💼 Analyzed job types")
        return self.analysis_results['job_types']
    
    def run_full_analysis(self):
        """Run all analysis methods."""
        print("\n" + "="*60)
        print("🔍 Running Full Job Analysis")
        print("="*60 + "\n")
        
        self.analyze_job_titles()
        self.analyze_companies()
        self.analyze_locations()
        self.extract_skills()
        self.extract_salary_info()
        self.analyze_experience_levels()
        self.analyze_job_types()
        
        # Add metadata
        self.analysis_results['metadata'] = {
            'total_jobs': len(self.df),
            'analysis_date': datetime.now().isoformat(),
            'source_file': str(self.data_path) if self.data_path else 'unknown'
        }
        
        print("\n✅ Analysis complete!")
        return self.analysis_results
    
    def save_results(self, output_path: str = None):
        """Save analysis results to JSON file."""
        if not output_path:
            output_dir = Path('d:/Linkedin-Job-Analysis/outputs/reports')
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = output_dir / f'analysis_{timestamp}.json'
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {output_path}")
        return output_path


def find_latest_data_file():
    """Find the most recent data file."""
    data_dir = Path('d:/Linkedin-Job-Analysis/data/raw')
    
    if not data_dir.exists():
        return None
    
    files = list(data_dir.glob('jobs_*.csv')) + list(data_dir.glob('jobs_*.json'))
    
    if not files:
        return None
    
    return max(files, key=lambda f: f.stat().st_mtime)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze LinkedIn job data')
    parser.add_argument('--input', '-i', type=str, help='Input data file path')
    parser.add_argument('--output', '-o', type=str, help='Output JSON file path')
    
    args = parser.parse_args()
    
    # Find data file
    data_file = args.input if args.input else find_latest_data_file()
    
    if not data_file:
        print("❌ No data file found. Please specify with --input")
        return
    
    # Run analysis
    analyzer = JobAnalyzer(data_file)
    analyzer.load_data()
    analyzer.run_full_analysis()
    analyzer.save_results(args.output)


if __name__ == "__main__":
    main()
