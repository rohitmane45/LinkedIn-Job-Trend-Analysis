"""
Indian Cities Job Scraper
=========================
Collect job data for major Indian cities like Bangalore, Pune, Mumbai, etc.

For REAL-TIME data, get FREE API keys from:
- Adzuna: https://developer.adzuna.com/

Usage:
    python scraper_india.py --mode sample
    python scraper_india.py --mode realtime --app-id YOUR_ID --app-key YOUR_KEY
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scraper_v2 import EnhancedJobScraper, INDIAN_CITIES

def main():
    parser = argparse.ArgumentParser(description='Scrape jobs for Indian cities')
    parser.add_argument('--mode', choices=['sample', 'realtime', 'hybrid'], 
                        default='sample', help='Data collection mode')
    parser.add_argument('--cities', nargs='+', 
                        default=['bangalore', 'pune', 'mumbai', 'hyderabad', 'delhi'],
                        help='Cities to scrape')
    parser.add_argument('--app-id', help='Adzuna App ID for real-time data')
    parser.add_argument('--app-key', help='Adzuna App Key for real-time data')
    parser.add_argument('--num-jobs', type=int, default=500, help='Number of sample jobs')
    
    args = parser.parse_args()
    
    print("="*60)
    print("🇮🇳 Indian Cities Job Data Collection")
    print("="*60)
    print(f"\nCities: {', '.join(args.cities)}")
    print(f"Mode: {args.mode}")
    
    if args.mode == 'realtime' and (not args.app_id or not args.app_key):
        print("\n⚠️  For real-time data, you need Adzuna API credentials!")
        print("Get FREE keys at: https://developer.adzuna.com/")
        print("Falling back to sample mode...\n")
        args.mode = 'sample'
    
    scraper = EnhancedJobScraper(output_dir="../data/raw")
    
    df = scraper.run_india(
        cities=args.cities,
        mode=args.mode,
        adzuna_app_id=args.app_id,
        adzuna_app_key=args.app_key,
        num_jobs=args.num_jobs
    )
    
    print(f"\n✅ Data collection complete!")
    print(f"\n📊 Summary by City:")
    print(df['city'].value_counts().to_string())
    
    print(f"\n💼 Top Job Titles:")
    print(df['title'].value_counts().head(10).to_string())
    
    print(f"\n🏢 Top Companies:")
    print(df['company'].value_counts().head(10).to_string())
    
    return df

if __name__ == "__main__":
    main()
