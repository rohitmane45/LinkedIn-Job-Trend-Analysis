"""Tests for the resume PDF parser module."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from resume_parser import extract_skills, extract_experience_years, extract_title, extract_locations, parse_resume_text


class TestSkillExtraction:
    """Test skill extraction from text."""

    def test_extracts_common_skills(self):
        text = "Proficient in Python, SQL, and machine learning."
        skills = extract_skills(text)
        assert "python" in skills
        assert "sql" in skills
        assert "machine learning" in skills

    def test_extracts_from_mixed_case(self):
        text = "Experience with Docker, Kubernetes, and AWS."
        skills = extract_skills(text)
        assert "docker" in skills
        assert "kubernetes" in skills
        assert "aws" in skills

    def test_aliases_resolved(self):
        text = "Worked with k8s, node, and postgres clusters."
        skills = extract_skills(text)
        assert "kubernetes" in skills
        assert "node.js" in skills
        assert "postgresql" in skills

    def test_normalization_applied(self):
        text = "Skilled in pyspark, reactjs, and sklearn."
        skills = extract_skills(text)
        assert "spark" in skills
        assert "react" in skills
        assert "scikit-learn" in skills

    def test_empty_text(self):
        assert extract_skills("") == []

    def test_no_skills_in_text(self):
        assert extract_skills("I enjoy hiking and cooking.") == []


class TestExperienceExtraction:

    def test_years_of_experience(self):
        assert extract_experience_years("5+ years of experience in data science") == 5

    def test_yrs_experience(self):
        assert extract_experience_years("Over 3 yrs experience in development") == 3

    def test_experience_colon_format(self):
        assert extract_experience_years("Experience: 7 years") == 7

    def test_years_in(self):
        assert extract_experience_years("8 years in software engineering") == 8

    def test_no_experience_mentioned(self):
        assert extract_experience_years("I am a fresh graduate.") == 0


class TestTitleExtraction:

    def test_data_scientist(self):
        assert extract_title("Senior Data Scientist at Google") == "Senior Data Scientist"

    def test_software_engineer(self):
        assert extract_title("I work as a Software Engineer") == "Software Engineer"

    def test_devops_engineer(self):
        assert extract_title("Current role: DevOps Engineer") == "Devops Engineer"

    def test_no_title_found(self):
        assert extract_title("I like to work on interesting projects") == ""


class TestLocationExtraction:

    def test_bangalore(self):
        locs = extract_locations("Based in Bangalore, Karnataka")
        assert "Bangalore" in locs

    def test_multiple_cities(self):
        locs = extract_locations("Worked in Mumbai and Delhi offices")
        assert "Mumbai" in locs
        assert "Delhi" in locs

    def test_remote(self):
        locs = extract_locations("Open to Remote opportunities")
        assert "Remote" in locs

    def test_no_locations(self):
        assert extract_locations("I live somewhere in Europe.") == []


class TestFullParsing:

    def test_parse_resume_text_returns_profile(self):
        text = (
            "Senior Data Scientist with 5 years of experience. "
            "Skills: Python, SQL, Machine Learning, AWS, Docker. "
            "Based in Bangalore. Open to Remote."
        )
        profile = parse_resume_text(text)
        assert profile["title"] == "Senior Data Scientist"
        assert profile["experience_years"] == 5
        assert "python" in profile["skills"]
        assert "Bangalore" in profile["preferred_locations"]
        assert "Remote" in profile["preferred_locations"]

    def test_parse_empty_text(self):
        profile = parse_resume_text("")
        assert profile["skills"] == []
        assert profile["experience_years"] == 0
