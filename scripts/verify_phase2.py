"""
Quick verification script for Phase 2 data collection.
Run this after scraper_v2.py to verify the output.
"""

import pandas as pd
from pathlib import Path
import glob

def verify_data():
    """Verify Phase 2 data collection results."""
    data_dir = Path("../data/raw")
    
    print("=" * 60)
    print("Phase 2 Data Verification")
    print("=" * 60)
    
    # Find the most recent CSV file
    csv_files = list(data_dir.glob("jobs_raw_*.csv"))
    
    if not csv_files:
        print("❌ No data files found! Run scraper_v2.py first.")
        return
    
    # Get most recent file
    latest_csv = max(csv_files, key=lambda x: x.stat().st_mtime)
    print(f"\n✅ Found data file: {latest_csv.name}")
    
    # Load and analyze
    df = pd.read_csv(latest_csv)
    
    print(f"\n📊 Dataset Overview:")
    print(f"   - Total records: {len(df)}")
    print(f"   - Columns: {list(df.columns)}")
    
    print(f"\n📋 Column Details:")
    for col in df.columns:
        non_null = df[col].notna().sum()
        print(f"   - {col}: {non_null}/{len(df)} non-null values")
    
    print(f"\n🏢 Top 10 Companies:")
    print(df['company'].value_counts().head(10).to_string())
    
    print(f"\n💼 Top 10 Job Titles:")
    print(df['title'].value_counts().head(10).to_string())
    
    print(f"\n📍 Top 10 Cities:")
    print(df['city'].value_counts().head(10).to_string())
    
    # Check skills column
    if 'skills' in df.columns:
        print(f"\n🔧 Skills Sample (first 3 rows):")
        for i, skills in enumerate(df['skills'].head(3)):
            print(f"   Row {i+1}: {skills[:100]}..." if len(str(skills)) > 100 else f"   Row {i+1}: {skills}")
    
    print(f"\n✅ Phase 2 verification complete!")
    print(f"   Data is ready for Phase 3 (preprocessing)")
    
    return df

if __name__ == "__main__":
    verify_data()
