"""
Database Module
===============
SQLite database for storing and querying job data.

Usage:
    python database.py --init              # Initialize database
    python database.py --import-csv FILE   # Import CSV data
    python database.py --stats             # Show database stats
    python database.py --query "python"    # Search jobs
"""

import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import argparse

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DB_FILE = PROJECT_ROOT / 'data' / 'jobs.db'
DATA_DIR = PROJECT_ROOT / 'data' / 'raw'

# Ensure directory exists
DB_FILE.parent.mkdir(parents=True, exist_ok=True)


class JobDatabase:
    """SQLite database for job listings."""
    
    def __init__(self, db_path: str = None):
        self.db_path = Path(db_path) if db_path else DB_FILE
        self.conn = None
    
    def connect(self):
        """Connect to database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def init_database(self):
        """Initialize database tables."""
        cursor = self.conn.cursor()
        
        # Jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE,
                title TEXT,
                company TEXT,
                location TEXT,
                description TEXT,
                salary TEXT,
                job_type TEXT,
                experience_level TEXT,
                posted_date TEXT,
                url TEXT,
                source TEXT DEFAULT 'linkedin',
                scraped_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Skills table (extracted from jobs)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                skill TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs(id)
            )
        ''')
        
        # Snapshots table (for trend tracking)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date TEXT,
                total_jobs INTEGER,
                top_skills TEXT,
                top_companies TEXT,
                top_locations TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Alerts matches table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_name TEXT,
                job_id INTEGER,
                matched_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES jobs(id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_scraped ON jobs(scraped_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_skills_skill ON job_skills(skill)')
        
        self.conn.commit()
        print("[OK] Database initialized successfully")
    
    def insert_job(self, job: Dict) -> int:
        """Insert a single job into database."""
        cursor = self.conn.cursor()
        
        # Generate job_id if not present
        job_id = job.get('job_id') or f"{job.get('company', '')}_{job.get('title', '')}_{datetime.now().timestamp()}"
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO jobs 
                (job_id, title, company, location, description, salary, job_type, 
                 experience_level, posted_date, url, source, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_id,
                job.get('title'),
                job.get('company'),
                job.get('location'),
                job.get('description'),
                job.get('salary'),
                job.get('job_type'),
                job.get('experience_level'),
                job.get('posted_date'),
                job.get('url'),
                job.get('source', 'linkedin'),
                job.get('scraped_at', datetime.now().isoformat())
            ))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return -1
    
    def insert_jobs(self, jobs: List[Dict]) -> int:
        """Insert multiple jobs into database."""
        inserted = 0
        for job in jobs:
            result = self.insert_job(job)
            if result > 0:
                inserted += 1
        print(f"[OK] Inserted {inserted}/{len(jobs)} jobs")
        return inserted
    
    def search_jobs(self, query: str, limit: int = 50) -> List[Dict]:
        """Search jobs by keyword."""
        cursor = self.conn.cursor()
        
        search_term = f"%{query}%"
        cursor.execute('''
            SELECT * FROM jobs 
            WHERE title LIKE ? OR company LIKE ? OR description LIKE ? OR location LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (search_term, search_term, search_term, search_term, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_jobs_by_company(self, company: str, limit: int = 50) -> List[Dict]:
        """Get jobs by company name."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM jobs WHERE company LIKE ? ORDER BY created_at DESC LIMIT ?
        ''', (f"%{company}%", limit))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_jobs_by_location(self, location: str, limit: int = 50) -> List[Dict]:
        """Get jobs by location."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM jobs WHERE location LIKE ? ORDER BY created_at DESC LIMIT ?
        ''', (f"%{location}%", limit))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_jobs(self, days: int = 7, limit: int = 100) -> List[Dict]:
        """Get jobs from last N days."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM jobs 
            WHERE date(created_at) >= date('now', ?)
            ORDER BY created_at DESC
            LIMIT ?
        ''', (f"-{days} days", limit))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Total jobs
        cursor.execute('SELECT COUNT(*) FROM jobs')
        stats['total_jobs'] = cursor.fetchone()[0]
        
        # Unique companies
        cursor.execute('SELECT COUNT(DISTINCT company) FROM jobs')
        stats['unique_companies'] = cursor.fetchone()[0]
        
        # Unique locations
        cursor.execute('SELECT COUNT(DISTINCT location) FROM jobs')
        stats['unique_locations'] = cursor.fetchone()[0]
        
        # Jobs by date
        cursor.execute('''
            SELECT date(created_at) as date, COUNT(*) as count 
            FROM jobs 
            GROUP BY date(created_at) 
            ORDER BY date DESC 
            LIMIT 7
        ''')
        stats['jobs_by_date'] = [dict(row) for row in cursor.fetchall()]
        
        # Top companies
        cursor.execute('''
            SELECT company, COUNT(*) as count 
            FROM jobs 
            GROUP BY company 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        stats['top_companies'] = [dict(row) for row in cursor.fetchall()]
        
        # Top locations
        cursor.execute('''
            SELECT location, COUNT(*) as count 
            FROM jobs 
            GROUP BY location 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        stats['top_locations'] = [dict(row) for row in cursor.fetchall()]
        
        return stats
    
    def export_to_json(self, output_path: str = None) -> str:
        """Export all jobs to JSON."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM jobs ORDER BY created_at DESC')
        jobs = [dict(row) for row in cursor.fetchall()]
        
        if not output_path:
            output_path = PROJECT_ROOT / 'data' / 'exports' / f"jobs_export_{datetime.now().strftime('%Y%m%d')}.json"
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Exported {len(jobs)} jobs to {output_path}")
        return str(output_path)
    
    def save_snapshot(self):
        """Save current stats as a snapshot for trend tracking."""
        stats = self.get_stats()
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO snapshots (snapshot_date, total_jobs, top_skills, top_companies, top_locations)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            datetime.now().strftime('%Y-%m-%d'),
            stats['total_jobs'],
            json.dumps([]),  # Skills would come from analysis
            json.dumps(stats['top_companies']),
            json.dumps(stats['top_locations'])
        ))
        self.conn.commit()
        print(f"[OK] Snapshot saved for {datetime.now().strftime('%Y-%m-%d')}")


def import_csv_to_db(csv_path: str):
    """Import CSV file into database."""
    try:
        import pandas as pd
    except ImportError:
        print("[X] pandas required: pip install pandas")
        return
    
    df = pd.read_csv(csv_path)
    jobs = df.to_dict('records')
    
    with JobDatabase() as db:
        db.init_database()
        db.insert_jobs(jobs)


def import_latest_data():
    """Import the latest data file into database."""
    csv_files = list(DATA_DIR.glob('jobs_*.csv'))
    json_files = list(DATA_DIR.glob('jobs_*.json'))
    
    all_files = csv_files + json_files
    if not all_files:
        print("[X] No data files found")
        return
    
    latest = max(all_files, key=lambda f: f.stat().st_mtime)
    print(f"[i] Importing: {latest.name}")
    
    if latest.suffix == '.csv':
        import_csv_to_db(str(latest))
    else:
        with open(latest, 'r', encoding='utf-8') as f:
            data = json.load(f)
            jobs = data if isinstance(data, list) else data.get('jobs', [])
        
        with JobDatabase() as db:
            db.init_database()
            db.insert_jobs(jobs)


def main():
    parser = argparse.ArgumentParser(description='Job Database Manager')
    parser.add_argument('--init', action='store_true', help='Initialize database')
    parser.add_argument('--import-csv', type=str, metavar='FILE', help='Import CSV file')
    parser.add_argument('--import-latest', action='store_true', help='Import latest data file')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--query', type=str, metavar='KEYWORD', help='Search jobs')
    parser.add_argument('--export', action='store_true', help='Export to JSON')
    parser.add_argument('--snapshot', action='store_true', help='Save snapshot for trends')
    
    args = parser.parse_args()
    
    if args.init:
        with JobDatabase() as db:
            db.init_database()
    
    elif args.import_csv:
        import_csv_to_db(args.import_csv)
    
    elif args.import_latest:
        import_latest_data()
    
    elif args.stats:
        with JobDatabase() as db:
            stats = db.get_stats()
            print("\n" + "="*60)
            print("DATABASE STATISTICS")
            print("="*60)
            print(f"  Total Jobs:       {stats['total_jobs']}")
            print(f"  Unique Companies: {stats['unique_companies']}")
            print(f"  Unique Locations: {stats['unique_locations']}")
            print("\n  Top Companies:")
            for c in stats['top_companies'][:5]:
                print(f"    - {c['company']}: {c['count']} jobs")
            print("\n  Top Locations:")
            for l in stats['top_locations'][:5]:
                print(f"    - {l['location']}: {l['count']} jobs")
            print("="*60)
    
    elif args.query:
        with JobDatabase() as db:
            jobs = db.search_jobs(args.query)
            print(f"\n[i] Found {len(jobs)} jobs matching '{args.query}':\n")
            for job in jobs[:10]:
                print(f"  [{job['id']}] {job['title']}")
                print(f"       {job['company']} - {job['location']}")
    
    elif args.export:
        with JobDatabase() as db:
            db.export_to_json()
    
    elif args.snapshot:
        with JobDatabase() as db:
            db.save_snapshot()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
