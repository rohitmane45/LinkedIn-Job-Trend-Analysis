"""
Pipeline Scheduler
==================
Schedule automatic runs of the job analysis pipeline.

Usage:
    python scheduler.py --start          # Start scheduler
    python scheduler.py --run-now        # Run pipeline immediately
    python scheduler.py --status         # Check scheduler status
"""

import schedule
import time
import subprocess
import sys
import os

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from datetime import datetime
import yaml
import argparse
import threading
import signal

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / 'scripts'
CONFIG_FILE = PROJECT_ROOT / 'config' / 'settings.yaml'
LOG_FILE = PROJECT_ROOT / 'logs' / 'scheduler.log'


class PipelineScheduler:
    """Schedule and manage pipeline runs."""
    
    def __init__(self):
        self.config = self._load_config()
        self.running = False
        self.last_run = None
        self.next_run = None
        
        # Ensure logs directory exists
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> dict:
        """Load configuration from YAML file."""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def _log(self, message: str):
        """Log message to file and console."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    
    def run_pipeline(self):
        """Run the pipeline."""
        self._log("🚀 Starting scheduled pipeline run...")
        self.last_run = datetime.now()
        
        pipeline_script = SCRIPTS_DIR / 'run_pipeline.py'
        
        if not pipeline_script.exists():
            self._log("❌ Pipeline script not found!")
            return
        
        try:
            result = subprocess.run(
                [sys.executable, str(pipeline_script), '--notify'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self._log("✅ Pipeline completed successfully")
            else:
                self._log(f"❌ Pipeline failed: {result.stderr}")
                
        except Exception as e:
            self._log(f"❌ Error running pipeline: {e}")
    
    def setup_schedule(self):
        """Setup the schedule based on config."""
        scheduler_config = self.config.get('scheduler', {})
        
        if not scheduler_config.get('enabled', False):
            self._log("⚠️ Scheduler is disabled in config")
            return False
        
        run_time = scheduler_config.get('run_time', '09:00')
        frequency = scheduler_config.get('frequency', 'daily')
        
        if frequency == 'daily':
            schedule.every().day.at(run_time).do(self.run_pipeline)
            self._log(f"📅 Scheduled daily run at {run_time}")
            
        elif frequency == 'weekly':
            weekly_day = scheduler_config.get('weekly_day', 'monday')
            getattr(schedule.every(), weekly_day).at(run_time).do(self.run_pipeline)
            self._log(f"📅 Scheduled weekly run on {weekly_day} at {run_time}")
            
        elif frequency == 'hourly':
            schedule.every().hour.do(self.run_pipeline)
            self._log("📅 Scheduled hourly run")
        
        return True
    
    def start(self):
        """Start the scheduler."""
        self._log("="*50)
        self._log("🕐 LinkedIn Job Analysis Scheduler Started")
        self._log("="*50)
        
        if not self.setup_schedule():
            return
        
        self.running = True
        
        # Handle graceful shutdown
        def signal_handler(signum, frame):
            self._log("\n🛑 Stopping scheduler...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        self._log("Press Ctrl+C to stop\n")
        
        while self.running:
            schedule.run_pending()
            
            # Show next run time
            next_job = schedule.next_run()
            if next_job != self.next_run:
                self.next_run = next_job
                if next_job:
                    self._log(f"⏰ Next run: {next_job.strftime('%Y-%m-%d %H:%M:%S')}")
            
            time.sleep(60)  # Check every minute
        
        self._log("👋 Scheduler stopped")
    
    def get_status(self) -> dict:
        """Get scheduler status."""
        scheduler_config = self.config.get('scheduler', {})
        
        status = {
            'enabled': scheduler_config.get('enabled', False),
            'frequency': scheduler_config.get('frequency', 'daily'),
            'run_time': scheduler_config.get('run_time', '09:00'),
            'last_run': None,
            'next_run': None,
            'log_file': str(LOG_FILE)
        }
        
        # Check log for last run
        if LOG_FILE.exists():
            with open(LOG_FILE, 'r') as f:
                lines = f.readlines()
                for line in reversed(lines):
                    if 'Starting scheduled pipeline' in line:
                        status['last_run'] = line.split(']')[0].strip('[')
                        break
        
        return status
    
    def show_status(self):
        """Display scheduler status."""
        status = self.get_status()
        
        print("\n" + "="*50)
        print("📊 SCHEDULER STATUS")
        print("="*50)
        print(f"  Enabled:    {'✅ Yes' if status['enabled'] else '❌ No'}")
        print(f"  Frequency:  {status['frequency']}")
        print(f"  Run Time:   {status['run_time']}")
        print(f"  Last Run:   {status['last_run'] or 'Never'}")
        print(f"  Log File:   {status['log_file']}")
        print("="*50 + "\n")


def main():
    parser = argparse.ArgumentParser(description='Schedule LinkedIn Job Analysis Pipeline')
    parser.add_argument('--start', action='store_true', help='Start the scheduler')
    parser.add_argument('--run-now', action='store_true', help='Run pipeline immediately')
    parser.add_argument('--status', action='store_true', help='Show scheduler status')
    
    args = parser.parse_args()
    
    scheduler = PipelineScheduler()
    
    if args.status:
        scheduler.show_status()
    elif args.run_now:
        scheduler.run_pipeline()
    elif args.start:
        scheduler.start()
    else:
        parser.print_help()
        print("\n💡 Examples:")
        print("  python scheduler.py --start      # Start scheduler")
        print("  python scheduler.py --run-now    # Run now")
        print("  python scheduler.py --status     # Check status")


if __name__ == "__main__":
    main()
