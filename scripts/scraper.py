"""
LinkedIn Job Scraper
====================
This script scrapes job postings data from job sites.
Note: Due to LinkedIn's anti-scraping measures, this uses alternative sources.

Author: LinkedIn Job Analysis Project
Date: January 2026
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import logging
import json
from datetime import datetime
from pathlib import Path
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# User agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
]

# Skills dictionary for extraction
SKILLS_DICTIONARY = {
    # Programming Languages
    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'go', 'golang',
    'rust', 'php', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'perl', 'shell', 'bash',
    
    # Data & Analytics
    'sql', 'nosql', 'mongodb', 'postgresql', 'mysql', 'oracle', 'redis', 'elasticsearch',
    'pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn', 'plotly', 'tableau', 'power bi',
    'excel', 'spark', 'hadoop', 'hive', 'kafka', 'airflow', 'dbt',
    
    # Machine Learning & AI
    'machine learning', 'deep learning', 'neural networks', 'tensorflow', 'pytorch',
    'keras', 'scikit-learn', 'sklearn', 'nlp', 'natural language processing',
    'computer vision', 'opencv', 'llm', 'gpt', 'transformers', 'huggingface',
    
    # Cloud & DevOps
    'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'k8s',
    'terraform', 'ansible', 'jenkins', 'ci/cd', 'git', 'github', 'gitlab',
    'linux', 'unix', 'windows server',
    
    # Web Development
    'html', 'css', 'react', 'reactjs', 'angular', 'vue', 'vuejs', 'node.js', 'nodejs',
    'express', 'django', 'flask', 'fastapi', 'spring', 'spring boot', 'rest api',
    'graphql', 'microservices',
    
    # Soft Skills & Methodologies
    'agile', 'scrum', 'jira', 'confluence', 'communication', 'leadership',
    'problem solving', 'teamwork', 'project management'
}


class JobScraper:
    """
    A class to scrape job postings from various job sites.
    """
    
    def __init__(self, output_dir: str = "../data/raw"):
        """
        Initialize the scraper.
        
        Args:
            output_dir: Directory to save raw scraped data
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.jobs_data = []
        
    def _get_random_user_agent(self) -> str:
        """Return a random user agent for request headers."""
        return random.choice(USER_AGENTS)
    
    def _get_headers(self) -> dict:
        """Generate request headers with random user agent."""
        return {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    def _rate_limit(self, min_delay: float = 2, max_delay: float = 5):
        """
        Add random delay between requests to avoid blocking.
        
        Args:
            min_delay: Minimum delay in seconds
            max_delay: Maximum delay in seconds
        """
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def extract_skills(self, text: str) -> list:
        """
        Extract skills from job description text.
        
        Args:
            text: Job description text
            
        Returns:
            List of extracted skills
        """
        if not text:
            return []
        
        text_lower = text.lower()
        found_skills = []
        
        for skill in SKILLS_DICTIONARY:
            if skill in text_lower:
                found_skills.append(skill)
        
        return list(set(found_skills))
    
    def scrape_indeed(self, query: str, location: str, num_pages: int = 5) -> list:
        """
        Scrape job listings from Indeed.
        
        Args:
            query: Job search query (e.g., "data analyst")
            location: Location to search (e.g., "New York")
            num_pages: Number of pages to scrape
            
        Returns:
            List of job dictionaries
        """
        logger.info(f"Scraping Indeed for '{query}' in '{location}'")
        jobs = []
        base_url = "https://www.indeed.com/jobs"
        
        for page in tqdm(range(num_pages), desc=f"Scraping {location}"):
            params = {
                'q': query,
                'l': location,
                'start': page * 10
            }
            
            try:
                response = self.session.get(
                    base_url,
                    params=params,
                    headers=self._get_headers(),
                    timeout=30
                )
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'lxml')
                    job_cards = soup.find_all('div', class_='job_seen_beacon')
                    
                    for card in job_cards:
                        job = self._parse_indeed_job(card, location)
                        if job:
                            jobs.append(job)
                            
                elif response.status_code == 403:
                    logger.warning("Access forbidden - possibly blocked")
                    break
                else:
                    logger.warning(f"Got status code: {response.status_code}")
                    
            except requests.RequestException as e:
                logger.error(f"Request error: {e}")
                
            self._rate_limit()
        
        logger.info(f"Scraped {len(jobs)} jobs from Indeed for {location}")
        return jobs
    
    def _parse_indeed_job(self, card, location: str) -> dict:
        """
        Parse a single Indeed job card.
        
        Args:
            card: BeautifulSoup element for job card
            location: Search location
            
        Returns:
            Dictionary with job details
        """
        try:
            # Extract job title
            title_elem = card.find('h2', class_='jobTitle')
            title = title_elem.get_text(strip=True) if title_elem else None
            
            # Extract company name
            company_elem = card.find('span', {'data-testid': 'company-name'})
            company = company_elem.get_text(strip=True) if company_elem else None
            
            # Extract location
            location_elem = card.find('div', {'data-testid': 'text-location'})
            job_location = location_elem.get_text(strip=True) if location_elem else location
            
            # Extract snippet/description
            snippet_elem = card.find('div', class_='job-snippet')
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
            
            # Extract skills from snippet
            skills = self.extract_skills(snippet)
            
            return {
                'job_id': f"ind_{hash(f'{title}{company}{job_location}')}",
                'title': title,
                'company': company,
                'location': job_location,
                'description_snippet': snippet,
                'skills': skills,
                'source': 'Indeed',
                'scraped_date': datetime.now().isoformat(),
                'search_location': location
            }
            
        except Exception as e:
            logger.error(f"Error parsing job card: {e}")
            return None
    
    def generate_sample_data(self, num_jobs: int = 500) -> pd.DataFrame:
        """
        Generate realistic sample job data for analysis.
        Use this when scraping is blocked or for testing.
        
        Args:
            num_jobs: Number of sample jobs to generate
            
        Returns:
            DataFrame with sample job data
        """
        logger.info(f"Generating {num_jobs} sample job records")
        
        # Sample data pools
        job_titles = [
            'Data Analyst', 'Senior Data Analyst', 'Data Scientist', 
            'Machine Learning Engineer', 'Software Engineer', 'Senior Software Engineer',
            'Data Engineer', 'Backend Developer', 'Frontend Developer',
            'Full Stack Developer', 'DevOps Engineer', 'Cloud Engineer',
            'Business Analyst', 'Product Manager', 'Project Manager',
            'QA Engineer', 'Security Engineer', 'Solutions Architect',
            'AI/ML Engineer', 'Python Developer', 'Java Developer'
        ]
        
        companies = [
            'Tech Corp', 'Data Solutions Inc', 'Cloud Systems LLC',
            'Innovation Labs', 'Digital Dynamics', 'Smart Analytics',
            'Future Tech', 'Code Masters', 'Data Driven Co',
            'AI Innovations', 'Software Solutions', 'Tech Pioneers',
            'Global Tech', 'Data Insights', 'Cloud Ventures'
        ]
        
        cities = [
            ('New York', 'NY'), ('San Francisco', 'CA'), ('Seattle', 'WA'),
            ('Austin', 'TX'), ('Boston', 'MA'), ('Los Angeles', 'CA'),
            ('Chicago', 'IL'), ('Denver', 'CO'), ('Atlanta', 'GA'),
            ('Remote', 'USA')
        ]
        
        # Skills by job type
        skills_by_role = {
            'Data Analyst': ['sql', 'python', 'excel', 'tableau', 'power bi', 'pandas'],
            'Data Scientist': ['python', 'machine learning', 'sql', 'pandas', 'scikit-learn', 'tensorflow'],
            'Machine Learning Engineer': ['python', 'tensorflow', 'pytorch', 'machine learning', 'deep learning', 'aws'],
            'Software Engineer': ['python', 'java', 'javascript', 'git', 'sql', 'rest api'],
            'Data Engineer': ['python', 'sql', 'spark', 'airflow', 'aws', 'kafka'],
            'DevOps Engineer': ['docker', 'kubernetes', 'aws', 'terraform', 'jenkins', 'linux'],
            'Frontend Developer': ['javascript', 'react', 'html', 'css', 'typescript', 'git'],
            'Backend Developer': ['python', 'java', 'sql', 'rest api', 'docker', 'git'],
            'Full Stack Developer': ['javascript', 'python', 'react', 'node.js', 'sql', 'git'],
        }
        
        jobs = []
        
        for i in tqdm(range(num_jobs), desc="Generating sample data"):
            title = random.choice(job_titles)
            city, state = random.choice(cities)
            company = random.choice(companies)
            
            # Get skills based on role (with some randomness)
            base_role = title.split()[0] if 'Senior' in title else title
            for role_key in skills_by_role:
                if role_key in title or base_role in role_key:
                    base_skills = skills_by_role[role_key]
                    break
            else:
                base_skills = ['python', 'sql', 'excel', 'communication']
            
            # Add some random additional skills
            num_skills = random.randint(3, 8)
            selected_skills = random.sample(base_skills, min(len(base_skills), num_skills))
            
            # Occasionally add other random skills
            if random.random() > 0.5:
                extra_skills = random.sample(list(SKILLS_DICTIONARY - set(selected_skills)), 
                                            min(2, len(SKILLS_DICTIONARY)))
                selected_skills.extend(extra_skills)
            
            job = {
                'job_id': f"sample_{i+1}",
                'title': title,
                'company': f"{company} #{random.randint(1, 100)}",
                'city': city,
                'state': state,
                'location': f"{city}, {state}",
                'skills': selected_skills,
                'post_date': datetime(2026, 1, random.randint(1, 14)).strftime('%Y-%m-%d'),
                'source': 'Sample Data',
                'scraped_date': datetime.now().isoformat()
            }
            
            jobs.append(job)
        
        df = pd.DataFrame(jobs)
        logger.info(f"Generated {len(df)} sample job records")
        return df
    
    def save_data(self, df: pd.DataFrame, filename: str):
        """
        Save scraped data to CSV and JSON formats.
        
        Args:
            df: DataFrame with job data
            filename: Base filename (without extension)
        """
        csv_path = self.output_dir / f"{filename}.csv"
        json_path = self.output_dir / f"{filename}.json"
        
        df.to_csv(csv_path, index=False)
        df.to_json(json_path, orient='records', indent=2)
        
        logger.info(f"Data saved to {csv_path} and {json_path}")
    
    def run(self, queries: list = None, locations: list = None, 
            use_sample_data: bool = True, num_sample_jobs: int = 500):
        """
        Main method to run the scraping process.
        
        Args:
            queries: List of job search queries
            locations: List of locations to search
            use_sample_data: If True, generate sample data instead of scraping
            num_sample_jobs: Number of sample jobs to generate
            
        Returns:
            DataFrame with all scraped/generated jobs
        """
        if use_sample_data:
            logger.info("Using sample data generation mode")
            df = self.generate_sample_data(num_sample_jobs)
        else:
            if queries is None:
                queries = ['data analyst', 'data scientist', 'software engineer']
            if locations is None:
                locations = ['New York', 'San Francisco', 'Seattle', 'Austin', 'Boston']
            
            all_jobs = []
            for query in queries:
                for location in locations:
                    jobs = self.scrape_indeed(query, location)
                    all_jobs.extend(jobs)
                    
            df = pd.DataFrame(all_jobs)
        
        # Save the data
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.save_data(df, f"jobs_raw_{timestamp}")
        
        return df


def main():
    """Main entry point for the scraper."""
    scraper = JobScraper(output_dir="../data/raw")
    
    # Generate sample data (recommended for initial development)
    # Set use_sample_data=False to attempt actual scraping
    df = scraper.run(use_sample_data=True, num_sample_jobs=500)
    
    print(f"\nScraping complete!")
    print(f"Total jobs collected: {len(df)}")
    print(f"\nSample of collected data:")
    print(df.head(10))
    
    return df


if __name__ == "__main__":
    main()
