"""
Master Flow Controller
======================
Complete project flow - from scraping to insights in one command.

FLOW:
1. Ask Data Source → Real-time API or Local stored data
2. Fetch/Load Data → Get job listings
3. Analyze Data → Extract insights & trends  
4. Ask for User Profile → Get user skills/preferences
5. Match Resume to Jobs → Find best matching jobs
6. Suggest Skills to Learn → Identify skill gaps
7. Save Results → Store for future use
8. Generate Visualizations → Create charts & reports
9. Launch Dashboard → View everything in web browser

Usage:
    python master_flow.py                    # Interactive (asks data source)
    python master_flow.py --realtime         # Force real-time API
    python master_flow.py --local            # Force local data
    python master_flow.py --quick            # Quick mode (no user input)
    python master_flow.py --dashboard-only   # Just launch dashboard
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import json
import subprocess
from pathlib import Path
from datetime import datetime
import argparse
import webbrowser
import time

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / 'scripts'
DATA_DIR = PROJECT_ROOT / 'data' / 'raw'
REPORTS_DIR = PROJECT_ROOT / 'outputs' / 'reports'
CONFIG_DIR = PROJECT_ROOT / 'config'

# Import data source manager
sys.path.insert(0, str(SCRIPTS_DIR))
try:
    from data_source_manager import DataSourceManager
except ImportError:
    DataSourceManager = None


class MasterFlowController:
    """Controls the complete project flow."""
    
    def __init__(self):
        self.start_time = None
        self.results = {}
        self.user_profile = None
        self.job_matches = []
        self.skill_gaps = []
        self.analysis_data = {}
        self.data_source = None
        self.data_file = None
        
    def print_header(self, text: str, char: str = "="):
        """Print formatted header."""
        print(f"\n{char * 70}")
        print(f"  {text}")
        print(f"{char * 70}\n")
    
    def print_step(self, step_num: int, total: int, text: str):
        """Print step progress."""
        print(f"\n[STEP {step_num}/{total}] {text}")
        print("-" * 50)
    
    def run_script(self, script_name: str, args: list = None, capture: bool = False) -> tuple:
        """Run a Python script."""
        script_path = SCRIPTS_DIR / script_name
        
        if not script_path.exists():
            print(f"  [SKIP] Script not found: {script_name}")
            return False, ""
        
        cmd = [sys.executable, str(script_path)]
        if args:
            cmd.extend(args)
        
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        try:
            if capture:
                result = subprocess.run(cmd, capture_output=True, text=True, 
                                       encoding='utf-8', errors='replace', env=env)
                return result.returncode == 0, result.stdout
            else:
                result = subprocess.run(cmd, env=env)
                return result.returncode == 0, ""
        except Exception as e:
            print(f"  [ERROR] {e}")
            return False, ""
    
    def step1_select_data_source(self, data_source: str = 'ask') -> bool:
        """Step 1: Select and fetch data source."""
        self.print_step(1, 9, "DATA SOURCE SELECTION")
        
        if DataSourceManager:
            manager = DataSourceManager()
            
            # Show current status
            status = manager.get_data_status()
            
            print(f"  Current Data Status:")
            if status['has_local_data']:
                print(f"    - Local file: {status['latest_file']}")
                print(f"    - Jobs: {status['job_count']}")
                print(f"    - Age: {status['data_age']}")
                if status['is_stale']:
                    print(f"    - [!] Data is STALE (consider refreshing)")
            else:
                print(f"    - No local data available")
            
            print()
            
            # Get data based on source
            if data_source == 'ask':
                print("  Choose data source:")
                print("    [1] REAL-TIME - Fetch fresh data from API (1-2 min)")
                print("    [2] LOCAL     - Use existing stored data (instant)")
                
                while True:
                    choice = input("\n  Enter 1 or 2: ").strip()
                    if choice == '1':
                        data_source = 'realtime'
                        break
                    elif choice == '2':
                        if status['has_local_data']:
                            data_source = 'local'
                            break
                        else:
                            print("  [X] No local data. You must fetch from API first.")
                    else:
                        print("  [X] Invalid choice")
            
            success, path = manager.get_data(data_source)
            self.data_source = data_source
            self.data_file = path
            
            if success:
                self.results['data_source'] = data_source
                self.results['data_file'] = path
                return True
            
            return False
        else:
            # Fallback if data_source_manager not available
            print("  [WARN] Data source manager not available")
            if data_source == 'realtime':
                return self._fallback_scrape()
            return True
    
    def _fallback_scrape(self) -> bool:
        """Fallback scraping method."""
        print("  Fetching data from API...")
        success, _ = self.run_script('scraper_india.py')
        return success or True  # Continue even if fails
    
    def step2_analyze_data(self) -> bool:
        """Step 2: Analyze scraped data."""
        self.print_step(2, 9, "ANALYZING DATA - Extracting Insights & Trends")
        
        print("  Running analysis on job data...")
        success, _ = self.run_script('analyze_jobs.py')
        
        if success:
            # Load analysis results
            analysis_files = list(REPORTS_DIR.glob('analysis_*.json'))
            if analysis_files:
                latest = max(analysis_files, key=lambda f: f.stat().st_mtime)
                with open(latest, 'r', encoding='utf-8') as f:
                    self.analysis_data = json.load(f)
                
                total_jobs = self.analysis_data.get('metadata', {}).get('total_jobs', 0)
                companies = self.analysis_data.get('top_companies', {}).get('total_unique', 0)
                skills = len(self.analysis_data.get('skills', {}).get('data', {}))
                
                print(f"  [OK] Analysis complete:")
                print(f"       - Total Jobs: {total_jobs}")
                print(f"       - Companies: {companies}")
                print(f"       - Skills Identified: {skills}")
                
                self.results['total_jobs'] = total_jobs
                self.results['companies'] = companies
                return True
        
        print("  [ERROR] Analysis failed")
        return False
    
    def step3_get_user_profile(self, quick_mode: bool = False) -> bool:
        """Step 3: Get or create user profile."""
        self.print_step(3, 9, "USER PROFILE - Your Skills & Preferences")
        
        profile_file = CONFIG_DIR / 'user_profile.json'
        
        # Check existing profile
        if profile_file.exists():
            with open(profile_file, 'r', encoding='utf-8') as f:
                self.user_profile = json.load(f)
            
            print(f"  Found existing profile for: {self.user_profile.get('name', 'User')}")
            print(f"  Skills: {', '.join(self.user_profile.get('skills', [])[:5])}...")
            
            if not quick_mode:
                choice = input("\n  Use this profile? (yes/no/edit): ").strip().lower()
                if choice == 'no' or choice == 'edit':
                    return self._create_profile_interactive()
            
            return True
        
        if quick_mode:
            print("  [SKIP] No profile found, skipping in quick mode")
            return False
        
        return self._create_profile_interactive()
    
    def _create_profile_interactive(self) -> bool:
        """Create user profile interactively."""
        print("\n  Let's create your profile:\n")
        
        profile = {
            'name': input("  Your name: ").strip(),
            'title': input("  Desired job title (e.g., Data Scientist): ").strip(),
            'experience_years': 0,
            'skills': [],
            'preferred_locations': [],
            'job_types': [],
            'updated_at': datetime.now().isoformat()
        }
        
        exp = input("  Years of experience: ").strip()
        profile['experience_years'] = int(exp) if exp.isdigit() else 0
        
        skills = input("  Your skills (comma-separated): ").strip()
        profile['skills'] = [s.strip() for s in skills.split(',') if s.strip()]
        
        locations = input("  Preferred locations (comma-separated): ").strip()
        profile['preferred_locations'] = [l.strip() for l in locations.split(',') if l.strip()]
        
        job_types = input("  Job types (remote/hybrid/onsite, comma-separated): ").strip()
        profile['job_types'] = [j.strip() for j in job_types.split(',') if j.strip()]
        
        # Save profile
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_DIR / 'user_profile.json', 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2)
        
        self.user_profile = profile
        print(f"\n  [OK] Profile saved!")
        return True
    
    def step4_match_jobs(self) -> bool:
        """Step 4: Match user profile to jobs."""
        self.print_step(4, 9, "JOB MATCHING - Finding Best Jobs for You")
        
        if not self.user_profile:
            print("  [SKIP] No user profile available")
            return False
        
        print("  Matching your profile against available jobs...")
        success, output = self.run_script('resume_matcher.py', ['--match'], capture=True)
        
        if success:
            # Load matches
            match_files = list(REPORTS_DIR.glob('job_matches_*.json'))
            if match_files:
                latest = max(match_files, key=lambda f: f.stat().st_mtime)
                with open(latest, 'r', encoding='utf-8') as f:
                    match_data = json.load(f)
                    self.job_matches = match_data.get('matches', [])
                
                print(f"  [OK] Found {len(self.job_matches)} matching jobs!")
                
                # Show top 3
                print("\n  Top 3 Matches:")
                for match in self.job_matches[:3]:
                    score = match.get('score', 0)
                    title = match.get('title', 'N/A')
                    company = match.get('company', 'N/A')
                    print(f"    - {title} at {company} ({score:.0f}% match)")
                
                self.results['job_matches'] = len(self.job_matches)
                return True
        
        print("  [WARN] Job matching had issues")
        return True
    
    def step5_analyze_skill_gaps(self) -> bool:
        """Step 5: Identify skill gaps and suggest learning."""
        self.print_step(5, 9, "SKILL GAP ANALYSIS - What to Learn")
        
        if not self.user_profile:
            print("  [SKIP] No user profile available")
            return False
        
        print("  Analyzing your skills against market demand...")
        success, output = self.run_script('resume_matcher.py', ['--gaps'], capture=True)
        
        # Generate recommendations
        self._generate_learning_recommendations()
        return True
    
    def _generate_learning_recommendations(self):
        """Generate learning and certification recommendations."""
        if not self.analysis_data:
            return
        
        user_skills = set(s.lower() for s in self.user_profile.get('skills', []))
        market_skills = self.analysis_data.get('skills', {}).get('data', {})
        
        # Find top skills user doesn't have
        missing_skills = []
        for skill, count in sorted(market_skills.items(), key=lambda x: x[1], reverse=True):
            if skill.lower() not in user_skills:
                missing_skills.append({'skill': skill, 'demand': count})
        
        print("\n  Skills to Learn (High Demand):")
        for item in missing_skills[:5]:
            print(f"    [!] {item['skill'].upper()} - {item['demand']} jobs require this")
        
        # Certification recommendations
        print("\n  Recommended Certifications:")
        cert_recommendations = {
            'aws': 'AWS Solutions Architect / AWS Developer Associate',
            'azure': 'Microsoft Azure Fundamentals (AZ-900)',
            'gcp': 'Google Cloud Professional Data Engineer',
            'python': 'PCEP/PCAP Python Certification',
            'machine learning': 'TensorFlow Developer Certificate / AWS ML Specialty',
            'docker': 'Docker Certified Associate',
            'kubernetes': 'Certified Kubernetes Administrator (CKA)',
            'data science': 'IBM Data Science Professional Certificate',
            'sql': 'Microsoft SQL Server Certification',
            'devops': 'AWS DevOps Engineer / Azure DevOps Engineer'
        }
        
        shown = 0
        for skill in missing_skills[:10]:
            skill_lower = skill['skill'].lower()
            for key, cert in cert_recommendations.items():
                if key in skill_lower and shown < 3:
                    print(f"    [*] {cert}")
                    shown += 1
                    break
        
        self.skill_gaps = missing_skills[:10]
        self.results['skills_to_learn'] = len(self.skill_gaps)
    
    def step6_save_results(self) -> bool:
        """Step 6: Save all results."""
        self.print_step(6, 9, "SAVING RESULTS")
        
        # Save comprehensive results
        results_file = REPORTS_DIR / f"flow_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        
        output = {
            'generated_at': datetime.now().isoformat(),
            'data_source': self.data_source,
            'summary': self.results,
            'user_profile': self.user_profile,
            'top_matches': self.job_matches[:10] if self.job_matches else [],
            'skill_gaps': self.skill_gaps,
            'market_insights': {
                'top_skills': list(self.analysis_data.get('skills', {}).get('top_10', {}).items())[:10],
                'top_companies': list(self.analysis_data.get('top_companies', {}).get('data', {}).items())[:10],
                'top_locations': list(self.analysis_data.get('top_locations', {}).get('data', {}).items())[:10]
            }
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"  [OK] Results saved to: {results_file.name}")
        return True
    
    def step7_generate_visualizations(self) -> bool:
        """Step 7: Generate visualizations and reports."""
        self.print_step(7, 9, "GENERATING VISUALIZATIONS & REPORTS")
        
        print("  Creating visualizations...")
        self.run_script('visualize_data.py')
        
        print("  Generating HTML report...")
        self.run_script('generate_report.py', ['--format', 'html'])
        
        print("  Generating Excel export...")
        self.run_script('export_manager.py', ['--excel'])
        
        print("  [OK] All reports generated!")
        return True
    
    def step8_launch_dashboard(self) -> bool:
        """Step 8: Launch the web dashboard."""
        self.print_step(8, 9, "LAUNCHING WEB DASHBOARD")
        
        print("  Starting dashboard server...")
        print("  Dashboard will open in your browser at http://localhost:5000")
        print("\n  Press Ctrl+C to stop the dashboard\n")
        
        # Open browser after short delay
        import threading
        def open_browser():
            time.sleep(2)
            webbrowser.open('http://localhost:5000')
        
        threading.Thread(target=open_browser, daemon=True).start()
        
        # Run dashboard
        self.run_script('dashboard.py')
        return True
    
    def print_summary(self):
        """Print flow summary."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        self.print_header("FLOW COMPLETE - SUMMARY", "=")
        
        print(f"  Duration: {duration:.1f} seconds")
        print(f"  Data Source: {self.data_source.upper() if self.data_source else 'N/A'}\n")
        
        print("  RESULTS:")
        print(f"    Jobs Analyzed:    {self.results.get('total_jobs', 'N/A')}")
        print(f"    Companies Found:  {self.results.get('companies', 'N/A')}")
        print(f"    Job Matches:      {self.results.get('job_matches', 'N/A')}")
        print(f"    Skills to Learn:  {self.results.get('skills_to_learn', 'N/A')}")
        
        if self.job_matches:
            print("\n  YOUR TOP JOB MATCHES:")
            for i, match in enumerate(self.job_matches[:5], 1):
                print(f"    {i}. {match.get('title')} at {match.get('company')} ({match.get('score', 0):.0f}%)")
        
        if self.skill_gaps:
            print("\n  SKILLS TO FOCUS ON:")
            for gap in self.skill_gaps[:5]:
                print(f"    - {gap['skill'].upper()}")
        
        print("\n  OUTPUT FILES:")
        print(f"    - Reports: outputs/reports/")
        print(f"    - Exports: data/exports/")
        print(f"    - Visualizations: outputs/visualizations/")
    
    def run_complete_flow(self, data_source: str = 'ask', quick_mode: bool = False, 
                          dashboard_only: bool = False):
        """Run the complete project flow."""
        self.start_time = datetime.now()
        
        self.print_header("LINKEDIN JOB ANALYSIS - MASTER FLOW", "=")
        print(f"  Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Mode: {'Quick' if quick_mode else 'Interactive'}")
        
        if dashboard_only:
            self.step8_launch_dashboard()
            return
        
        print("""
  FLOW OVERVIEW:
  ==============
  1. Data Source     -> Real-time API or Local data?
  2. Fetch/Load      -> Get job listings
  3. Analyze Data    -> Extract insights & trends
  4. User Profile    -> Your skills & preferences
  5. Match Jobs      -> Find best jobs for you
  6. Skill Gaps      -> What to learn + certifications
  7. Save Results    -> Store everything
  8. Visualizations  -> Charts & reports
  9. Dashboard       -> View in web browser
        """)
        
        if not quick_mode and data_source == 'ask':
            input("\n  Press Enter to start the flow...")
        
        # Execute flow
        self.step1_select_data_source(data_source)
        self.step2_analyze_data()
        self.step3_get_user_profile(quick_mode)
        self.step4_match_jobs()
        self.step5_analyze_skill_gaps()
        self.step6_save_results()
        self.step7_generate_visualizations()
        
        # Summary before dashboard
        self.print_summary()
        
        if not quick_mode:
            launch = input("\n  Launch dashboard? (yes/no): ").strip().lower()
            if launch == 'yes':
                self.step8_launch_dashboard()
        else:
            print("\n  [TIP] Run 'python scripts/cli.py dashboard' to view results")


def main():
    parser = argparse.ArgumentParser(description='Master Flow Controller')
    parser.add_argument('--realtime', action='store_true', help='Force real-time API data')
    parser.add_argument('--local', action='store_true', help='Force local stored data')
    parser.add_argument('--quick', action='store_true', help='Quick mode (minimal user input)')
    parser.add_argument('--dashboard-only', action='store_true', help='Just launch dashboard')
    
    args = parser.parse_args()
    
    # Determine data source
    if args.realtime:
        data_source = 'realtime'
    elif args.local:
        data_source = 'local'
    else:
        data_source = 'ask'
    
    controller = MasterFlowController()
    controller.run_complete_flow(
        data_source=data_source,
        quick_mode=args.quick,
        dashboard_only=args.dashboard_only
    )


if __name__ == "__main__":
    main()
