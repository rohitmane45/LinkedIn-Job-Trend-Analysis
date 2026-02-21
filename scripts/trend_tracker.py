"""
Trend Tracker
=============
Track and compare job market trends over time.

Usage:
    python trend_tracker.py --compare-weeks     # Compare this week vs last week
    python trend_tracker.py --skill-trends      # Show skill demand trends
    python trend_tracker.py --report            # Generate trend report
"""

import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
from collections import Counter
import argparse

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
REPORTS_DIR = PROJECT_ROOT / 'outputs' / 'reports'
TRENDS_FILE = REPORTS_DIR / 'trends_history.json'

# Ensure directory exists
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


class TrendTracker:
    """Track job market trends over time."""
    
    # Skills to track (loaded from centralized config)
    from skills_loader import SKILLS_TO_TRACK as _SKILLS_TO_TRACK
    SKILLS_TO_TRACK = _SKILLS_TO_TRACK
    
    def __init__(self):
        self.history = self._load_history()
    
    def _load_history(self) -> Dict:
        """Load trend history from file."""
        if TRENDS_FILE.exists():
            with open(TRENDS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'snapshots': [], 'created_at': datetime.now().isoformat()}
    
    def _save_history(self):
        """Save trend history to file."""
        with open(TRENDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)
    
    def _load_analysis_files(self) -> List[Dict]:
        """Load all analysis files."""
        analysis_files = list(REPORTS_DIR.glob('analysis_*.json'))
        analyses = []
        
        for f in sorted(analysis_files, key=lambda x: x.stat().st_mtime):
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
                data['_file'] = f.name
                data['_date'] = datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d')
                analyses.append(data)
        
        return analyses
    
    def record_snapshot(self, analysis_data: Dict = None):
        """Record current state as a snapshot."""
        if not analysis_data:
            # Load latest analysis
            files = list(REPORTS_DIR.glob('analysis_*.json'))
            if not files:
                print("[X] No analysis files found")
                return
            latest = max(files, key=lambda f: f.stat().st_mtime)
            with open(latest, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
        
        snapshot = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'timestamp': datetime.now().isoformat(),
            'total_jobs': analysis_data.get('metadata', {}).get('total_jobs', 0),
            'top_skills': analysis_data.get('skills', {}).get('top_10', {}),
            'top_companies': dict(list(analysis_data.get('top_companies', {}).get('data', {}).items())[:10]),
            'top_locations': dict(list(analysis_data.get('top_locations', {}).get('data', {}).items())[:10]),
            'unique_companies': analysis_data.get('top_companies', {}).get('total_unique', 0),
            'unique_locations': analysis_data.get('top_locations', {}).get('total_unique', 0)
        }
        
        self.history['snapshots'].append(snapshot)
        self._save_history()
        print(f"[OK] Snapshot recorded for {snapshot['date']}")
    
    def compare_periods(self, period1_days: int = 7, period2_days: int = 14) -> Dict:
        """Compare two time periods."""
        analyses = self._load_analysis_files()
        
        if len(analyses) < 2:
            print("[!] Need at least 2 analysis files for comparison")
            return {}
        
        # Get most recent and older analysis
        current = analyses[-1]
        previous = analyses[-2] if len(analyses) >= 2 else analyses[-1]
        
        comparison = {
            'current_date': current.get('_date'),
            'previous_date': previous.get('_date'),
            'changes': {}
        }
        
        # Compare total jobs
        current_jobs = current.get('metadata', {}).get('total_jobs', 0)
        previous_jobs = previous.get('metadata', {}).get('total_jobs', 0)
        job_change = current_jobs - previous_jobs
        job_change_pct = (job_change / previous_jobs * 100) if previous_jobs > 0 else 0
        
        comparison['changes']['total_jobs'] = {
            'current': current_jobs,
            'previous': previous_jobs,
            'change': job_change,
            'change_percent': round(job_change_pct, 1)
        }
        
        # Compare skills
        current_skills = current.get('skills', {}).get('top_10', {})
        previous_skills = previous.get('skills', {}).get('top_10', {})
        
        skill_changes = []
        all_skills = set(current_skills.keys()) | set(previous_skills.keys())
        
        for skill in all_skills:
            curr_count = current_skills.get(skill, 0)
            prev_count = previous_skills.get(skill, 0)
            change = curr_count - prev_count
            if change != 0:
                skill_changes.append({
                    'skill': skill,
                    'current': curr_count,
                    'previous': prev_count,
                    'change': change,
                    'trend': 'up' if change > 0 else 'down'
                })
        
        skill_changes.sort(key=lambda x: abs(x['change']), reverse=True)
        comparison['changes']['skills'] = skill_changes[:10]
        
        # Compare companies
        current_companies = current.get('top_companies', {}).get('data', {})
        previous_companies = previous.get('top_companies', {}).get('data', {})
        
        # New companies hiring
        new_companies = set(current_companies.keys()) - set(previous_companies.keys())
        comparison['changes']['new_companies'] = list(new_companies)[:10]
        
        return comparison
    
    def get_skill_trends(self, days: int = 30) -> Dict:
        """Get skill demand trends over time."""
        if len(self.history['snapshots']) < 2:
            # Try to build from analysis files
            analyses = self._load_analysis_files()
            trends = {}
            
            for analysis in analyses[-10:]:  # Last 10 analyses
                date = analysis.get('_date')
                skills = analysis.get('skills', {}).get('top_10', {})
                
                for skill, count in skills.items():
                    if skill not in trends:
                        trends[skill] = []
                    trends[skill].append({'date': date, 'count': count})
            
            return trends
        
        # Build from snapshots
        trends = {}
        for snapshot in self.history['snapshots'][-30:]:
            date = snapshot['date']
            for skill, count in snapshot.get('top_skills', {}).items():
                if skill not in trends:
                    trends[skill] = []
                trends[skill].append({'date': date, 'count': count})
        
        return trends
    
    def generate_trend_report(self) -> str:
        """Generate a comprehensive trend report."""
        comparison = self.compare_periods()
        skill_trends = self.get_skill_trends()
        
        report = []
        report.append("=" * 60)
        report.append("JOB MARKET TREND REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("=" * 60)
        
        if comparison:
            report.append(f"\nComparing: {comparison.get('previous_date')} -> {comparison.get('current_date')}")
            report.append("-" * 40)
            
            # Job changes
            job_changes = comparison.get('changes', {}).get('total_jobs', {})
            change_pct = job_changes.get('change_percent', 0)
            arrow = "[^]" if change_pct > 0 else "[v]" if change_pct < 0 else "[-]"
            report.append(f"\nTotal Jobs: {job_changes.get('current', 0)} {arrow} ({change_pct:+.1f}%)")
            
            # Skill changes
            report.append("\nSkill Demand Changes:")
            for skill_change in comparison.get('changes', {}).get('skills', [])[:10]:
                trend = "[^]" if skill_change['trend'] == 'up' else "[v]"
                report.append(f"  {trend} {skill_change['skill'].upper()}: {skill_change['change']:+d}")
            
            # New companies
            new_companies = comparison.get('changes', {}).get('new_companies', [])
            if new_companies:
                report.append(f"\nNew Companies Hiring ({len(new_companies)}):")
                for company in new_companies[:5]:
                    report.append(f"  [+] {company}")
        
        # Skill trends summary
        if skill_trends:
            report.append("\n" + "-" * 40)
            report.append("Skill Trends (Last 30 days):")
            
            for skill, history in list(skill_trends.items())[:10]:
                if len(history) >= 2:
                    first = history[0]['count']
                    last = history[-1]['count']
                    change = last - first
                    trend = "[^]" if change > 0 else "[v]" if change < 0 else "[-]"
                    report.append(f"  {trend} {skill.upper()}: {first} -> {last} ({change:+d})")
        
        # Forecast section
        forecasts = self.forecast_skills()
        if forecasts:
            report.append("\n" + "-" * 40)
            report.append("Skill Demand Forecast (90-day):")
            for item in forecasts[:10]:
                direction = "[^]" if item['growth_rate'] > 0 else "[v]" if item['growth_rate'] < 0 else "[-]"
                report.append(
                    f"  {direction} {item['skill'].upper()}: "
                    f"predicted {item['predicted_count']:.0f} mentions "
                    f"(R²={item['confidence']:.2f})"
                )
        
        # Growth rankings
        rankings = self.get_growth_rankings()
        if rankings.get('rising'):
            report.append("\n" + "-" * 40)
            report.append("Growth Rankings:")
            report.append("  RISING:    " + ", ".join(s.upper() for s in rankings['rising'][:5]))
            if rankings.get('stable'):
                report.append("  STABLE:    " + ", ".join(s.upper() for s in rankings['stable'][:5]))
            if rankings.get('declining'):
                report.append("  DECLINING: " + ", ".join(s.upper() for s in rankings['declining'][:5]))
        
        report.append("\n" + "=" * 60)
        
        report_text = "\n".join(report)
        print(report_text)
        
        # Save report
        report_file = REPORTS_DIR / f"trend_report_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        print(f"\n[OK] Report saved to: {report_file}")
        
        return report_text

    # ──────────────────────────────────────────────────────────
    # Forecasting
    # ──────────────────────────────────────────────────────────

    def forecast_skills(self, horizon_days: int = 90) -> List[Dict]:
        """
        Forecast future skill demand using linear regression.

        Fits a line (numpy polyfit, degree 1) on each skill's historical
        counts and extrapolates forward by `horizon_days`.

        Returns:
            List of dicts sorted by growth rate, each containing:
            - skill: skill name
            - current_count: latest known count
            - predicted_count: forecasted count at horizon
            - growth_rate: slope (change per day)
            - confidence: R² score (0-1)
        """
        import numpy as np

        skill_trends = self.get_skill_trends()
        if not skill_trends:
            return []

        results = []
        for skill, history in skill_trends.items():
            if len(history) < 2:
                continue

            # Convert dates to numeric (days from first date)
            try:
                dates = [datetime.strptime(h['date'], '%Y-%m-%d') for h in history]
            except (ValueError, KeyError):
                continue

            base_date = dates[0]
            x = np.array([(d - base_date).days for d in dates], dtype=float)
            y = np.array([h['count'] for h in history], dtype=float)

            if len(set(x)) < 2:
                # All same date — can't fit a line
                continue

            # Fit linear regression
            coeffs = np.polyfit(x, y, 1)
            slope, intercept = coeffs

            # Predict at horizon
            last_day = x[-1]
            forecast_day = last_day + horizon_days
            predicted = slope * forecast_day + intercept
            predicted = max(0, predicted)  # Can't have negative mentions

            # R² confidence
            y_pred = np.polyval(coeffs, x)
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            r_squared = max(0, min(1, r_squared))

            results.append({
                'skill': skill,
                'current_count': int(y[-1]),
                'predicted_count': round(predicted, 1),
                'growth_rate': round(slope, 4),
                'confidence': round(r_squared, 3),
                'data_points': len(history),
            })

        # Sort by growth rate descending
        results.sort(key=lambda r: r['growth_rate'], reverse=True)
        return results

    def get_growth_rankings(self) -> Dict:
        """
        Categorize skills into rising, stable, and declining groups
        based on their linear growth rate.

        Returns:
            dict with keys 'rising', 'stable', 'declining', each a list of skill names.
        """
        forecasts = self.forecast_skills()
        if not forecasts:
            return {'rising': [], 'stable': [], 'declining': []}

        rising = [f['skill'] for f in forecasts if f['growth_rate'] > 0.1]
        declining = [f['skill'] for f in forecasts if f['growth_rate'] < -0.1]
        stable = [f['skill'] for f in forecasts if -0.1 <= f['growth_rate'] <= 0.1]

        return {
            'rising': rising,
            'stable': stable,
            'declining': declining,
        }


def main():
    parser = argparse.ArgumentParser(description='Track Job Market Trends')
    parser.add_argument('--snapshot', action='store_true', help='Record current snapshot')
    parser.add_argument('--compare', action='store_true', help='Compare recent periods')
    parser.add_argument('--skill-trends', action='store_true', help='Show skill trends')
    parser.add_argument('--forecast', action='store_true', help='Forecast skill demand (90-day)')
    parser.add_argument('--report', action='store_true', help='Generate full trend report')
    
    args = parser.parse_args()
    
    tracker = TrendTracker()
    
    if args.snapshot:
        tracker.record_snapshot()
    elif args.compare:
        comparison = tracker.compare_periods()
        if comparison:
            print(json.dumps(comparison, indent=2))
    elif args.skill_trends:
        trends = tracker.get_skill_trends()
        print(json.dumps(trends, indent=2))
    elif args.forecast:
        forecasts = tracker.forecast_skills()
        if forecasts:
            print("\n" + "=" * 60)
            print("SKILL DEMAND FORECAST (90-day)")
            print("=" * 60)
            for f in forecasts[:15]:
                direction = "↑" if f['growth_rate'] > 0 else "↓" if f['growth_rate'] < 0 else "→"
                print(f"  {direction} {f['skill'].upper():25s} "
                      f"now: {f['current_count']:4d}  →  predicted: {f['predicted_count']:6.0f}  "
                      f"(R²={f['confidence']:.2f})")
            print("=" * 60)

            rankings = tracker.get_growth_rankings()
            if rankings['rising']:
                print(f"\n  RISING:    {', '.join(s.upper() for s in rankings['rising'][:5])}")
            if rankings['stable']:
                print(f"  STABLE:    {', '.join(s.upper() for s in rankings['stable'][:5])}")
            if rankings['declining']:
                print(f"  DECLINING: {', '.join(s.upper() for s in rankings['declining'][:5])}")
        else:
            print("[!] Not enough historical data for forecasting.")
            print("    Run the pipeline a few times to build up trend history.")
    elif args.report:
        tracker.generate_trend_report()
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python trend_tracker.py --snapshot     # Save current state")
        print("  python trend_tracker.py --compare      # Compare periods")
        print("  python trend_tracker.py --forecast     # 90-day skill forecast")
        print("  python trend_tracker.py --report       # Full report")


if __name__ == "__main__":
    main()

