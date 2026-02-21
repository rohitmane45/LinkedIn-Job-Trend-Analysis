"""
Shared test fixtures for LinkedIn Job Analysis tests.
"""

import sys
import pytest
from pathlib import Path

# Add scripts directory to path so tests can import modules
SCRIPTS_DIR = Path(__file__).parent.parent / 'scripts'
sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture
def sample_job():
    """A single sample job record."""
    return {
        'job_id': 'test_001',
        'title': 'Senior Data Scientist',
        'company': 'Acme Corp',
        'location': 'Bangalore, Karnataka',
        'city': 'Bangalore',
        'state': 'Karnataka',
        'description': 'We need a senior data scientist with python, machine learning, sql, and aws skills. 5+ years experience required.',
        'skills': ['python', 'machine learning', 'sql', 'aws'],
        'post_date': '2026-01-15',
        'source': 'Test',
    }


@pytest.fixture
def sample_jobs_list(sample_job):
    """A list of sample job records for batch operations."""
    return [
        sample_job,
        {
            'job_id': 'test_002',
            'title': 'Frontend Engineer',
            'company': 'Widget Inc',
            'location': 'Remote, USA',
            'city': 'Remote',
            'state': 'USA',
            'description': 'Looking for a react, typescript, and css expert.',
            'skills': ['react', 'typescript', 'css'],
            'post_date': '2026-01-20',
            'source': 'Test',
        },
        {
            'job_id': 'test_003',
            'title': 'DevOps Engineer',
            'company': 'CloudCo',
            'location': 'Mumbai, Maharashtra',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'description': 'Need experience with docker, kubernetes, terraform, aws, and ci/cd pipelines. 3 years minimum.',
            'skills': ['docker', 'kubernetes', 'terraform', 'aws', 'ci/cd'],
            'post_date': '2026-01-25',
            'source': 'Test',
        },
    ]


@pytest.fixture
def sample_user_profile():
    """A sample user profile for resume matching tests."""
    return {
        'name': 'Test User',
        'title': 'Data Scientist',
        'experience_years': 4,
        'skills': ['python', 'sql', 'machine learning', 'pandas', 'aws'],
        'preferred_locations': ['Bangalore', 'Remote'],
        'preferred_companies': ['Acme Corp'],
        'min_salary_lpa': 15,
        'job_types': ['remote', 'hybrid'],
        'industries': [],
    }
