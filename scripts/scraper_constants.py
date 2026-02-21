"""
Scraper constants extracted from scraper_v2.py for maintainability.
"""

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/121.0.0.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
]

INDIAN_CITIES = {
    'bangalore': {'city': 'Bangalore', 'state': 'Karnataka', 'adzuna_location': 'bangalore'},
    'mumbai': {'city': 'Mumbai', 'state': 'Maharashtra', 'adzuna_location': 'mumbai'},
    'pune': {'city': 'Pune', 'state': 'Maharashtra', 'adzuna_location': 'pune'},
    'hyderabad': {'city': 'Hyderabad', 'state': 'Telangana', 'adzuna_location': 'hyderabad'},
    'chennai': {'city': 'Chennai', 'state': 'Tamil Nadu', 'adzuna_location': 'chennai'},
    'delhi': {'city': 'Delhi', 'state': 'Delhi NCR', 'adzuna_location': 'delhi'},
    'noida': {'city': 'Noida', 'state': 'Uttar Pradesh', 'adzuna_location': 'noida'},
    'gurgaon': {'city': 'Gurgaon', 'state': 'Haryana', 'adzuna_location': 'gurgaon'},
    'kolkata': {'city': 'Kolkata', 'state': 'West Bengal', 'adzuna_location': 'kolkata'},
    'ahmedabad': {'city': 'Ahmedabad', 'state': 'Gujarat', 'adzuna_location': 'ahmedabad'},
}
