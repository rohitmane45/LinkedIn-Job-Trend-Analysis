"""
Resume PDF Parser
==================
Extract skills, job title, and experience from a PDF resume
and create a UserProfile for job matching.

Usage:
    python resume_parser.py --pdf resume.pdf
    python resume_parser.py --pdf resume.pdf --save   # Save as user_profile.json
    python resume_parser.py --text "I am a data scientist with 5 years..."
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import re
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set

from skills_loader import SKILLS_DICTIONARY, SKILL_ALIASES, SKILL_NORMALIZATION

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
PROFILE_FILE = CONFIG_DIR / "user_profile.json"


# ──────────────────────────────────────────────────────────────
# PDF text extraction
# ──────────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file using pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        raise ImportError(
            "pdfplumber is required for PDF parsing. "
            "Install it with: pip install pdfplumber"
        )

    text_parts: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    return "\n".join(text_parts)


# ──────────────────────────────────────────────────────────────
# Skill extraction
# ──────────────────────────────────────────────────────────────

def extract_skills(text: str) -> List[str]:
    """
    Extract recognized skills from free text.

    Matches against the centralized skills_config.json dictionary
    and applies alias/normalization resolution.
    """
    text_lower = text.lower()
    found: Set[str] = set()

    # 1. Direct match against known skills (longest first to avoid partial matches)
    sorted_skills = sorted(SKILLS_DICTIONARY, key=len, reverse=True)
    for skill in sorted_skills:
        # Word-boundary match to avoid e.g. "r" matching inside "react"
        pattern = r'(?<!\w)' + re.escape(skill) + r'(?!\w)'
        if re.search(pattern, text_lower):
            found.add(skill)

    # 2. Check aliases
    for alias, canonical in SKILL_ALIASES.items():
        pattern = r'(?<!\w)' + re.escape(alias) + r'(?!\w)'
        if re.search(pattern, text_lower):
            found.add(canonical)

    # 3. Check normalization variants
    for variant, canonical in SKILL_NORMALIZATION.items():
        pattern = r'(?<!\w)' + re.escape(variant) + r'(?!\w)'
        if re.search(pattern, text_lower):
            found.add(canonical)

    # Sort alphabetically for consistent output
    return sorted(found)


# ──────────────────────────────────────────────────────────────
# Experience extraction
# ──────────────────────────────────────────────────────────────

_EXP_PATTERNS = [
    # "5+ years of experience", "5 years experience"
    r'(\d{1,2})\+?\s*(?:years?|yrs?)[\s\w]*(?:of\s+)?(?:experience|exp)',
    # "experience: 5 years"
    r'experience[\s:]*(\d{1,2})\+?\s*(?:years?|yrs?)',
    # Fallback: "X years in ..."
    r'(\d{1,2})\+?\s*(?:years?|yrs?)\s+(?:in|of|working)',
    # "worked for 3 years"
    r'worked\s+(?:for\s+)?(\d{1,2})\+?\s*(?:years?|yrs?)',
]


def _estimate_from_graduation(text: str) -> int:
    """Estimate experience from graduation year."""
    current_year = datetime.now().year
    patterns = [
        r'(?:graduated?|batch|class\s+of|passing\s+year)[:\s]*(20\d{2})',
        r'(20\d{2})[\s-]+(?:20\d{2})?[\s]*(?:b\.?\s*(?:tech|e|sc|eng|ca))',
        r'(?:b\.?\s*(?:tech|e|sc|eng|ca))[^\n]{0,30}(20\d{2})',
    ]
    for pat in patterns:
        m = re.search(pat, text.lower())
        if m:
            grad_year = int(m.group(1))
            if 2000 <= grad_year <= current_year:
                return max(0, current_year - grad_year)
    return 0


def extract_experience_years(text: str) -> int:
    """Extract years of experience from resume text."""
    text_lower = text.lower()

    # Check for fresher / intern keywords
    if re.search(r'\b(?:fresher|fresh graduate|entry[- ]level)\b', text_lower):
        return 0

    for pattern in _EXP_PATTERNS:
        match = re.search(pattern, text_lower)
        if match:
            return int(match.group(1))

    # Fallback: estimate from graduation year
    grad_exp = _estimate_from_graduation(text)
    if grad_exp > 0:
        return grad_exp

    return 0


# ──────────────────────────────────────────────────────────────
# Title extraction
# ──────────────────────────────────────────────────────────────

_COMMON_TITLES = [
    # Executive / Senior
    "chief technology officer", "cto", "vp of engineering",
    "director of engineering", "engineering manager",
    "principal engineer", "staff engineer",
    "senior software engineer", "senior developer",
    "senior data scientist", "senior data engineer",
    "senior machine learning engineer", "senior ml engineer",
    "senior frontend engineer", "senior backend engineer",
    "senior full stack developer", "senior devops engineer",
    # Mid-level
    "software engineer", "software developer",
    "data scientist", "data analyst", "data engineer",
    "machine learning engineer", "ml engineer",
    "frontend engineer", "frontend developer",
    "backend engineer", "backend developer",
    "full stack developer", "full stack engineer",
    "devops engineer", "cloud engineer", "sre",
    "product manager", "project manager",
    "qa engineer", "test engineer",
    "business analyst", "solutions architect",
    "web developer", "mobile developer",
    "android developer", "ios developer",
    "python developer", "java developer",
    # Intern / Entry-level
    "data science intern", "software intern", "ml intern",
    "machine learning intern", "web development intern",
    "software engineering intern", "data analyst intern",
    "data engineering intern", "research intern",
    # Aspirant / student titles
    "aspiring data scientist", "aspiring data analyst",
    "aspiring software engineer", "aspiring ml engineer",
    "data science enthusiast", "ml enthusiast",
]

# Skill-to-title fallback: if no explicit title found, infer from skills
_SKILL_TITLE_MAP = {
    "data science": "Data Science Professional",
    "machine learning": "ML / Data Science Professional",
    "deep learning": "ML / Data Science Professional",
    "data analysis": "Data Analyst",
    "web development": "Web Developer",
    "android": "Android Developer",
    "ios": "iOS Developer",
    "flutter": "Mobile Developer",
    "react": "Frontend Developer",
    "angular": "Frontend Developer",
    "node": "Backend Developer",
    "devops": "DevOps Engineer",
    "cloud": "Cloud Engineer",
}


def extract_title(text: str) -> str:
    """Extract the most likely job title from resume text."""
    text_lower = text.lower()

    # 1. Try exact title match (longest first)
    for title in sorted(_COMMON_TITLES, key=len, reverse=True):
        if title in text_lower:
            return title.title()

    # 2. Look for "objective" / "career goal" sections for title hints
    obj_patterns = [
        r'(?:objective|career\s*(?:goal|objective|summary))[:\s]+[^.]*?((?:data|software|ml|machine learning|web|full.?stack|backend|frontend|devops|cloud)\s*(?:scientist|engineer|developer|analyst|intern))',
    ]
    for pat in obj_patterns:
        m = re.search(pat, text_lower)
        if m:
            return m.group(1).strip().title()

    # 3. Fallback: infer from detected skills
    for keyword, fallback_title in _SKILL_TITLE_MAP.items():
        if keyword in text_lower:
            return fallback_title

    return ""


# ──────────────────────────────────────────────────────────────
# Location extraction
# ──────────────────────────────────────────────────────────────

_INDIAN_CITIES = [
    "bangalore", "bengaluru", "mumbai", "delhi", "new delhi",
    "hyderabad", "pune", "chennai", "kolkata", "noida",
    "gurgaon", "gurugram", "ahmedabad", "jaipur", "lucknow",
    "chandigarh", "indore", "kochi", "thiruvananthapuram",
    "coimbatore", "nagpur", "visakhapatnam", "bhubaneswar",
]


def extract_locations(text: str) -> List[str]:
    """Extract city names from resume text."""
    text_lower = text.lower()
    found = []
    for city in _INDIAN_CITIES:
        if city in text_lower:
            found.append(city.title())
    # Also check for "Remote"
    if "remote" in text_lower:
        found.append("Remote")
    return found


# ──────────────────────────────────────────────────────────────
# Full parser
# ──────────────────────────────────────────────────────────────

def parse_resume_text(text: str) -> Dict:
    """
    Parse resume text and return a profile dict compatible with UserProfile.

    Returns:
        dict with keys: name, title, experience_years, skills,
        preferred_locations, preferred_companies, min_salary_lpa, job_types
    """
    skills = extract_skills(text)
    title = extract_title(text)
    experience = extract_experience_years(text)
    locations = extract_locations(text)

    return {
        "name": "",  # Cannot reliably extract name
        "title": title,
        "experience_years": experience,
        "skills": skills,
        "preferred_locations": locations,
        "preferred_companies": [],
        "min_salary_lpa": 0,
        "job_types": [],
        "industries": [],
        "source": "pdf_parser",
    }


def parse_pdf(pdf_path: str) -> Dict:
    """Parse a PDF resume file and return a profile dict."""
    text = extract_text_from_pdf(pdf_path)
    if not text.strip():
        return {"error": "Could not extract any text from the PDF"}
    profile = parse_resume_text(text)
    profile["_raw_text_length"] = len(text)
    return profile


# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Parse a PDF resume into a job-matching profile")
    parser.add_argument("--pdf", type=str, help="Path to the PDF resume")
    parser.add_argument("--text", type=str, help="Raw resume text (instead of PDF)")
    parser.add_argument("--save", action="store_true", help="Save result as user_profile.json")

    args = parser.parse_args()

    if not args.pdf and not args.text:
        parser.print_help()
        print("\nExamples:")
        print("  python resume_parser.py --pdf resume.pdf")
        print("  python resume_parser.py --pdf resume.pdf --save")
        print('  python resume_parser.py --text "Senior Python developer with 5 years..."')
        return

    if args.pdf:
        if not Path(args.pdf).exists():
            print(f"\n[X] File not found: {args.pdf}")
            print("    Please provide the full path to your PDF resume.")
            print(f'    Example: python resume_parser.py --pdf "C:\\Users\\you\\Documents\\resume.pdf"')
            return
        profile = parse_pdf(args.pdf)
    else:
        profile = parse_resume_text(args.text)

    print("\n" + "=" * 60)
    print("PARSED RESUME PROFILE")
    print("=" * 60)
    print(f"  Title:       {profile.get('title') or '(not detected)'}")
    print(f"  Experience:  {profile.get('experience_years', 0)} years")
    print(f"  Skills:      {', '.join(profile.get('skills', [])) or '(none detected)'}")
    print(f"  Locations:   {', '.join(profile.get('preferred_locations', [])) or '(none detected)'}")
    print("=" * 60)

    if args.save:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        # Merge with existing profile if present
        existing = {}
        if PROFILE_FILE.exists():
            with open(PROFILE_FILE, 'r', encoding='utf-8') as f:
                existing = json.load(f)

        # Only overwrite fields that the parser found
        for key in ["title", "skills", "preferred_locations"]:
            if profile.get(key):
                existing[key] = profile[key]
        if profile.get("experience_years", 0) > 0:
            existing["experience_years"] = profile["experience_years"]

        with open(PROFILE_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        print(f"\n[OK] Profile saved to {PROFILE_FILE}")


if __name__ == "__main__":
    main()
