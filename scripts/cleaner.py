"""
Data Cleaning Script - Phase 3
==============================
Clean and standardize scraped job data:
- Standardize job titles
- Parse and extract skills from descriptions
- Clean and normalize location data
- Remove duplicates and handle missing values

Usage:
    python cleaner.py --input ../data/raw/jobs_latest.csv --output ../data/processed/
"""

import pandas as pd
import re
import argparse
from pathlib import Path
from datetime import datetime
from collections import Counter
import json

class JobDataCleaner:
    """Clean and standardize job data."""
    
    def __init__(self):
        # Master skills dictionary - common tech skills
        self.skills_dict = {
            # Programming Languages
            'python': ['python', 'python3', 'py'],
            'javascript': ['javascript', 'js', 'ecmascript'],
            'java': ['java', 'j2ee', 'jvm'],
            'sql': ['sql', 'mysql', 'postgresql', 'postgres', 'sqlite', 'tsql', 'plsql'],
            'r': ['r programming', 'r language', 'rstudio'],
            'c++': ['c++', 'cpp', 'c plus plus'],
            'c#': ['c#', 'csharp', 'c sharp'],
            'typescript': ['typescript', 'ts'],
            'scala': ['scala'],
            'go': ['golang', 'go language'],
            'rust': ['rust'],
            'php': ['php'],
            'ruby': ['ruby', 'rails', 'ruby on rails'],
            'swift': ['swift'],
            'kotlin': ['kotlin'],
            
            # Data Science & ML
            'machine learning': ['machine learning', 'ml', 'deep learning', 'dl'],
            'data science': ['data science', 'data scientist'],
            'artificial intelligence': ['artificial intelligence', 'ai', 'generative ai', 'genai'],
            'nlp': ['nlp', 'natural language processing', 'text mining'],
            'computer vision': ['computer vision', 'cv', 'image processing'],
            'tensorflow': ['tensorflow', 'tf'],
            'pytorch': ['pytorch', 'torch'],
            'scikit-learn': ['scikit-learn', 'sklearn', 'scikit learn'],
            'pandas': ['pandas'],
            'numpy': ['numpy'],
            'keras': ['keras'],
            
            # Cloud & DevOps
            'aws': ['aws', 'amazon web services', 'ec2', 's3', 'lambda'],
            'azure': ['azure', 'microsoft azure'],
            'gcp': ['gcp', 'google cloud', 'google cloud platform'],
            'docker': ['docker', 'containerization'],
            'kubernetes': ['kubernetes', 'k8s'],
            'terraform': ['terraform'],
            'jenkins': ['jenkins'],
            'ci/cd': ['ci/cd', 'cicd', 'continuous integration', 'continuous deployment'],
            'git': ['git', 'github', 'gitlab', 'bitbucket'],
            'linux': ['linux', 'unix', 'ubuntu', 'centos'],
            
            # Databases
            'mongodb': ['mongodb', 'mongo'],
            'redis': ['redis'],
            'elasticsearch': ['elasticsearch', 'elastic search', 'elk'],
            'cassandra': ['cassandra'],
            'dynamodb': ['dynamodb'],
            'oracle': ['oracle', 'oracle db'],
            
            # Big Data
            'spark': ['spark', 'apache spark', 'pyspark'],
            'hadoop': ['hadoop', 'hdfs', 'hive'],
            'kafka': ['kafka', 'apache kafka'],
            'airflow': ['airflow', 'apache airflow'],
            'databricks': ['databricks'],
            'snowflake': ['snowflake'],
            
            # Web & Frameworks
            'react': ['react', 'reactjs', 'react.js'],
            'angular': ['angular', 'angularjs'],
            'vue': ['vue', 'vuejs', 'vue.js'],
            'node.js': ['node', 'nodejs', 'node.js'],
            'django': ['django'],
            'flask': ['flask'],
            'fastapi': ['fastapi', 'fast api'],
            'spring': ['spring', 'spring boot', 'springboot'],
            'rest api': ['rest', 'rest api', 'restful', 'api'],
            
            # BI & Visualization
            'tableau': ['tableau'],
            'power bi': ['power bi', 'powerbi'],
            'looker': ['looker'],
            'excel': ['excel', 'ms excel', 'microsoft excel', 'advanced excel'],
            
            # Soft Skills
            'agile': ['agile', 'scrum', 'kanban', 'jira'],
            'communication': ['communication', 'presentation'],
            'leadership': ['leadership', 'team lead', 'management'],
        }
        
        # Job title standardization mapping
        self.title_mapping = {
            # Data roles
            'data analyst': ['data analyst', 'business data analyst', 'sr data analyst', 
                           'junior data analyst', 'data analyst i', 'data analyst ii'],
            'data scientist': ['data scientist', 'sr data scientist', 'junior data scientist',
                              'data scientist i', 'data scientist ii', 'applied scientist'],
            'data engineer': ['data engineer', 'sr data engineer', 'big data engineer',
                             'data engineer i', 'data engineer ii', 'etl developer'],
            'ml engineer': ['machine learning engineer', 'ml engineer', 'mlops engineer',
                          'ai engineer', 'deep learning engineer'],
            'analytics engineer': ['analytics engineer', 'bi engineer'],
            
            # Software roles
            'software engineer': ['software engineer', 'software developer', 'sde',
                                 'software engineer i', 'software engineer ii', 'programmer'],
            'backend engineer': ['backend engineer', 'backend developer', 'server developer'],
            'frontend engineer': ['frontend engineer', 'frontend developer', 'ui developer'],
            'fullstack engineer': ['fullstack engineer', 'full stack developer', 'fullstack developer'],
            'devops engineer': ['devops engineer', 'site reliability engineer', 'sre', 
                               'platform engineer', 'infrastructure engineer'],
            
            # Management roles
            'engineering manager': ['engineering manager', 'tech lead', 'technical lead',
                                   'development manager', 'software manager'],
            'product manager': ['product manager', 'pm', 'product owner', 'technical pm'],
            'project manager': ['project manager', 'program manager', 'delivery manager'],
            
            # Analyst roles
            'business analyst': ['business analyst', 'ba', 'systems analyst'],
            'financial analyst': ['financial analyst', 'finance analyst'],
            'marketing analyst': ['marketing analyst', 'digital analyst'],
        }
        
        # Indian cities standardization
        self.city_mapping = {
            'bangalore': ['bangalore', 'bengaluru', 'blr', 'banglore'],
            'mumbai': ['mumbai', 'bombay'],
            'delhi': ['delhi', 'new delhi', 'delhi ncr', 'ncr'],
        'dl': 'deep learning',
        'artificial intelligence': 'ai',
        'natural language processing': 'nlp',
        'sklearn': 'scikit-learn',
        'sci-kit learn': 'scikit-learn',
        'tf': 'tensorflow',
        'tensor flow': 'tensorflow',
        'py torch': 'pytorch',
        
        # Tools
        'ms excel': 'excel',
        'microsoft excel': 'excel',
        'powerbi': 'power bi',
        'github actions': 'github',
        'gitlab ci': 'gitlab',
    }
    
    # City standardization
    CITY_MAPPING = {
        'nyc': 'New York',
        'new york city': 'New York',
        'ny': 'New York',
        'sf': 'San Francisco',
        'san fran': 'San Francisco',
        'la': 'Los Angeles',
        'l.a.': 'Los Angeles',
        'dc': 'Washington',
        'washington dc': 'Washington',
        'washington d.c.': 'Washington',
    }
    
    # State abbreviation mapping
    STATE_MAPPING = {
        'california': 'CA',
        'new york': 'NY',
        'texas': 'TX',
        'washington': 'WA',
        'massachusetts': 'MA',
        'illinois': 'IL',
        'colorado': 'CO',
        'georgia': 'GA',
        'florida': 'FL',
        'virginia': 'VA',
        'north carolina': 'NC',
        'pennsylvania': 'PA',
        'ohio': 'OH',
        'michigan': 'MI',
        'arizona': 'AZ',
        'oregon': 'OR',
        'minnesota': 'MN',
        'maryland': 'MD',
        'tennessee': 'TN',
        'indiana': 'IN',
    }
    
    def __init__(self, input_dir: str = "../data/raw", output_dir: str = "../data/processed"):
        """
        Initialize the cleaner.
        
        Args:
            input_dir: Directory containing raw data
            output_dir: Directory to save processed data
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def load_latest_raw_data(self) -> pd.DataFrame:
        """
        Load the most recent raw data file.
        
        Returns:
            DataFrame with raw job data
        """
        csv_files = list(self.input_dir.glob("jobs_raw_*.csv"))
        
        if not csv_files:
            raise FileNotFoundError("No raw data files found. Run scraper.py first.")
        
        latest_file = max(csv_files, key=lambda x: x.stat().st_mtime)
        logger.info(f"Loading data from: {latest_file}")
        
        df = pd.read_csv(latest_file)
        logger.info(f"Loaded {len(df)} records")
        
        return df
    
    def load_data(self, filepath: str) -> pd.DataFrame:
        """
        Load data from a specific file.
        
        Args:
            filepath: Path to the data file
            
        Returns:
            DataFrame with job data
        """
        filepath = Path(filepath)
        
        if filepath.suffix == '.csv':
            df = pd.read_csv(filepath)
        elif filepath.suffix == '.json':
            df = pd.read_json(filepath)
        else:
            raise ValueError(f"Unsupported file format: {filepath.suffix}")
        
        logger.info(f"Loaded {len(df)} records from {filepath}")
        return df
    
    def standardize_job_title(self, title: str) -> str:
        """
        Standardize job title to a consistent format.
        
        Args:
            title: Raw job title
            
        Returns:
            Standardized job title
        """
        if pd.isna(title):
            return "Unknown"
        
        title_lower = str(title).lower().strip()
        
        for pattern, standard_title in self.TITLE_MAPPING.items():
            if re.search(pattern, title_lower):
                return standard_title
        
        # If no match, return cleaned original title
        return title.strip().title()
    
    def normalize_skill(self, skill: str) -> str:
        """
        Normalize a skill name to standard format.
        
        Args:
            skill: Raw skill name
            
        Returns:
            Normalized skill name
        """
        if pd.isna(skill):
            return None
        
        skill_lower = str(skill).lower().strip()
        
        # Check if there's a mapping
        if skill_lower in self.SKILL_NORMALIZATION:
            return self.SKILL_NORMALIZATION[skill_lower]
        
        return skill_lower
    
    def parse_skills_column(self, skills_value) -> list:
        """
        Parse skills from various formats (string list, actual list, JSON string).
        
        Args:
            skills_value: Raw skills value from DataFrame
            
        Returns:
            List of normalized skills
        """
        if pd.isna(skills_value):
            return []
        
        # If already a list
        if isinstance(skills_value, list):
            skills = skills_value
        # If it's a string representation of a list
        elif isinstance(skills_value, str):
            try:
                # Try parsing as JSON
                skills = json.loads(skills_value.replace("'", '"'))
            except json.JSONDecodeError:
                # Try splitting by comma
                skills = [s.strip() for s in skills_value.split(',')]
        else:
            return []
        
        # Normalize each skill
        normalized = [self.normalize_skill(s) for s in skills if s]
        return [s for s in normalized if s]  # Remove None values
    
    def standardize_location(self, location: str) -> tuple:
        """
        Parse and standardize location into city and state.
        
        Args:
            location: Raw location string
            
        Returns:
            Tuple of (city, state)
        """
        if pd.isna(location):
            return ("Unknown", "Unknown")
        
        location = str(location).strip()
        
        # Handle "Remote" locations
        if 'remote' in location.lower():
            return ("Remote", "USA")
        
        # Try to split by comma
        parts = [p.strip() for p in location.split(',')]
        
        if len(parts) >= 2:
            city = parts[0]
            state = parts[1].strip().upper()[:2]  # Get state abbreviation
        else:
            city = parts[0]
            state = "Unknown"
        
        # Standardize city name
        city_lower = city.lower()
        if city_lower in self.CITY_MAPPING:
            city = self.CITY_MAPPING[city_lower]
        else:
            city = city.title()
        
        # Standardize state
        if len(state) > 2:
            state_lower = state.lower()
            if state_lower in self.STATE_MAPPING:
                state = self.STATE_MAPPING[state_lower]
        
        return (city, state)
    
    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate job postings.
        
        Args:
            df: DataFrame with job data
            
        Returns:
            DataFrame with duplicates removed
        """
        initial_count = len(df)
        
        # Remove duplicates based on key fields (avoid columns with lists)
        subset_cols = ['title_standardized', 'company']
        if 'city' in df.columns:
            subset_cols.append('city')
        elif 'city_standardized' in df.columns:
            subset_cols.append('city_standardized')
        
        df = df.drop_duplicates(subset=subset_cols, keep='first')
        
        removed = initial_count - len(df)
        logger.info(f"Removed {removed} duplicate records")
        
        return df
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Main cleaning pipeline.
        
        Args:
            df: Raw DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        logger.info("Starting data cleaning process...")
        
        # Make a copy
        df_clean = df.copy()
        
        # Step 1: Standardize job titles
        logger.info("Standardizing job titles...")
        df_clean['title_standardized'] = df_clean['title'].apply(self.standardize_job_title)
        
        # Step 2: Parse and normalize skills
        logger.info("Parsing and normalizing skills...")
        df_clean['skills_normalized'] = df_clean['skills'].apply(self.parse_skills_column)
        
        # Step 3: Standardize locations
        logger.info("Standardizing locations...")
        location_col = 'location' if 'location' in df_clean.columns else 'city'
        
        if location_col in df_clean.columns:
            location_parsed = df_clean[location_col].apply(self.standardize_location)
            df_clean['city_standardized'] = location_parsed.apply(lambda x: x[0])
            df_clean['state_standardized'] = location_parsed.apply(lambda x: x[1])
        
        # Step 4: Handle missing values
        logger.info("Handling missing values...")
        df_clean['company'] = df_clean['company'].fillna('Unknown Company')
        df_clean['title_standardized'] = df_clean['title_standardized'].fillna('Unknown Role')
        
        # Step 5: Remove duplicates
        logger.info("Removing duplicates...")
        df_clean = self.remove_duplicates(df_clean)
        
        # Step 6: Create role category
        logger.info("Creating role categories...")
        df_clean['role_category'] = df_clean['title_standardized'].apply(self._categorize_role)
        
        # Step 7: Add skill count
        df_clean['skill_count'] = df_clean['skills_normalized'].apply(len)
        
        logger.info(f"Cleaning complete. Final dataset has {len(df_clean)} records.")
        
        return df_clean
    
    def _categorize_role(self, title: str) -> str:
        """
        Categorize job titles into broader role categories.
        
        Args:
            title: Standardized job title
            
        Returns:
            Role category
        """
        title_lower = title.lower()
        
        if 'data scientist' in title_lower or 'machine learning' in title_lower or 'ai' in title_lower:
            return 'Data Science & ML'
        elif 'data analyst' in title_lower or 'bi analyst' in title_lower or 'business analyst' in title_lower:
            return 'Analytics'
        elif 'data engineer' in title_lower:
            return 'Data Engineering'
        elif 'software' in title_lower or 'developer' in title_lower:
            return 'Software Engineering'
        elif 'devops' in title_lower or 'sre' in title_lower or 'platform' in title_lower or 'cloud' in title_lower:
            return 'DevOps & Cloud'
        elif 'manager' in title_lower:
            return 'Management'
        elif 'architect' in title_lower:
            return 'Architecture'
        elif 'security' in title_lower or 'qa' in title_lower:
            return 'Security & QA'
        else:
            return 'Other'
    
    def save_cleaned_data(self, df: pd.DataFrame, filename: str = None):
        """
        Save cleaned data to files.
        
        Args:
            df: Cleaned DataFrame
            filename: Base filename (optional)
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"jobs_cleaned_{timestamp}"
        
        # Save as CSV
        csv_path = self.output_dir / f"{filename}.csv"
        
        # For CSV, convert lists to strings
        df_csv = df.copy()
        df_csv['skills_normalized'] = df_csv['skills_normalized'].apply(lambda x: ','.join(x) if isinstance(x, list) else x)
        df_csv.to_csv(csv_path, index=False)
        
        # Save as JSON (preserves list structure)
        json_path = self.output_dir / f"{filename}.json"
        df.to_json(json_path, orient='records', indent=2)
        
        # Save Excel with multiple sheets
        excel_path = self.output_dir / f"{filename}.xlsx"
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df_csv.to_excel(writer, sheet_name='All Jobs', index=False)
            
            # Summary statistics
            summary_data = {
                'Metric': [
                    'Total Jobs',
                    'Unique Companies',
                    'Unique Cities',
                    'Unique Job Titles',
                    'Average Skills per Job',
                    'Most Common Role Category'
                ],
                'Value': [
                    len(df),
                    df['company'].nunique(),
                    df['city_standardized'].nunique() if 'city_standardized' in df.columns else 'N/A',
                    df['title_standardized'].nunique(),
                    df['skill_count'].mean().round(2),
                    df['role_category'].mode()[0] if 'role_category' in df.columns else 'N/A'
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        logger.info(f"Cleaned data saved to:")
        logger.info(f"  - {csv_path}")
        logger.info(f"  - {json_path}")
        logger.info(f"  - {excel_path}")
    
    def get_data_quality_report(self, df: pd.DataFrame) -> dict:
        """
        Generate a data quality report.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with quality metrics
        """
        # Get subset of columns that don't contain lists for duplicate check
        hashable_cols = [col for col in df.columns if not df[col].apply(lambda x: isinstance(x, list)).any()]
        
        report = {
            'total_records': len(df),
            'duplicate_count': df[hashable_cols].duplicated().sum() if hashable_cols else 0,
            'unique_titles': df['title_standardized'].nunique() if 'title_standardized' in df.columns else 0,
            'unique_companies': df['company'].nunique() if 'company' in df.columns else 0,
            'unique_cities': df['city_standardized'].nunique() if 'city_standardized' in df.columns else 0,
            'avg_skills_per_job': df['skill_count'].mean() if 'skill_count' in df.columns else 0,
            'jobs_with_no_skills': (df['skill_count'] == 0).sum() if 'skill_count' in df.columns else 0,
        }
        
        return report
    
    def run(self, input_file: str = None) -> pd.DataFrame:
        """
        Main method to run the cleaning pipeline.
        
        Args:
            input_file: Path to input file (optional, uses latest if not provided)
            
        Returns:
            Cleaned DataFrame
        """
        # Load data
        if input_file:
            df = self.load_data(input_file)
        else:
            df = self.load_latest_raw_data()
        
        # Clean data
        df_clean = self.clean_data(df)
        
        # Save cleaned data
        self.save_cleaned_data(df_clean)
        
        # Generate quality report
        report = self.get_data_quality_report(df_clean)
        logger.info(f"\nData Quality Report:")
        for key, value in report.items():
            logger.info(f"  {key}: {value}")
        
        return df_clean


def main():
    """Main entry point for the cleaner."""
    cleaner = JobDataCleaner(
        input_dir="../data/raw",
        output_dir="../data/processed"
    )
    
    df_clean = cleaner.run()
    
    print(f"\nCleaning complete!")
    print(f"Total cleaned records: {len(df_clean)}")
    print(f"\nRole Category Distribution:")
    print(df_clean['role_category'].value_counts())
    print(f"\nTop 10 Cities:")
    if 'city_standardized' in df_clean.columns:
        print(df_clean['city_standardized'].value_counts().head(10))
    
    return df_clean


if __name__ == "__main__":
    main()
