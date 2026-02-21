"""
Skills Configuration Loader
============================
Centralized loader for shared skills data used across all modules.
All skill definitions live in config/skills_config.json (single source of truth).
"""

import json
from pathlib import Path

_CONFIG_FILE = Path(__file__).parent.parent / 'config' / 'skills_config.json'

def _load_config() -> dict:
    """Load skills configuration from JSON file."""
    with open(_CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

_config = _load_config()

# Master set of all recognized skills
SKILLS_DICTIONARY: set = set(_config['skills_dictionary'])

# Category -> list of skills mapping
SKILL_CATEGORIES: dict = _config['skill_categories']

# Short alias -> canonical skill name
SKILL_ALIASES: dict = _config['skill_aliases']

# Variant spelling -> canonical skill name (for cleaning/normalization)
SKILL_NORMALIZATION: dict = _config['skill_normalization']

# Subset of skills to track trends over time
SKILLS_TO_TRACK: list = _config['skills_to_track']

# Subset of skills for job description analysis
TECH_SKILLS: list = _config['tech_skills']
