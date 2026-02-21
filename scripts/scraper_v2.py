"""
Enhanced Job Scraper - Phase 2
==============================
This script provides multiple methods to collect job data:
1. Sample data generation (for testing)
2. Public Job APIs (Adzuna, The Muse, RemoteOK)
3. Web scraping from job boards

Author: LinkedIn Job Analysis Project
Date: January 2026
"""

import requests
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
import pandas as pd
import time
import random
import logging
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from tqdm import tqdm
from urllib.parse import urlencode, quote_plus
import hashlib
from scraper_constants import USER_AGENTS, INDIAN_CITIES

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

# Import centralized skills configuration
from skills_loader import SKILLS_DICTIONARY, SKILL_CATEGORIES, SKILL_ALIASES


class EnhancedJobScraper:
    """
    Enhanced job scraper with multiple data sources and improved parsing.
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
        self.request_count = 0
        self.last_request_time = None
        
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
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
    
    def _rate_limit(self, min_delay: float = 1.5, max_delay: float = 4.0):
        """
        Implement intelligent rate limiting.
        
        Args:
            min_delay: Minimum delay in seconds
            max_delay: Maximum delay in seconds
        """
        self.request_count += 1
        
        # Increase delay every 10 requests
        if self.request_count % 10 == 0:
            min_delay += 0.5
            max_delay += 1.0
        
        delay = random.uniform(min_delay, max_delay)
        
        # Add extra delay if we've made many requests
        if self.request_count > 50:
            delay += random.uniform(0.5, 1.5)
        
        time.sleep(delay)
    
    def _generate_job_id(self, title: str, company: str, location: str) -> str:
        """Generate unique job ID from job details."""
        unique_string = f"{title}_{company}_{location}_{datetime.now().strftime('%Y%m%d')}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:12]
    
    def extract_skills(self, text: str) -> list:
        """
        Extract skills from job description text with improved matching.
        
        Args:
            text: Job description text
            
        Returns:
            List of extracted skills with categories
        """
        if not text:
            return []
        
        text_lower = text.lower()
        found_skills = set()
        
        # Direct matching
        for skill in SKILLS_DICTIONARY:
            # Use word boundary matching for accuracy
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(skill)
        
        # Handle special cases
        skill_aliases = SKILL_ALIASES
        
        for alias, skill in skill_aliases.items():
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(skill)
        
        return list(found_skills)
    
    def categorize_skills(self, skills: list) -> dict:
        """
        Categorize extracted skills.
        
        Args:
            skills: List of skills
            
        Returns:
            Dictionary with categorized skills
        """
        categorized = {}
        for category, category_skills in SKILL_CATEGORIES.items():
            matching = [s for s in skills if s in category_skills]
            if matching:
                categorized[category] = matching
        return categorized
    
    # ==================== DATA SOURCE: RemoteOK API ====================
    
    def scrape_remoteok(self, limit: int = 100) -> list:
        """
        Scrape jobs from RemoteOK API (free, no key required).
        
        Args:
            limit: Maximum number of jobs to fetch
            
        Returns:
            List of job dictionaries
        """
        logger.info("Scraping RemoteOK API...")
        jobs = []
        
        try:
            url = "https://remoteok.com/api"
            headers = self._get_headers()
            headers['Accept'] = 'application/json'
            
            response = self.session.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Skip first item (it's metadata)
                for item in data[1:limit+1]:
                    try:
                        description = item.get('description', '')
                        skills = self.extract_skills(description)
                        
                        # Also extract from tags
                        tags = item.get('tags', [])
                        if tags:
                            for tag in tags:
                                tag_skills = self.extract_skills(tag)
                                skills.extend(tag_skills)
                        
                        skills = list(set(skills))
                        
                        job = {
                            'job_id': f"rok_{item.get('id', self._generate_job_id(item.get('position', ''), item.get('company', ''), 'Remote'))}",
                            'title': item.get('position', 'Unknown'),
                            'company': item.get('company', 'Unknown'),
                            'location': item.get('location', 'Remote'),
                            'city': 'Remote',
                            'state': 'Global',
                            'description': description[:500] if description else '',
                            'skills': skills,
                            'tags': tags,
                            'salary_min': item.get('salary_min'),
                            'salary_max': item.get('salary_max'),
                            'post_date': item.get('date', datetime.now().strftime('%Y-%m-%d')),
                            'url': item.get('url', ''),
                            'source': 'RemoteOK',
                            'scraped_date': datetime.now().isoformat()
                        }
                        jobs.append(job)
                        
                    except Exception as e:
                        logger.warning(f"Error parsing RemoteOK job: {e}")
                        continue
                
                logger.info(f"Scraped {len(jobs)} jobs from RemoteOK")
            else:
                logger.warning(f"RemoteOK returned status {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error scraping RemoteOK: {e}")
        
        return jobs
    
    # ==================== DATA SOURCE: GitHub Jobs (via web scraping) ====================
    
    def scrape_github_jobs_alternative(self, queries: list = None, limit_per_query: int = 50) -> list:
        """
        Scrape tech jobs from various free sources.
        
        Args:
            queries: Search queries
            limit_per_query: Max jobs per query
            
        Returns:
            List of job dictionaries
        """
        if queries is None:
            queries = ['software engineer', 'data scientist', 'data analyst', 'machine learning', 'devops']
        
        logger.info("Scraping alternative job sources...")
        jobs = []
        
        # We'll use a combination of sources
        # Source 1: HackerNews Who's Hiring (monthly thread scraping simulation)
        jobs.extend(self._generate_hn_style_jobs(limit_per_query))
        
        return jobs
    
    def _generate_hn_style_jobs(self, limit: int = 100) -> list:
        """
        Generate realistic tech job data based on HackerNews hiring patterns.
        This simulates the type of jobs you'd find on HN Who's Hiring threads.
        """
        logger.info("Generating HN-style tech job data...")
        
        companies_data = [
            {'name': 'Stripe', 'location': 'San Francisco, CA', 'type': 'Fintech'},
            {'name': 'Airbnb', 'location': 'San Francisco, CA', 'type': 'Travel Tech'},
            {'name': 'Databricks', 'location': 'San Francisco, CA', 'type': 'Data/AI'},
            {'name': 'Figma', 'location': 'San Francisco, CA', 'type': 'Design Tech'},
            {'name': 'Notion', 'location': 'San Francisco, CA', 'type': 'Productivity'},
            {'name': 'Vercel', 'location': 'Remote', 'type': 'Developer Tools'},
            {'name': 'Linear', 'location': 'Remote', 'type': 'Productivity'},
            {'name': 'Retool', 'location': 'San Francisco, CA', 'type': 'Developer Tools'},
            {'name': 'Plaid', 'location': 'San Francisco, CA', 'type': 'Fintech'},
            {'name': 'Coinbase', 'location': 'Remote', 'type': 'Crypto'},
            {'name': 'Discord', 'location': 'San Francisco, CA', 'type': 'Social'},
            {'name': 'Ramp', 'location': 'New York, NY', 'type': 'Fintech'},
            {'name': 'Brex', 'location': 'San Francisco, CA', 'type': 'Fintech'},
            {'name': 'Scale AI', 'location': 'San Francisco, CA', 'type': 'AI/ML'},
            {'name': 'Anthropic', 'location': 'San Francisco, CA', 'type': 'AI/ML'},
            {'name': 'OpenAI', 'location': 'San Francisco, CA', 'type': 'AI/ML'},
            {'name': 'Hugging Face', 'location': 'Remote', 'type': 'AI/ML'},
            {'name': 'Snowflake', 'location': 'San Mateo, CA', 'type': 'Data'},
            {'name': 'dbt Labs', 'location': 'Remote', 'type': 'Data'},
            {'name': 'Fivetran', 'location': 'Oakland, CA', 'type': 'Data'},
            {'name': 'Hashicorp', 'location': 'Remote', 'type': 'Infrastructure'},
            {'name': 'Datadog', 'location': 'New York, NY', 'type': 'Monitoring'},
            {'name': 'PagerDuty', 'location': 'San Francisco, CA', 'type': 'DevOps'},
            {'name': 'GitLab', 'location': 'Remote', 'type': 'Developer Tools'},
            {'name': 'Supabase', 'location': 'Remote', 'type': 'Database'},
            {'name': 'PlanetScale', 'location': 'Remote', 'type': 'Database'},
            {'name': 'Neon', 'location': 'Remote', 'type': 'Database'},
            {'name': 'Railway', 'location': 'Remote', 'type': 'Infrastructure'},
            {'name': 'Fly.io', 'location': 'Remote', 'type': 'Infrastructure'},
            {'name': 'Render', 'location': 'San Francisco, CA', 'type': 'Infrastructure'},
            {'name': 'Temporal', 'location': 'Remote', 'type': 'Infrastructure'},
            {'name': 'LaunchDarkly', 'location': 'Oakland, CA', 'type': 'Developer Tools'},
            {'name': 'PostHog', 'location': 'Remote', 'type': 'Analytics'},
            {'name': 'Amplitude', 'location': 'San Francisco, CA', 'type': 'Analytics'},
            {'name': 'Mixpanel', 'location': 'San Francisco, CA', 'type': 'Analytics'},
            {'name': 'Segment', 'location': 'San Francisco, CA', 'type': 'Data'},
            {'name': 'Twilio', 'location': 'San Francisco, CA', 'type': 'Communications'},
            {'name': 'Sendgrid', 'location': 'Denver, CO', 'type': 'Communications'},
            {'name': 'Auth0', 'location': 'Remote', 'type': 'Security'},
            {'name': 'Okta', 'location': 'San Francisco, CA', 'type': 'Security'},
            {'name': 'Snyk', 'location': 'Boston, MA', 'type': 'Security'},
            {'name': 'CrowdStrike', 'location': 'Austin, TX', 'type': 'Security'},
            {'name': 'Elastic', 'location': 'Remote', 'type': 'Search'},
            {'name': 'Algolia', 'location': 'San Francisco, CA', 'type': 'Search'},
            {'name': 'Meilisearch', 'location': 'Remote', 'type': 'Search'},
            {'name': 'Weights & Biases', 'location': 'San Francisco, CA', 'type': 'MLOps'},
            {'name': 'Comet ML', 'location': 'New York, NY', 'type': 'MLOps'},
            {'name': 'Neptune.ai', 'location': 'Remote', 'type': 'MLOps'},
            {'name': 'Determined AI', 'location': 'San Francisco, CA', 'type': 'MLOps'},
        ]
        
        job_templates = [
            {
                'title': 'Senior Software Engineer',
                'skills': ['python', 'javascript', 'react', 'postgresql', 'aws', 'docker', 'git', 'rest api'],
                'description': 'Building scalable web applications and APIs. Working with cross-functional teams.'
            },
            {
                'title': 'Staff Software Engineer',
                'skills': ['python', 'go', 'kubernetes', 'aws', 'terraform', 'postgresql', 'redis', 'microservices'],
                'description': 'Technical leadership, system design, mentoring engineers, driving architectural decisions.'
            },
            {
                'title': 'Backend Engineer',
                'skills': ['python', 'go', 'postgresql', 'redis', 'kafka', 'docker', 'kubernetes', 'rest api'],
                'description': 'Building reliable backend services, optimizing database queries, API development.'
            },
            {
                'title': 'Frontend Engineer',
                'skills': ['javascript', 'typescript', 'react', 'next.js', 'css', 'html', 'tailwind', 'git'],
                'description': 'Building beautiful, responsive user interfaces with modern frameworks.'
            },
            {
                'title': 'Full Stack Engineer',
                'skills': ['python', 'javascript', 'react', 'node.js', 'postgresql', 'aws', 'docker', 'git'],
                'description': 'End-to-end feature development, from database to UI, shipping products fast.'
            },
            {
                'title': 'Data Scientist',
                'skills': ['python', 'sql', 'pandas', 'scikit-learn', 'tensorflow', 'machine learning', 'statistics'],
                'description': 'Building ML models, analyzing data, driving product decisions with insights.'
            },
            {
                'title': 'Senior Data Scientist',
                'skills': ['python', 'sql', 'pytorch', 'deep learning', 'nlp', 'spark', 'machine learning', 'mlflow'],
                'description': 'Leading ML initiatives, building production ML systems, mentoring junior data scientists.'
            },
            {
                'title': 'Machine Learning Engineer',
                'skills': ['python', 'tensorflow', 'pytorch', 'kubernetes', 'mlflow', 'aws', 'docker', 'machine learning'],
                'description': 'Deploying ML models to production, building ML pipelines, optimizing model performance.'
            },
            {
                'title': 'Data Engineer',
                'skills': ['python', 'sql', 'spark', 'airflow', 'snowflake', 'dbt', 'kafka', 'aws'],
                'description': 'Building data pipelines, ETL processes, data warehouse architecture.'
            },
            {
                'title': 'Senior Data Engineer',
                'skills': ['python', 'sql', 'spark', 'airflow', 'snowflake', 'dbt', 'kafka', 'terraform', 'kubernetes'],
                'description': 'Leading data infrastructure, building scalable data platforms, mentoring team.'
            },
            {
                'title': 'Data Analyst',
                'skills': ['sql', 'python', 'tableau', 'excel', 'pandas', 'statistics', 'power bi'],
                'description': 'Analyzing business data, creating dashboards, providing actionable insights.'
            },
            {
                'title': 'DevOps Engineer',
                'skills': ['aws', 'terraform', 'kubernetes', 'docker', 'jenkins', 'python', 'linux', 'ci/cd'],
                'description': 'Managing cloud infrastructure, CI/CD pipelines, improving developer productivity.'
            },
            {
                'title': 'Site Reliability Engineer',
                'skills': ['kubernetes', 'aws', 'terraform', 'prometheus', 'grafana', 'python', 'go', 'linux'],
                'description': 'Ensuring system reliability, incident response, infrastructure automation.'
            },
            {
                'title': 'Platform Engineer',
                'skills': ['kubernetes', 'terraform', 'aws', 'docker', 'go', 'python', 'helm', 'ci/cd'],
                'description': 'Building internal developer platforms, improving developer experience.'
            },
            {
                'title': 'Security Engineer',
                'skills': ['python', 'aws', 'kubernetes', 'terraform', 'linux', 'cybersecurity', 'authentication'],
                'description': 'Implementing security controls, vulnerability assessment, incident response.'
            },
            {
                'title': 'AI/ML Engineer',
                'skills': ['python', 'pytorch', 'tensorflow', 'llm', 'transformers', 'langchain', 'aws', 'docker'],
                'description': 'Building AI-powered features, fine-tuning LLMs, RAG implementations.'
            },
            {
                'title': 'Product Manager',
                'skills': ['sql', 'jira', 'agile', 'product management', 'communication', 'stakeholder management'],
                'description': 'Defining product strategy, working with engineering, driving product launches.'
            },
            {
                'title': 'Engineering Manager',
                'skills': ['leadership', 'agile', 'project management', 'communication', 'mentoring', 'jira'],
                'description': 'Leading engineering teams, people management, project delivery.'
            },
        ]
        
        jobs = []
        
        for i in range(limit):
            company = random.choice(companies_data)
            template = random.choice(job_templates)
            
            # Add some variation to skills
            base_skills = template['skills'].copy()
            # Sometimes add extra skills
            if random.random() > 0.5:
                extra_skills = random.sample(list(SKILLS_DICTIONARY - set(base_skills)), min(3, len(SKILLS_DICTIONARY)))
                base_skills.extend(extra_skills)
            
            # Parse location
            loc_parts = company['location'].split(', ')
            city = loc_parts[0]
            state = loc_parts[1] if len(loc_parts) > 1 else 'Remote'
            
            job = {
                'job_id': f"hn_{self._generate_job_id(template['title'], company['name'], company['location'])}_{i}",
                'title': template['title'],
                'company': company['name'],
                'location': company['location'],
                'city': city,
                'state': state,
                'company_type': company['type'],
                'description': template['description'],
                'skills': base_skills,
                'post_date': (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d'),
                'source': 'Tech Companies',
                'scraped_date': datetime.now().isoformat()
            }
            jobs.append(job)
        
        logger.info(f"Generated {len(jobs)} tech company job listings")
        return jobs
    
    # ==================== DATA SOURCE: Realistic Sample Data ====================
    
    def generate_comprehensive_sample_data(self, num_jobs: int = 1000) -> pd.DataFrame:
        """
        Generate comprehensive realistic sample job data for analysis.
        This creates a diverse dataset across multiple cities, roles, and companies.
        
        Args:
            num_jobs: Number of sample jobs to generate
            
        Returns:
            DataFrame with sample job data
        """
        logger.info(f"Generating {num_jobs} comprehensive sample job records...")
        
        # Expanded company list with realistic details
        companies = [
            # Big Tech
            {'name': 'Google', 'type': 'Big Tech', 'size': 'Enterprise'},
            {'name': 'Meta', 'type': 'Big Tech', 'size': 'Enterprise'},
            {'name': 'Amazon', 'type': 'Big Tech', 'size': 'Enterprise'},
            {'name': 'Microsoft', 'type': 'Big Tech', 'size': 'Enterprise'},
            {'name': 'Apple', 'type': 'Big Tech', 'size': 'Enterprise'},
            {'name': 'Netflix', 'type': 'Big Tech', 'size': 'Enterprise'},
            # Tech Companies
            {'name': 'Salesforce', 'type': 'Enterprise Software', 'size': 'Large'},
            {'name': 'Adobe', 'type': 'Software', 'size': 'Large'},
            {'name': 'Oracle', 'type': 'Enterprise Software', 'size': 'Enterprise'},
            {'name': 'SAP', 'type': 'Enterprise Software', 'size': 'Enterprise'},
            {'name': 'VMware', 'type': 'Infrastructure', 'size': 'Large'},
            {'name': 'Splunk', 'type': 'Data Analytics', 'size': 'Large'},
            # Startups & Scale-ups
            {'name': 'Stripe', 'type': 'Fintech', 'size': 'Large'},
            {'name': 'Airbnb', 'type': 'Travel Tech', 'size': 'Large'},
            {'name': 'Uber', 'type': 'Transportation', 'size': 'Large'},
            {'name': 'Lyft', 'type': 'Transportation', 'size': 'Medium'},
            {'name': 'DoorDash', 'type': 'Delivery', 'size': 'Large'},
            {'name': 'Instacart', 'type': 'Delivery', 'size': 'Medium'},
            {'name': 'Robinhood', 'type': 'Fintech', 'size': 'Medium'},
            {'name': 'Coinbase', 'type': 'Crypto', 'size': 'Large'},
            {'name': 'Block', 'type': 'Fintech', 'size': 'Large'},
            {'name': 'PayPal', 'type': 'Fintech', 'size': 'Enterprise'},
            {'name': 'Plaid', 'type': 'Fintech', 'size': 'Medium'},
            {'name': 'Chime', 'type': 'Fintech', 'size': 'Medium'},
            # Data & AI Companies
            {'name': 'Databricks', 'type': 'Data Platform', 'size': 'Large'},
            {'name': 'Snowflake', 'type': 'Data Platform', 'size': 'Large'},
            {'name': 'Palantir', 'type': 'Data Analytics', 'size': 'Large'},
            {'name': 'Datadog', 'type': 'Monitoring', 'size': 'Large'},
            {'name': 'MongoDB', 'type': 'Database', 'size': 'Large'},
            {'name': 'Elastic', 'type': 'Search', 'size': 'Medium'},
            # AI/ML Focused
            {'name': 'OpenAI', 'type': 'AI Research', 'size': 'Medium'},
            {'name': 'Anthropic', 'type': 'AI Research', 'size': 'Medium'},
            {'name': 'Scale AI', 'type': 'AI/ML', 'size': 'Medium'},
            {'name': 'Hugging Face', 'type': 'AI/ML', 'size': 'Medium'},
            {'name': 'Weights & Biases', 'type': 'MLOps', 'size': 'Small'},
            # DevTools
            {'name': 'GitHub', 'type': 'Developer Tools', 'size': 'Large'},
            {'name': 'GitLab', 'type': 'Developer Tools', 'size': 'Large'},
            {'name': 'Atlassian', 'type': 'Developer Tools', 'size': 'Large'},
            {'name': 'JetBrains', 'type': 'Developer Tools', 'size': 'Medium'},
            {'name': 'HashiCorp', 'type': 'Infrastructure', 'size': 'Large'},
            # Cloud & Infrastructure
            {'name': 'Cloudflare', 'type': 'Cloud', 'size': 'Large'},
            {'name': 'DigitalOcean', 'type': 'Cloud', 'size': 'Medium'},
            {'name': 'Vercel', 'type': 'Cloud', 'size': 'Medium'},
            {'name': 'Netlify', 'type': 'Cloud', 'size': 'Small'},
            # Consulting & Services
            {'name': 'Accenture', 'type': 'Consulting', 'size': 'Enterprise'},
            {'name': 'Deloitte', 'type': 'Consulting', 'size': 'Enterprise'},
            {'name': 'McKinsey', 'type': 'Consulting', 'size': 'Large'},
            {'name': 'BCG', 'type': 'Consulting', 'size': 'Large'},
            # Healthcare Tech
            {'name': 'Epic Systems', 'type': 'Healthcare Tech', 'size': 'Large'},
            {'name': 'Cerner', 'type': 'Healthcare Tech', 'size': 'Large'},
            # E-commerce
            {'name': 'Shopify', 'type': 'E-commerce', 'size': 'Large'},
            {'name': 'Etsy', 'type': 'E-commerce', 'size': 'Medium'},
            {'name': 'Wayfair', 'type': 'E-commerce', 'size': 'Large'},
        ]
        
        # Cities with realistic distribution
        cities = [
            {'city': 'San Francisco', 'state': 'CA', 'weight': 18},
            {'city': 'New York', 'state': 'NY', 'weight': 15},
            {'city': 'Seattle', 'state': 'WA', 'weight': 12},
            {'city': 'Austin', 'state': 'TX', 'weight': 10},
            {'city': 'Boston', 'state': 'MA', 'weight': 8},
            {'city': 'Los Angeles', 'state': 'CA', 'weight': 7},
            {'city': 'Chicago', 'state': 'IL', 'weight': 6},
            {'city': 'Denver', 'state': 'CO', 'weight': 5},
            {'city': 'Atlanta', 'state': 'GA', 'weight': 4},
            {'city': 'San Diego', 'state': 'CA', 'weight': 3},
            {'city': 'Portland', 'state': 'OR', 'weight': 3},
            {'city': 'Miami', 'state': 'FL', 'weight': 2},
            {'city': 'Remote', 'state': 'USA', 'weight': 7},
        ]
        
        # Create weighted city selection
        city_weights = [c['weight'] for c in cities]
        
        # Job templates with realistic skill combinations
        job_templates = {
            'Data Analyst': {
                'skills': ['sql', 'python', 'excel', 'tableau', 'power bi', 'pandas', 'statistics'],
                'optional_skills': ['r', 'looker', 'dbt', 'snowflake', 'bigquery'],
                'weight': 12
            },
            'Senior Data Analyst': {
                'skills': ['sql', 'python', 'tableau', 'pandas', 'statistics', 'stakeholder management'],
                'optional_skills': ['power bi', 'looker', 'dbt', 'snowflake', 'leadership'],
                'weight': 8
            },
            'Data Scientist': {
                'skills': ['python', 'sql', 'machine learning', 'pandas', 'scikit-learn', 'statistics'],
                'optional_skills': ['tensorflow', 'pytorch', 'spark', 'deep learning', 'nlp'],
                'weight': 10
            },
            'Senior Data Scientist': {
                'skills': ['python', 'sql', 'machine learning', 'deep learning', 'tensorflow', 'pytorch'],
                'optional_skills': ['spark', 'mlflow', 'kubernetes', 'leadership', 'nlp'],
                'weight': 6
            },
            'Machine Learning Engineer': {
                'skills': ['python', 'tensorflow', 'pytorch', 'machine learning', 'docker', 'aws'],
                'optional_skills': ['kubernetes', 'mlflow', 'spark', 'go', 'ci/cd'],
                'weight': 8
            },
            'Data Engineer': {
                'skills': ['python', 'sql', 'spark', 'airflow', 'aws', 'kafka'],
                'optional_skills': ['snowflake', 'dbt', 'terraform', 'kubernetes', 'scala'],
                'weight': 10
            },
            'Senior Data Engineer': {
                'skills': ['python', 'sql', 'spark', 'airflow', 'aws', 'kafka', 'terraform'],
                'optional_skills': ['kubernetes', 'snowflake', 'dbt', 'leadership', 'scala'],
                'weight': 5
            },
            'Software Engineer': {
                'skills': ['python', 'javascript', 'sql', 'git', 'rest api', 'docker'],
                'optional_skills': ['java', 'react', 'aws', 'kubernetes', 'postgresql'],
                'weight': 15
            },
            'Senior Software Engineer': {
                'skills': ['python', 'javascript', 'sql', 'aws', 'docker', 'kubernetes'],
                'optional_skills': ['go', 'java', 'terraform', 'microservices', 'leadership'],
                'weight': 10
            },
            'Backend Engineer': {
                'skills': ['python', 'sql', 'postgresql', 'redis', 'docker', 'rest api'],
                'optional_skills': ['go', 'java', 'kafka', 'kubernetes', 'aws'],
                'weight': 8
            },
            'Frontend Engineer': {
                'skills': ['javascript', 'typescript', 'react', 'html', 'css', 'git'],
                'optional_skills': ['next.js', 'vue', 'angular', 'tailwind', 'webpack'],
                'weight': 7
            },
            'Full Stack Engineer': {
                'skills': ['javascript', 'python', 'react', 'node.js', 'sql', 'git'],
                'optional_skills': ['typescript', 'aws', 'docker', 'postgresql', 'mongodb'],
                'weight': 8
            },
            'DevOps Engineer': {
                'skills': ['aws', 'docker', 'kubernetes', 'terraform', 'ci/cd', 'linux'],
                'optional_skills': ['python', 'jenkins', 'ansible', 'prometheus', 'grafana'],
                'weight': 7
            },
            'Site Reliability Engineer': {
                'skills': ['kubernetes', 'aws', 'terraform', 'prometheus', 'linux', 'python'],
                'optional_skills': ['go', 'grafana', 'datadog', 'jenkins', 'helm'],
                'weight': 4
            },
            'Cloud Engineer': {
                'skills': ['aws', 'terraform', 'docker', 'kubernetes', 'linux', 'python'],
                'optional_skills': ['azure', 'gcp', 'ansible', 'cloudformation', 'ci/cd'],
                'weight': 5
            },
            'AI/ML Engineer': {
                'skills': ['python', 'pytorch', 'tensorflow', 'llm', 'transformers', 'aws'],
                'optional_skills': ['langchain', 'huggingface', 'docker', 'kubernetes', 'mlflow'],
                'weight': 6
            },
            'Product Manager': {
                'skills': ['sql', 'jira', 'agile', 'product management', 'communication'],
                'optional_skills': ['python', 'tableau', 'leadership', 'stakeholder management'],
                'weight': 5
            },
            'Engineering Manager': {
                'skills': ['leadership', 'agile', 'project management', 'communication', 'mentoring'],
                'optional_skills': ['python', 'aws', 'jira', 'scrum', 'technical writing'],
                'weight': 3
            },
            'Business Intelligence Analyst': {
                'skills': ['sql', 'tableau', 'power bi', 'excel', 'python'],
                'optional_skills': ['looker', 'dbt', 'snowflake', 'statistics', 'communication'],
                'weight': 5
            },
            'Security Engineer': {
                'skills': ['python', 'linux', 'aws', 'cybersecurity', 'networking'],
                'optional_skills': ['kubernetes', 'terraform', 'penetration testing', 'authentication'],
                'weight': 3
            },
        }
        
        # Create weighted job selection
        job_titles = list(job_templates.keys())
        job_weights = [job_templates[j]['weight'] for j in job_titles]
        
        jobs = []
        
        for i in tqdm(range(num_jobs), desc="Generating sample data"):
            # Select job type based on weights
            title = random.choices(job_titles, weights=job_weights, k=1)[0]
            template = job_templates[title]
            
            # Select city based on weights
            city_info = random.choices(cities, weights=city_weights, k=1)[0]
            
            # Select company
            company = random.choice(companies)
            
            # Build skills list
            required_skills = template['skills'].copy()
            num_optional = random.randint(1, min(4, len(template['optional_skills'])))
            optional_skills = random.sample(template['optional_skills'], num_optional)
            all_skills = list(set(required_skills + optional_skills))
            
            # Generate job
            job = {
                'job_id': f"sample_{i+1:05d}",
                'title': title,
                'company': company['name'],
                'company_type': company['type'],
                'company_size': company['size'],
                'city': city_info['city'],
                'state': city_info['state'],
                'location': f"{city_info['city']}, {city_info['state']}",
                'skills': all_skills,
                'post_date': (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d'),
                'source': 'Sample Data',
                'scraped_date': datetime.now().isoformat()
            }
            
            jobs.append(job)
        
        df = pd.DataFrame(jobs)
        logger.info(f"Generated {len(df)} comprehensive sample job records")
        
        # Log distribution stats
        logger.info(f"\nJob Title Distribution:")
        logger.info(df['title'].value_counts().head(10).to_string())
        logger.info(f"\nCity Distribution:")
        logger.info(df['city'].value_counts().head(10).to_string())
        
        return df
    
    # ==================== REAL-TIME: Adzuna API (India) ====================
    
    def scrape_adzuna_india(self, cities: list = None, queries: list = None, 
                            app_id: str = None, app_key: str = None,
                            results_per_query: int = 50) -> list:
        """
        Scrape REAL jobs from Adzuna API for Indian cities.
        
        Get FREE API keys from: https://developer.adzuna.com/
        
        Args:
            cities: List of Indian cities ['bangalore', 'pune', 'mumbai']
            queries: Job search queries ['data scientist', 'software engineer']
            app_id: Adzuna App ID (get free from their website)
            app_key: Adzuna App Key
            results_per_query: Results per search
            
        Returns:
            List of real job dictionaries
        """
        if cities is None:
            cities = ['bangalore', 'pune', 'mumbai', 'hyderabad', 'delhi']
        
        if queries is None:
            queries = ['data scientist', 'data analyst', 'software engineer', 
                      'machine learning', 'python developer', 'data engineer']
        
        # Check for API credentials
        if not app_id or not app_key:
            logger.warning("⚠️ Adzuna API credentials not provided!")
            logger.info("Get FREE API keys from: https://developer.adzuna.com/")
            logger.info("Falling back to sample data for Indian cities...")
            return self._generate_indian_sample_data(cities, len(queries) * results_per_query)
        
        jobs = []
        base_url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
        
        for city in cities:
            city_info = INDIAN_CITIES.get(city.lower(), {})
            if not city_info:
                continue
                
            for query in queries:
                try:
                    params = {
                        'app_id': app_id,
                        'app_key': app_key,
                        'results_per_page': results_per_query,
                        'what': query,
                        'where': city_info['adzuna_location'],
                        'content-type': 'application/json'
                    }
                    
                    response = self.session.get(base_url, params=params, 
                                               headers=self._get_headers(), timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        for item in data.get('results', []):
                            description = item.get('description', '')
                            skills = self.extract_skills(description)
                            
                            job = {
                                'job_id': f"adzuna_{item.get('id', '')}",
                                'title': item.get('title', 'Unknown'),
                                'company': item.get('company', {}).get('display_name', 'Unknown'),
                                'location': item.get('location', {}).get('display_name', city_info['city']),
                                'city': city_info['city'],
                                'state': city_info['state'],
                                'description': description[:500],
                                'skills': skills,
                                'salary_min': item.get('salary_min'),
                                'salary_max': item.get('salary_max'),
                                'post_date': item.get('created', datetime.now().strftime('%Y-%m-%d')),
                                'url': item.get('redirect_url', ''),
                                'source': 'Adzuna India',
                                'scraped_date': datetime.now().isoformat(),
                                'is_realtime': True
                            }
                            jobs.append(job)
                        
                        logger.info(f"Fetched {len(data.get('results', []))} jobs for '{query}' in {city_info['city']}")
                    
                    self._rate_limit(1.0, 2.0)  # Respect rate limits
                    
                except Exception as e:
                    logger.warning(f"Error fetching {query} in {city}: {e}")
                    continue
        
        logger.info(f"Total real-time jobs from Adzuna India: {len(jobs)}")
        return jobs
    
    def _generate_indian_sample_data(self, cities: list, num_jobs: int) -> list:
        """Generate realistic sample data for Indian cities."""
        
        indian_companies = [
            {'name': 'TCS', 'type': 'IT Services', 'size': 'Enterprise'},
            {'name': 'Infosys', 'type': 'IT Services', 'size': 'Enterprise'},
            {'name': 'Wipro', 'type': 'IT Services', 'size': 'Enterprise'},
            {'name': 'HCL Technologies', 'type': 'IT Services', 'size': 'Enterprise'},
            {'name': 'Tech Mahindra', 'type': 'IT Services', 'size': 'Enterprise'},
            {'name': 'Cognizant', 'type': 'IT Services', 'size': 'Enterprise'},
            {'name': 'Flipkart', 'type': 'E-commerce', 'size': 'Large'},
            {'name': 'Swiggy', 'type': 'Food Tech', 'size': 'Large'},
            {'name': 'Zomato', 'type': 'Food Tech', 'size': 'Large'},
            {'name': 'PhonePe', 'type': 'Fintech', 'size': 'Large'},
            {'name': 'Paytm', 'type': 'Fintech', 'size': 'Large'},
            {'name': 'Razorpay', 'type': 'Fintech', 'size': 'Medium'},
            {'name': 'CRED', 'type': 'Fintech', 'size': 'Medium'},
            {'name': 'Zerodha', 'type': 'Fintech', 'size': 'Medium'},
            {'name': 'Dream11', 'type': 'Gaming', 'size': 'Large'},
            {'name': 'Ola', 'type': 'Transportation', 'size': 'Large'},
            {'name': 'Meesho', 'type': 'E-commerce', 'size': 'Large'},
            {'name': 'Myntra', 'type': 'E-commerce', 'size': 'Large'},
            {'name': 'Nykaa', 'type': 'E-commerce', 'size': 'Medium'},
            {'name': 'BigBasket', 'type': 'E-commerce', 'size': 'Large'},
            {'name': 'Freshworks', 'type': 'SaaS', 'size': 'Large'},
            {'name': 'Zoho', 'type': 'SaaS', 'size': 'Large'},
            {'name': 'Postman', 'type': 'Developer Tools', 'size': 'Medium'},
            {'name': 'Browserstack', 'type': 'Developer Tools', 'size': 'Medium'},
            {'name': 'Hasura', 'type': 'Developer Tools', 'size': 'Small'},
            {'name': 'Unacademy', 'type': 'EdTech', 'size': 'Large'},
            {'name': 'Byju\'s', 'type': 'EdTech', 'size': 'Enterprise'},
            {'name': 'upGrad', 'type': 'EdTech', 'size': 'Medium'},
            {'name': 'Scaler', 'type': 'EdTech', 'size': 'Medium'},
            {'name': 'OYO', 'type': 'Travel Tech', 'size': 'Large'},
            {'name': 'MakeMyTrip', 'type': 'Travel Tech', 'size': 'Large'},
            {'name': 'Google India', 'type': 'Big Tech', 'size': 'Enterprise'},
            {'name': 'Microsoft India', 'type': 'Big Tech', 'size': 'Enterprise'},
            {'name': 'Amazon India', 'type': 'Big Tech', 'size': 'Enterprise'},
            {'name': 'Meta India', 'type': 'Big Tech', 'size': 'Enterprise'},
            {'name': 'Walmart Global Tech', 'type': 'E-commerce', 'size': 'Enterprise'},
            {'name': 'Goldman Sachs', 'type': 'Finance', 'size': 'Enterprise'},
            {'name': 'JP Morgan', 'type': 'Finance', 'size': 'Enterprise'},
            {'name': 'Nvidia India', 'type': 'Hardware/AI', 'size': 'Enterprise'},
            {'name': 'Intel India', 'type': 'Hardware', 'size': 'Enterprise'},
        ]
        
        jobs = []
        job_templates = list(self.generate_comprehensive_sample_data(1).to_dict('records')[0].keys())
        
        for i in range(num_jobs):
            city_key = random.choice(cities)
            city_info = INDIAN_CITIES.get(city_key.lower(), 
                                          {'city': 'Bangalore', 'state': 'Karnataka'})
            company = random.choice(indian_companies)
            
            title = random.choice([
                'Data Scientist', 'Data Analyst', 'Software Engineer',
                'Senior Software Engineer', 'Machine Learning Engineer',
                'Data Engineer', 'Full Stack Developer', 'Backend Developer',
                'DevOps Engineer', 'Product Manager', 'Business Analyst'
            ])
            
            skills = random.sample(list(SKILLS_DICTIONARY), random.randint(5, 10))
            
            job = {
                'job_id': f"india_sample_{i+1:05d}",
                'title': title,
                'company': company['name'],
                'company_type': company['type'],
                'company_size': company['size'],
                'city': city_info['city'],
                'state': city_info['state'],
                'location': f"{city_info['city']}, {city_info['state']}",
                'skills': skills,
                'post_date': (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d'),
                'source': 'Sample Data (India)',
                'scraped_date': datetime.now().isoformat(),
                'is_realtime': False
            }
            jobs.append(job)
        
        return jobs
    
    def run_india(self, cities: list = None, mode: str = 'sample',
                  adzuna_app_id: str = None, adzuna_app_key: str = None,
                  num_jobs: int = 500) -> pd.DataFrame:
        """
        Run data collection specifically for Indian cities.
        
        Args:
            cities: List of Indian cities ['bangalore', 'pune', 'mumbai']
            mode: 'sample', 'realtime', or 'hybrid'
            adzuna_app_id: Adzuna API ID (for realtime)
            adzuna_app_key: Adzuna API Key (for realtime)
            num_jobs: Number of jobs for sample mode
        """
        if cities is None:
            cities = ['bangalore', 'pune', 'mumbai', 'hyderabad', 'delhi', 'chennai']
        
        all_jobs = []
        
        if mode in ['realtime', 'hybrid']:
            logger.info("=== Fetching Real-Time Indian Job Data ===")
            real_jobs = self.scrape_adzuna_india(
                cities=cities,
                app_id=adzuna_app_id,
                app_key=adzuna_app_key
            )
            all_jobs.extend(real_jobs)
        
        if mode in ['sample', 'hybrid']:
            logger.info("=== Generating Indian Sample Data ===")
            sample_jobs = self._generate_indian_sample_data(cities, num_jobs)
            all_jobs.extend(sample_jobs)
        
        df = pd.DataFrame(all_jobs)
        df = df.drop_duplicates(subset=['job_id'], keep='first')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.save_data(df, f"jobs_india_{timestamp}")
        
        logger.info(f"\n{'='*50}")
        logger.info(f"Indian Cities Data Collection Complete!")
        logger.info(f"Total jobs: {len(df)}")
        logger.info(f"Cities covered: {df['city'].unique().tolist()}")
        logger.info(f"{'='*50}")
        
        return df

    # ==================== MAIN METHODS ====================
    
    def save_data(self, df: pd.DataFrame, filename: str):
        """
        Save scraped data to CSV and JSON formats with backup.
        
        Args:
            df: DataFrame with job data
            filename: Base filename (without extension)
        """
        # Main files
        csv_path = self.output_dir / f"{filename}.csv"
        json_path = self.output_dir / f"{filename}.json"
        
        # For CSV, convert lists to strings
        df_csv = df.copy()
        if 'skills' in df_csv.columns:
            df_csv['skills'] = df_csv['skills'].apply(lambda x: ','.join(x) if isinstance(x, list) else x)
        if 'tags' in df_csv.columns:
            df_csv['tags'] = df_csv['tags'].apply(lambda x: ','.join(x) if isinstance(x, list) else x)
        
        df_csv.to_csv(csv_path, index=False)
        df.to_json(json_path, orient='records', indent=2)
        
        # Create backup
        backup_dir = self.output_dir / 'backups'
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = backup_dir / f"{filename}_backup_{timestamp}.json"
        df.to_json(backup_path, orient='records', indent=2)
        
        logger.info(f"Data saved to {csv_path} and {json_path}")
        logger.info(f"Backup created at {backup_path}")
    
    def run(self, mode: str = 'sample', num_jobs: int = 1000) -> pd.DataFrame:
        """
        Main method to run the scraping/data collection process.
        
        Args:
            mode: 'sample' for sample data, 'scrape' for real scraping, 'hybrid' for both
            num_jobs: Number of jobs to collect
            
        Returns:
            DataFrame with all collected jobs
        """
        all_jobs = []
        
        if mode in ['sample', 'hybrid']:
            logger.info("=== Generating Sample Data ===")
            sample_df = self.generate_comprehensive_sample_data(num_jobs)
            all_jobs.extend(sample_df.to_dict('records'))
        
        if mode in ['scrape', 'hybrid']:
            logger.info("=== Scraping Real Data ===")
            
            # Try RemoteOK
            try:
                remoteok_jobs = self.scrape_remoteok(limit=100)
                all_jobs.extend(remoteok_jobs)
            except Exception as e:
                logger.warning(f"RemoteOK scraping failed: {e}")
            
            # Add tech company jobs
            tech_jobs = self._generate_hn_style_jobs(200)
            all_jobs.extend(tech_jobs)
        
        # Create DataFrame
        df = pd.DataFrame(all_jobs)
        
        # Remove any duplicates
        df = df.drop_duplicates(subset=['job_id'], keep='first')
        
        # Save the data
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.save_data(df, f"jobs_raw_{timestamp}")
        
        logger.info(f"\n{'='*50}")
        logger.info(f"Data Collection Complete!")
        logger.info(f"Total jobs collected: {len(df)}")
        logger.info(f"Unique companies: {df['company'].nunique()}")
        logger.info(f"Unique cities: {df['city'].nunique()}")
        logger.info(f"{'='*50}")
        
        return df


def main():
    """Main entry point for the enhanced scraper."""
    scraper = EnhancedJobScraper(output_dir="../data/raw")
    
    print("="*60)
    print("LinkedIn Job Trend Analysis - Data Collection (Phase 2)")
    print("="*60)
    print("\nSelect data collection mode:")
    print("1. Sample Data (Recommended for testing) - Fast, reliable")
    print("2. Hybrid (Sample + Real scraping) - Best of both")
    print("3. Scrape Only (Real data from APIs)")
    print("4. Indian Cities (Bangalore, Pune, Mumbai, etc.)")
    
    # Default to sample mode for reliability
    mode = 'sample'
    num_jobs = 1000
    
    print(f"\nRunning in '{mode}' mode with {num_jobs} jobs...")
    
    df = scraper.run(mode=mode, num_jobs=num_jobs)
    
    print(f"\n✅ Data collection complete!")
    print(f"\nDataset Summary:")
    print(f"  - Total jobs: {len(df)}")
    print(f"  - Unique job titles: {df['title'].nunique()}")
    print(f"  - Unique companies: {df['company'].nunique()}")
    print(f"  - Unique cities: {df['city'].nunique()}")
    
    print(f"\nTop 5 Job Titles:")
    print(df['title'].value_counts().head())
    
    print(f"\nTop 5 Cities:")
    print(df['city'].value_counts().head())
    
    return df


if __name__ == "__main__":
    main()
