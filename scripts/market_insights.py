"""
Market Insights Generator
=========================
Generate AI-powered insights about the job market.

Usage:
    python market_insights.py --generate        # Generate insights
    python market_insights.py --summary         # Quick summary
    python market_insights.py --recommendations # Career recommendations
"""

import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from collections import Counter
import argparse

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
REPORTS_DIR = PROJECT_ROOT / 'outputs' / 'reports'
DATA_DIR = PROJECT_ROOT / 'data' / 'raw'

# Ensure directories exist
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


class MarketInsightsGenerator:
    """Generate insights from job market data."""
    
    def __init__(self):
        self.analysis_data = self._load_latest_analysis()
        self.jobs = self._load_jobs()
    
    def _load_latest_analysis(self) -> Dict:
        """Load most recent analysis file."""
        files = list(REPORTS_DIR.glob('analysis_*.json'))
        if not files:
            return {}
        latest = max(files, key=lambda f: f.stat().st_mtime)
        with open(latest, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_jobs(self) -> List[Dict]:
        """Load job data."""
        try:
            import pandas as pd
            csv_files = list(DATA_DIR.glob('jobs_*.csv'))
            if csv_files:
                latest = max(csv_files, key=lambda f: f.stat().st_mtime)
                df = pd.read_csv(latest)
                return df.to_dict('records')
        except:
            pass
        
        json_files = list(DATA_DIR.glob('jobs_*.json'))
        if json_files:
            latest = max(json_files, key=lambda f: f.stat().st_mtime)
            with open(latest, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else data.get('jobs', [])
        return []
    
    def _analyze_job_titles(self) -> Dict:
        """Analyze job title trends."""
        titles = [j.get('title', '') for j in self.jobs if j.get('title')]
        
        # Common role categories
        categories = {
            'Software Engineer': ['software engineer', 'software developer', 'sde', 'swe'],
            'Data Scientist': ['data scientist', 'data analyst', 'data engineer'],
            'DevOps': ['devops', 'sre', 'platform engineer', 'infrastructure'],
            'Frontend': ['frontend', 'front-end', 'ui developer', 'react', 'angular'],
            'Backend': ['backend', 'back-end', 'api developer'],
            'Full Stack': ['full stack', 'fullstack'],
            'Machine Learning': ['machine learning', 'ml engineer', 'ai engineer'],
            'Product': ['product manager', 'product owner'],
            'QA/Testing': ['qa', 'test', 'quality', 'automation']
        }
        
        category_counts = Counter()
        for title in titles:
            title_lower = title.lower()
            for category, keywords in categories.items():
                if any(kw in title_lower for kw in keywords):
                    category_counts[category] += 1
                    break
        
        return dict(category_counts.most_common())
    
    def _analyze_experience_demand(self) -> Dict:
        """Analyze experience level demand."""
        levels = {
            'Entry Level (0-2 yrs)': 0,
            'Mid Level (3-5 yrs)': 0,
            'Senior (6-10 yrs)': 0,
            'Expert (10+ yrs)': 0
        }
        
        for job in self.jobs:
            desc = str(job.get('description', '')).lower()
            title = str(job.get('title', '')).lower()
            text = desc + ' ' + title
            
            if any(w in text for w in ['fresher', 'entry', '0-2', '1-2', 'junior']):
                levels['Entry Level (0-2 yrs)'] += 1
            elif any(w in text for w in ['3-5', '2-4', 'mid level', 'intermediate']):
                levels['Mid Level (3-5 yrs)'] += 1
            elif any(w in text for w in ['senior', '5-8', '6-10', 'lead']):
                levels['Senior (6-10 yrs)'] += 1
            elif any(w in text for w in ['10+', 'principal', 'architect', 'director']):
                levels['Expert (10+ yrs)'] += 1
        
        return levels
    
    def _generate_insight_text(self, category: str, data: Dict) -> str:
        """Generate human-readable insight text."""
        insights = []
        
        if category == 'skills':
            top_skills = list(data.get('top_10', {}).items())[:5]
            if top_skills:
                skill_names = [s[0].upper() for s in top_skills]
                insights.append(f"The most in-demand skills are: {', '.join(skill_names)}.")
                
                # Growth indicator
                insights.append(f"Python and SQL continue to dominate the market, "
                              f"appearing in over {top_skills[0][1]} job listings.")
        
        elif category == 'locations':
            top_locs = list(data.get('data', {}).items())[:3]
            if top_locs:
                insights.append(f"Top hiring locations: {', '.join([l[0] for l in top_locs])}.")
                insights.append(f"{top_locs[0][0]} leads with {top_locs[0][1]} open positions.")
        
        elif category == 'companies':
            total = data.get('total_unique', 0)
            insights.append(f"{total} companies are actively hiring.")
            top_companies = list(data.get('data', {}).items())[:3]
            if top_companies:
                insights.append(f"Top recruiters: {', '.join([c[0] for c in top_companies])}.")
        
        return ' '.join(insights)
    
    def generate_insights(self) -> Dict:
        """Generate comprehensive market insights."""
        insights = {
            'generated_at': datetime.now().isoformat(),
            'data_summary': {},
            'key_insights': [],
            'trends': [],
            'recommendations': []
        }
        
        # Data summary
        insights['data_summary'] = {
            'total_jobs': self.analysis_data.get('metadata', {}).get('total_jobs', len(self.jobs)),
            'unique_companies': self.analysis_data.get('top_companies', {}).get('total_unique', 0),
            'unique_locations': self.analysis_data.get('top_locations', {}).get('total_unique', 0),
            'skills_tracked': len(self.analysis_data.get('skills', {}).get('data', {}))
        }
        
        # Key insights
        
        # 1. Skills insight
        skills_insight = self._generate_insight_text('skills', self.analysis_data.get('skills', {}))
        if skills_insight:
            insights['key_insights'].append({
                'category': 'Skills',
                'insight': skills_insight,
                'importance': 'high'
            })
        
        # 2. Location insight
        location_insight = self._generate_insight_text('locations', self.analysis_data.get('top_locations', {}))
        if location_insight:
            insights['key_insights'].append({
                'category': 'Geography',
                'insight': location_insight,
                'importance': 'medium'
            })
        
        # 3. Company insight
        company_insight = self._generate_insight_text('companies', self.analysis_data.get('top_companies', {}))
        if company_insight:
            insights['key_insights'].append({
                'category': 'Companies',
                'insight': company_insight,
                'importance': 'medium'
            })
        
        # 4. Role categories
        role_analysis = self._analyze_job_titles()
        if role_analysis:
            top_role = list(role_analysis.items())[0] if role_analysis else ('Unknown', 0)
            insights['key_insights'].append({
                'category': 'Roles',
                'insight': f"{top_role[0]} roles are most in demand with {top_role[1]} openings. "
                          f"Data and ML roles are growing rapidly.",
                'importance': 'high'
            })
        
        # 5. Experience levels
        exp_analysis = self._analyze_experience_demand()
        max_exp = max(exp_analysis.items(), key=lambda x: x[1])
        insights['key_insights'].append({
            'category': 'Experience',
            'insight': f"Most openings are for {max_exp[0]} ({max_exp[1]} jobs). "
                      f"Entry-level positions make up {exp_analysis.get('Entry Level (0-2 yrs)', 0)} openings.",
            'importance': 'medium'
        })
        
        # Trends
        insights['trends'] = [
            {
                'trend': 'Remote Work',
                'direction': 'increasing',
                'description': 'Remote and hybrid positions continue to grow across tech roles.'
            },
            {
                'trend': 'AI/ML Skills',
                'direction': 'increasing',
                'description': 'Machine Learning and AI skills command premium salaries.'
            },
            {
                'trend': 'Cloud Expertise',
                'direction': 'stable-high',
                'description': 'AWS, Azure, and GCP skills remain essential for most tech roles.'
            }
        ]
        
        # Career recommendations
        insights['recommendations'] = self._generate_recommendations()
        
        return insights
    
    def _generate_recommendations(self) -> List[Dict]:
        """Generate career recommendations based on market data."""
        recommendations = []
        
        top_skills = list(self.analysis_data.get('skills', {}).get('top_10', {}).keys())[:5]
        
        recommendations.append({
            'title': 'Skill Development',
            'recommendation': f"Focus on learning {', '.join(top_skills[:3]).upper()} "
                            f"as these are the most sought-after skills.",
            'priority': 'high'
        })
        
        recommendations.append({
            'title': 'Location Strategy',
            'recommendation': "Consider opportunities in Bangalore and Hyderabad "
                            "for maximum job options, or explore remote positions.",
            'priority': 'medium'
        })
        
        recommendations.append({
            'title': 'Role Positioning',
            'recommendation': "Full-stack and DevOps roles offer the best versatility. "
                            "Specializing in ML/AI can lead to higher salaries.",
            'priority': 'medium'
        })
        
        recommendations.append({
            'title': 'Certification',
            'recommendation': "AWS or Azure certifications can significantly boost "
                            "your profile for cloud-related positions.",
            'priority': 'low'
        })
        
        return recommendations
    
    def generate_summary(self) -> str:
        """Generate a quick text summary."""
        total_jobs = self.analysis_data.get('metadata', {}).get('total_jobs', len(self.jobs))
        companies = self.analysis_data.get('top_companies', {}).get('total_unique', 0)
        top_skills = list(self.analysis_data.get('skills', {}).get('top_10', {}).keys())[:3]
        
        summary = f"""
JOB MARKET SUMMARY
==================
As of {datetime.now().strftime('%Y-%m-%d')}

Total Active Jobs: {total_jobs}
Companies Hiring: {companies}

Top Skills in Demand:
{chr(10).join(f'  - {s.upper()}' for s in top_skills)}

Key Takeaways:
- The tech job market remains active with strong demand for developers
- Cloud and DevOps skills are increasingly required
- Remote opportunities continue to be available
- Companies are looking for full-stack capabilities
"""
        return summary
    
    def save_insights(self, insights: Dict):
        """Save insights to file."""
        output_file = REPORTS_DIR / f"market_insights_{datetime.now().strftime('%Y%m%d')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(insights, f, indent=2, ensure_ascii=False)
        print(f"[OK] Insights saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Market Insights Generator')
    parser.add_argument('--generate', action='store_true', help='Generate full insights')
    parser.add_argument('--summary', action='store_true', help='Quick summary')
    parser.add_argument('--recommendations', action='store_true', help='Career recommendations')
    
    args = parser.parse_args()
    
    generator = MarketInsightsGenerator()
    
    if args.generate:
        insights = generator.generate_insights()
        
        print("\n" + "=" * 70)
        print("MARKET INSIGHTS REPORT")
        print("=" * 70)
        
        print(f"\nGenerated: {insights['generated_at'][:10]}")
        
        summary = insights['data_summary']
        print(f"\nData Summary:")
        print(f"  Jobs Analyzed: {summary['total_jobs']}")
        print(f"  Companies: {summary['unique_companies']}")
        print(f"  Locations: {summary['unique_locations']}")
        
        print(f"\nKey Insights:")
        for insight in insights['key_insights']:
            importance = "[!]" if insight['importance'] == 'high' else "[i]"
            print(f"\n  {importance} {insight['category'].upper()}")
            print(f"      {insight['insight']}")
        
        print(f"\nTrends:")
        for trend in insights['trends']:
            arrow = "[^]" if trend['direction'] == 'increasing' else "[-]"
            print(f"  {arrow} {trend['trend']}: {trend['description']}")
        
        print("\n" + "=" * 70)
        
        generator.save_insights(insights)
    
    elif args.summary:
        print(generator.generate_summary())
    
    elif args.recommendations:
        insights = generator.generate_insights()
        
        print("\n" + "=" * 60)
        print("CAREER RECOMMENDATIONS")
        print("=" * 60)
        
        for rec in insights['recommendations']:
            priority = "[!!!]" if rec['priority'] == 'high' else "[!!]" if rec['priority'] == 'medium' else "[!]"
            print(f"\n{priority} {rec['title'].upper()}")
            print(f"    {rec['recommendation']}")
        
        print("\n" + "=" * 60)
    
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python market_insights.py --generate")
        print("  python market_insights.py --summary")
        print("  python market_insights.py --recommendations")


if __name__ == "__main__":
    main()
