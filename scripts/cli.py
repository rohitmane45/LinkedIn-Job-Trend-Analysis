"""
LinkedIn Job Analysis CLI
=========================
Unified command-line interface for all features.

Usage:
    python cli.py scrape              # Run scraper
    python cli.py analyze             # Analyze data
    python cli.py report              # Generate report
    python cli.py dashboard           # Start dashboard
    python cli.py export --excel      # Export to Excel
    python cli.py alerts --check      # Check job alerts
    python cli.py match               # Match resume to jobs
    python cli.py predict "Title"     # Predict salary
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess
from pathlib import Path
import argparse

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / 'scripts'


def run_script(script_name: str, args: list = None):
    """Run a script with arguments."""
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
        
        subprocess.run(cmd, env=env)
        return True
    except Exception as e:
        print(f"[X] Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='LinkedIn Job Analysis - Unified CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  scrape          Run the job scraper (real-time API)
  analyze         Analyze scraped data
  report          Generate report
  visualize       Create visualizations
  dashboard       Start web dashboard
  api             Start API server
  export          Export data (--excel, --pdf, --csv)
  alerts          Job alerts (--check, --create)
  match           Match resume to jobs
  predict         Predict salary
  trends          Track market trends
  insights        Generate market insights
  cleanup         Clean up old files
  pipeline        Run full pipeline
  flow            Master flow (asks data source)
  data            Data source manager (--status, --realtime, --local)

Examples:
  python cli.py flow                          # Interactive flow (asks data source)
  python cli.py flow --realtime               # Flow with fresh API data
  python cli.py flow --local                  # Flow with local data
  python cli.py data --status                 # Check data status
  python cli.py scrape                        # Fetch fresh data from API
  python cli.py analyze                       # Analyze existing data
        """
    )
    
    parser.add_argument('command', nargs='?', help='Command to run')
    parser.add_argument('positional', nargs='*', help='Positional arguments')
    parser.add_argument('--excel', action='store_true', help='Export to Excel')
    parser.add_argument('--pdf', action='store_true', help='Export to PDF')
    parser.add_argument('--csv', action='store_true', help='Export to CSV')
    parser.add_argument('--check', action='store_true', help='Check alerts')
    parser.add_argument('--create', action='store_true', help='Create new')
    parser.add_argument('--profile', action='store_true', help='User profile')
    parser.add_argument('--gaps', action='store_true', help='Skill gaps')
    parser.add_argument('--location', type=str, help='Location')
    parser.add_argument('--exp', type=int, help='Experience years')
    parser.add_argument('--format', type=str, default='html', help='Report format')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    parser.add_argument('--skip-scrape', action='store_true', help='Skip scraping')
    parser.add_argument('--realtime', action='store_true', help='Use real-time API data')
    parser.add_argument('--local', action='store_true', help='Use local stored data')
    parser.add_argument('--status', action='store_true', help='Show status')
    parser.add_argument('--quick', action='store_true', help='Quick mode')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    command = args.command.lower()
    
    # Command mappings
    commands = {
        'scrape': ('scraper_india.py', []),
        'analyze': ('analyze_jobs.py', []),
        'report': ('generate_report.py', ['--format', args.format]),
        'visualize': ('visualize_data.py', []),
        'dashboard': ('dashboard.py', []),
        'api': ('api_server.py', []),
        'cleanup': ('cleanup_project.py', ['--dry-run'] if args.dry_run else []),
        'pipeline': ('run_pipeline.py', ['--skip-scrape'] if args.skip_scrape else []),
        'trends': ('trend_tracker.py', ['--report']),
        'insights': ('market_insights.py', ['--generate']),
        'scheduler': ('scheduler.py', ['--start']),
        'db': ('database.py', ['--stats']),
    }
    
    if command in commands:
        script, default_args = commands[command]
        run_script(script, default_args)
    
    elif command == 'flow':
        flow_args = []
        if args.realtime:
            flow_args.append('--realtime')
        elif args.local:
            flow_args.append('--local')
        if args.quick:
            flow_args.append('--quick')
        run_script('master_flow.py', flow_args)
    
    elif command == 'data':
        data_args = []
        if args.status:
            data_args.append('--status')
        elif args.realtime:
            data_args.append('--realtime')
        elif args.local:
            data_args.append('--local')
        else:
            data_args.append('--status')
        run_script('data_source_manager.py', data_args)
    
    elif command == 'export':
        export_args = []
        if args.excel:
            export_args.append('--excel')
        elif args.pdf:
            export_args.append('--pdf')
        elif args.csv:
            export_args.append('--csv')
        else:
            export_args.append('--all')
        run_script('export_manager.py', export_args)
    
    elif command == 'alerts':
        alert_args = []
        if args.check:
            alert_args.append('--check')
        elif args.create:
            alert_args.append('--add-alert')
        else:
            alert_args.append('--list-alerts')
        run_script('job_alerts.py', alert_args)
    
    elif command == 'match':
        match_args = []
        if args.profile:
            match_args.append('--profile')
        elif args.gaps:
            match_args.append('--gaps')
        else:
            match_args.append('--match')
        run_script('resume_matcher.py', match_args)
    
    elif command == 'predict':
        predict_args = []
        if args.positional:
            predict_args.extend(['--predict', ' '.join(args.positional)])
        if args.location:
            predict_args.extend(['--location', args.location])
        if args.exp:
            predict_args.extend(['--exp', str(args.exp)])
        
        if predict_args:
            run_script('salary_predictor.py', predict_args)
        else:
            run_script('salary_predictor.py', ['--analyze'])
    
    elif command == 'notify':
        run_script('notification_manager.py', ['--send-report'])
    
    elif command == 'help':
        parser.print_help()
    
    else:
        print(f"[X] Unknown command: {command}")
        print("Run 'python cli.py help' for available commands")


if __name__ == "__main__":
    main()
