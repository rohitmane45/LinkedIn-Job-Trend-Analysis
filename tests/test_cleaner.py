"""Tests for cleaner.py — title standardization, skill normalization, location parsing."""

from cleaner import JobDataCleaner
import pandas as pd


class TestTitleStandardization:
    """Test job title standardization."""

    def test_data_scientist_match(self):
        cleaner = JobDataCleaner()
        result = cleaner.standardize_job_title('Senior Data Scientist')
        assert result == 'Data Scientist'

    def test_software_engineer_match(self):
        cleaner = JobDataCleaner()
        result = cleaner.standardize_job_title('Software Developer')
        assert result == 'Software Engineer'

    def test_devops_match(self):
        cleaner = JobDataCleaner()
        result = cleaner.standardize_job_title('Site Reliability Engineer')
        assert result == 'DevOps Engineer'

    def test_unknown_title_returns_cleaned(self):
        cleaner = JobDataCleaner()
        result = cleaner.standardize_job_title('  chief happiness officer  ')
        assert result == 'Chief Happiness Officer'

    def test_nan_returns_unknown(self):
        cleaner = JobDataCleaner()
        result = cleaner.standardize_job_title(float('nan'))
        assert result == 'Unknown'


class TestSkillNormalization:
    """Test skill normalization via centralized config."""

    def test_normalizes_variant(self):
        cleaner = JobDataCleaner()
        assert cleaner.normalize_skill('powerbi') == 'power bi'

    def test_normalizes_tensorflow_variant(self):
        cleaner = JobDataCleaner()
        assert cleaner.normalize_skill('tensor flow') == 'tensorflow'

    def test_passes_through_unknown(self):
        cleaner = JobDataCleaner()
        result = cleaner.normalize_skill('obscure_tool')
        assert result == 'obscure_tool'

    def test_nan_returns_none(self):
        cleaner = JobDataCleaner()
        assert cleaner.normalize_skill(float('nan')) is None


class TestLocationParsing:
    """Test location standardization."""

    def test_remote(self):
        cleaner = JobDataCleaner()
        city, state = cleaner.standardize_location('Remote - Anywhere')
        assert city == 'Remote'
        assert state == 'USA'

    def test_city_state_split(self):
        cleaner = JobDataCleaner()
        city, state = cleaner.standardize_location('San Francisco, CA')
        assert city == 'San Francisco'
        assert state == 'CA'

    def test_city_alias(self):
        cleaner = JobDataCleaner()
        city, _ = cleaner.standardize_location('NYC, NY')
        assert city == 'New York'

    def test_nan_returns_unknown(self):
        cleaner = JobDataCleaner()
        city, state = cleaner.standardize_location(float('nan'))
        assert city == 'Unknown'


class TestDuplicateRemoval:
    """Test duplicate removal."""

    def test_removes_exact_duplicates(self):
        cleaner = JobDataCleaner()
        df = pd.DataFrame([
            {'title_standardized': 'Data Scientist', 'company': 'Acme', 'city': 'SF'},
            {'title_standardized': 'Data Scientist', 'company': 'Acme', 'city': 'SF'},
            {'title_standardized': 'Engineer', 'company': 'Acme', 'city': 'SF'},
        ])
        result = cleaner.remove_duplicates(df)
        assert len(result) == 2
