"""Tests for analyze_jobs.py — skill extraction, title analysis, experience detection."""

import pandas as pd
from analyze_jobs import JobAnalyzer


class TestSkillExtraction:
    """Test skill extraction from job descriptions."""

    def test_extracts_known_skills(self):
        analyzer = JobAnalyzer()
        analyzer.df = pd.DataFrame([
            {'description': 'We need python, sql, and aws experience.', 'title': 'Data Engineer'},
        ])
        result = analyzer.extract_skills()
        assert 'python' in result['data']
        assert 'sql' in result['data']
        assert 'aws' in result['data']

    def test_no_false_positives_on_empty(self):
        analyzer = JobAnalyzer()
        analyzer.df = pd.DataFrame([
            {'description': 'We need a friendly person.', 'title': 'Greeter'},
        ])
        result = analyzer.extract_skills()
        # Should not find skills that aren't there
        assert result['data'].get('kubernetes', 0) == 0

    def test_missing_description_column(self):
        analyzer = JobAnalyzer()
        analyzer.df = pd.DataFrame([{'title': 'Test'}])
        result = analyzer.extract_skills()
        assert result == {}


class TestJobTitleAnalysis:
    """Test job title counting."""

    def test_top_titles(self):
        analyzer = JobAnalyzer()
        analyzer.df = pd.DataFrame([
            {'title': 'Data Scientist'},
            {'title': 'Data Scientist'},
            {'title': 'Software Engineer'},
        ])
        result = analyzer.analyze_job_titles(top_n=5)
        assert result['data']['Data Scientist'] == 2
        assert result['total_unique'] == 2

    def test_missing_title_column(self):
        analyzer = JobAnalyzer()
        analyzer.df = pd.DataFrame([{'company': 'Acme'}])
        result = analyzer.analyze_job_titles()
        assert result == {}


class TestExperienceLevels:
    """Test experience level detection from descriptions."""

    def test_detects_senior(self):
        analyzer = JobAnalyzer()
        analyzer.df = pd.DataFrame([
            {'description': 'Senior engineer with 8+ years of experience'},
        ])
        result = analyzer.analyze_experience_levels()
        assert result['Senior (6-10 yrs)'] >= 1

    def test_detects_entry_level(self):
        analyzer = JobAnalyzer()
        analyzer.df = pd.DataFrame([
            {'description': 'Entry level position for freshers with 0-2 years'},
        ])
        result = analyzer.analyze_experience_levels()
        assert result['Entry Level (0-2 yrs)'] >= 1
