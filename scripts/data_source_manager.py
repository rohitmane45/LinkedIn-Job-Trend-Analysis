"""
Data Source Manager
===================
Choose between real-time API data or locally stored data.

Usage:
    python data_source_manager.py                    # Interactive mode
    python data_source_manager.py --realtime         # Force real-time API
    python data_source_manager.py --local            # Force local data
    python data_source_manager.py --status           # Show data status
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
from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Optional
import argparse

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / 'scripts'
DATA_DIR = PROJECT_ROOT / 'data' / 'raw'
CONFIG_DIR = PROJECT_ROOT / 'config'

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)


class DataSourceManager:
    """Manage data source selection and fetching."""
    
    def __init__(self):
        self.local_files = []
        self.latest_file = None
        self.latest_file_age = None
        self.job_count = 0
        self._scan_local_data()
    
    def _scan_local_data(self):
        """Scan for locally stored data files."""
        csv_files = list(DATA_DIR.glob('jobs_*.csv'))
        json_files = list(DATA_DIR.glob('jobs_*.json'))
        
        self.local_files = csv_files + json_files
        
        if self.local_files:
            self.latest_file = max(self.local_files, key=lambda f: f.stat().st_mtime)
            file_time = datetime.fromtimestamp(self.latest_file.stat().st_mtime)
            self.latest_file_age = datetime.now() - file_time
            
            # Count jobs in latest file
            try:
                import pandas as pd
                if self.latest_file.suffix == '.csv':
                    df = pd.read_csv(self.latest_file)
                    self.job_count = len(df)
                else:
                    with open(self.latest_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.job_count = len(data) if isinstance(data, list) else len(data.get('jobs', []))
            except:
                self.job_count = 0
    
    def get_data_status(self) -> Dict:
        """Get current data status."""
        status = {
            'has_local_data': len(self.local_files) > 0,
            'local_file_count': len(self.local_files),
            'latest_file': str(self.latest_file.name) if self.latest_file else None,
            'latest_file_path': str(self.latest_file) if self.latest_file else None,
            'job_count': self.job_count,
            'data_age': None,
            'data_age_hours': None,
            'is_stale': False
        }
        
        if self.latest_file_age:
            hours = self.latest_file_age.total_seconds() / 3600
            days = self.latest_file_age.days
            
            if days > 0:
                status['data_age'] = f"{days} day(s) ago"
            elif hours > 1:
                status['data_age'] = f"{int(hours)} hour(s) ago"
            else:
                minutes = int(self.latest_file_age.total_seconds() / 60)
                status['data_age'] = f"{minutes} minute(s) ago"
            
            status['data_age_hours'] = hours
            status['is_stale'] = hours > 24  # Consider stale if > 24 hours
        
        return status
    
    def print_status(self):
        """Print data status in a nice format."""
        status = self.get_data_status()
        
        print("\n" + "=" * 60)
        print("  DATA SOURCE STATUS")
        print("=" * 60)
        
        if status['has_local_data']:
            print(f"\n  [OK] Local data available")
            print(f"       File: {status['latest_file']}")
            print(f"       Jobs: {status['job_count']}")
            print(f"       Age:  {status['data_age']}")
            
            if status['is_stale']:
                print(f"\n  [!] Data is STALE (more than 24 hours old)")
                print(f"      Consider fetching fresh data from API")
            else:
                print(f"\n  [OK] Data is FRESH")
        else:
            print(f"\n  [X] No local data found")
            print(f"      You need to fetch data from API first")
        
        print("\n" + "=" * 60)
    
    def ask_data_source(self) -> str:
        """Ask user to choose data source."""
        status = self.get_data_status()
        
        print("\n" + "=" * 60)
        print("  SELECT DATA SOURCE")
        print("=" * 60)
        
        print("\n  Options:")
        print("  -" * 30)
        
        # Option 1: Real-time API
        print("\n  [1] REAL-TIME (Fetch from API)")
        print("      - Get fresh job listings from Adzuna API")
        print("      - Takes 1-2 minutes")
        print("      - Requires internet connection")
        
        # Option 2: Local data
        print("\n  [2] LOCAL (Use stored data)")
        if status['has_local_data']:
            print(f"      - {status['job_count']} jobs available")
            print(f"      - Last updated: {status['data_age']}")
            if status['is_stale']:
                print(f"      - [WARN] Data is stale (>24 hours)")
        else:
            print(f"      - [X] No local data available")
            print(f"      - You must choose Real-time first")
        
        print("\n  -" * 30)
        
        # Get choice
        while True:
            choice = input("\n  Enter choice (1 for Real-time, 2 for Local): ").strip()
            
            if choice == '1':
                return 'realtime'
            elif choice == '2':
                if status['has_local_data']:
                    return 'local'
                else:
                    print("  [X] No local data available. Please choose Real-time (1)")
            else:
                print("  [X] Invalid choice. Enter 1 or 2")
    
    def fetch_realtime_data(self) -> Tuple[bool, Optional[str]]:
        """Fetch data from real-time API."""
        print("\n" + "-" * 50)
        print("  FETCHING REAL-TIME DATA FROM API...")
        print("-" * 50 + "\n")
        
        # Run scraper
        scraper_path = SCRIPTS_DIR / 'scraper_india.py'
        
        if not scraper_path.exists():
            print("  [X] Scraper not found!")
            return False, None
        
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        try:
            result = subprocess.run(
                [sys.executable, str(scraper_path)],
                env=env,
                capture_output=False
            )
            
            # Refresh local data info
            self._scan_local_data()
            
            if self.latest_file:
                print(f"\n  [OK] Data fetched successfully!")
                print(f"       File: {self.latest_file.name}")
                print(f"       Jobs: {self.job_count}")
                return True, str(self.latest_file)
            else:
                print("  [X] Scraping completed but no data file found")
                return False, None
                
        except Exception as e:
            print(f"  [X] Error fetching data: {e}")
            return False, None
    
    def use_local_data(self) -> Tuple[bool, Optional[str]]:
        """Use locally stored data."""
        if not self.latest_file:
            print("  [X] No local data available")
            return False, None
        
        print(f"\n  [OK] Using local data:")
        print(f"       File: {self.latest_file.name}")
        print(f"       Jobs: {self.job_count}")
        print(f"       Age:  {self.get_data_status()['data_age']}")
        
        return True, str(self.latest_file)
    
    def get_data(self, source: str = 'ask') -> Tuple[bool, Optional[str]]:
        """
        Get data from specified source.
        
        Args:
            source: 'realtime', 'local', or 'ask' (interactive)
        
        Returns:
            (success, file_path)
        """
        if source == 'ask':
            source = self.ask_data_source()
        
        if source == 'realtime':
            return self.fetch_realtime_data()
        else:
            return self.use_local_data()


def main():
    parser = argparse.ArgumentParser(description='Data Source Manager')
    parser.add_argument('--realtime', action='store_true', help='Fetch real-time data from API')
    parser.add_argument('--local', action='store_true', help='Use locally stored data')
    parser.add_argument('--status', action='store_true', help='Show data status')
    parser.add_argument('--ask', action='store_true', help='Interactive mode (default)')
    
    args = parser.parse_args()
    
    manager = DataSourceManager()
    
    if args.status:
        manager.print_status()
    elif args.realtime:
        success, path = manager.get_data('realtime')
        if success:
            print(f"\n  [OK] Data ready: {path}")
    elif args.local:
        success, path = manager.get_data('local')
        if success:
            print(f"\n  [OK] Data ready: {path}")
    else:
        # Default: interactive mode
        manager.print_status()
        success, path = manager.get_data('ask')
        if success:
            print(f"\n  [OK] Data ready for analysis!")


if __name__ == "__main__":
    main()
