"""
Pipeline Runner
===============
Run the complete job analysis pipeline with one command.

Usage:
    python run_pipeline.py                    # Run full pipeline
    python run_pipeline.py --skip-scrape      # Skip scraping, use existing data
    python run_pipeline.py --notify           # Send email notification
"""

import subprocess
import sys
import os

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from datetime import datetime
import webbrowser
import argparse

# Optional imports
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / 'scripts'
CONFIG_FILE = PROJECT_ROOT / 'config' / 'settings.yaml'
DATA_DIR = PROJECT_ROOT / 'data' / 'raw'
REPORTS_DIR = PROJECT_ROOT / 'outputs' / 'reports'


class PipelineRunner:
    """Run the complete LinkedIn Job Analysis pipeline."""
    
    def __init__(self):
        self.config = self._load_config()
        self.start_time = None
        self.results = {
            'scrape': None,
            'analyze': None,
            'report': None,
            'cleanup': None
        }
        self.report_path = None
        
    def _load_config(self) -> dict:
        """Load configuration from YAML file."""
        if HAS_YAML and CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def _run_script(self, script_name: str, args: list = None) -> bool:
        """Run a Python script and return success status."""
        script_path = SCRIPTS_DIR / script_name
        
        if not script_path.exists():
            print(f"[X] Script not found: {script_name}")
            return False
        
        cmd = [sys.executable, str(script_path)]
        if args:
            cmd.extend(args)
        
        try:
            # Set encoding for subprocess
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env
            )
            if result.returncode == 0:
                print(result.stdout)
                return True
            else:
                print(f"[X] Error in {script_name}:")
                print(result.stderr)
                return False
        except Exception as e:
            print(f"[X] Failed to run {script_name}: {e}")
            return False
    
    def _find_latest_file(self, directory: Path, pattern: str) -> Path:
        """Find the most recently modified file matching pattern."""
        if not directory.exists():
            return None
        files = list(directory.glob(pattern))
        if not files:
            return None
        return max(files, key=lambda f: f.stat().st_mtime)
    
    def step_scrape(self) -> bool:
        """Step 1: Run the scraper."""
        print("\n" + "="*60)
        print("[>] STEP 1: Scraping Job Listings")
        print("="*60 + "\n")
        
        # Check which scraper exists
        if (SCRIPTS_DIR / 'scraper_india.py').exists():
            success = self._run_script('scraper_india.py')
        elif (SCRIPTS_DIR / 'scraper_v2.py').exists():
            success = self._run_script('scraper_v2.py')
        else:
            print("[!] No scraper found, skipping...")
            return True
        
        self.results['scrape'] = success
        return success
    
    def step_analyze(self) -> bool:
        """Step 2: Analyze the scraped data."""
        print("\n" + "="*60)
        print("[>] STEP 2: Analyzing Job Data")
        print("="*60 + "\n")
        
        # Find latest data file
        data_file = self._find_latest_file(DATA_DIR, 'jobs_*.csv')
        if not data_file:
            data_file = self._find_latest_file(DATA_DIR, 'jobs_*.json')
        
        if not data_file:
            print("[X] No data file found to analyze")
            return False
        
        print(f"[i] Analyzing: {data_file.name}")
        
        success = self._run_script('analyze_jobs.py', ['--input', str(data_file)])
        self.results['analyze'] = success
        return success
    
    def step_visualize(self) -> bool:
        """Step 2.5: Generate visualizations (optional)."""
        print("\n" + "="*60)
        print("[>] STEP 2.5: Generating Visualizations")
        print("="*60 + "\n")
        
        if not (SCRIPTS_DIR / 'visualize_data.py').exists():
            print("[!] Visualization script not found, skipping...")
            return True
        
        return self._run_script('visualize_data.py')
    
    def step_report(self) -> bool:
        """Step 3: Generate the report."""
        print("\n" + "="*60)
        print("[>] STEP 3: Generating Report")
        print("="*60 + "\n")
        
        report_format = self.config.get('report', {}).get('format', 'html')
        
        success = self._run_script('generate_report.py', ['--format', report_format])
        
        if success:
            # Find the generated report
            pattern = f'report_*.{report_format}' if report_format == 'html' else 'report_*.md'
            self.report_path = self._find_latest_file(REPORTS_DIR, pattern)
        
        self.results['report'] = success
        return success
    
    def step_cleanup(self) -> bool:
        """Step 4: Clean up old files."""
        print("\n" + "="*60)
        print("[>] STEP 4: Cleaning Up Old Files")
        print("="*60 + "\n")
        
        if not (SCRIPTS_DIR / 'cleanup_project.py').exists():
            print("[!] Cleanup script not found, skipping...")
            return True
        
        # Run cleanup in dry-run mode
        success = self._run_script('cleanup_project.py', ['--dry-run'])
        self.results['cleanup'] = success
        return success
    
    def send_email_notification(self) -> bool:
        """Send email notification with report attached."""
        email_config = self.config.get('email', {})
        
        if not email_config.get('enabled', False):
            print("[i] Email notifications disabled")
            return True
        
        print("\n[>] Sending email notification...")
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders
            
            msg = MIMEMultipart()
            msg['From'] = email_config['sender_email']
            msg['To'] = email_config['recipient_email']
            msg['Subject'] = f"LinkedIn Job Analysis Report - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Email body
            body = f"""
LinkedIn Job Analysis Report

Pipeline completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Results:
- Scraping: {'Success' if self.results['scrape'] else 'Failed'}
- Analysis: {'Success' if self.results['analyze'] else 'Failed'}
- Report: {'Success' if self.results['report'] else 'Failed'}

Please find the detailed report attached.
            """
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach report if exists
            if self.report_path and self.report_path.exists():
                with open(self.report_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', 
                                  f'attachment; filename={self.report_path.name}')
                    msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['sender_email'], email_config['sender_password'])
            server.send_message(msg)
            server.quit()
            
            print("[OK] Email sent successfully!")
            return True
            
        except Exception as e:
            print(f"[X] Failed to send email: {e}")
            return False
    
    def open_report(self):
        """Open the generated report in browser."""
        if self.report_path and self.report_path.exists():
            if self.config.get('report', {}).get('auto_open', True):
                print(f"\n[>] Opening report in browser...")
                webbrowser.open(f'file://{self.report_path}')
    
    def run(self, skip_scrape: bool = False, notify: bool = False) -> bool:
        """Run the complete pipeline."""
        self.start_time = datetime.now()
        
        print("\n" + "="*60)
        print(">>> LINKEDIN JOB ANALYSIS PIPELINE")
        print(f"    Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # Step 1: Scrape (optional)
        if not skip_scrape:
            if not self.step_scrape():
                print("\n[!] Scraping failed, but continuing with existing data...")
        else:
            print("\n[>>] Skipping scrape step (using existing data)")
        
        # Step 2: Analyze
        if not self.step_analyze():
            print("\n[X] Analysis failed. Pipeline stopped.")
            return False
        
        # Step 2.5: Visualize
        self.step_visualize()
        
        # Step 3: Report
        if not self.step_report():
            print("\n[!] Report generation failed")
        
        # Step 4: Cleanup
        self.step_cleanup()
        
        # Calculate duration
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # Summary
        print("\n" + "="*60)
        print(">>> PIPELINE SUMMARY")
        print("="*60)
        print(f"  Duration: {duration.total_seconds():.1f} seconds")
        print(f"  Scrape:   {'[OK]' if self.results['scrape'] else '[SKIP]'}")
        print(f"  Analyze:  {'[OK]' if self.results['analyze'] else '[FAIL]'}")
        print(f"  Report:   {'[OK]' if self.results['report'] else '[FAIL]'}")
        
        if self.report_path:
            print(f"\n  Report: {self.report_path}")
        
        print("="*60 + "\n")
        
        # Send notification if requested
        if notify:
            self.send_email_notification()
        
        # Open report
        self.open_report()
        
        return True


def main():
    parser = argparse.ArgumentParser(description='Run LinkedIn Job Analysis Pipeline')
    parser.add_argument('--skip-scrape', action='store_true',
                       help='Skip scraping, use existing data')
    parser.add_argument('--notify', action='store_true',
                       help='Send email notification when complete')
    parser.add_argument('--no-open', action='store_true',
                       help='Do not auto-open report in browser')
    
    args = parser.parse_args()
    
    runner = PipelineRunner()
    
    if args.no_open:
        runner.config['report'] = runner.config.get('report', {})
        runner.config['report']['auto_open'] = False
    
    success = runner.run(skip_scrape=args.skip_scrape, notify=args.notify)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
