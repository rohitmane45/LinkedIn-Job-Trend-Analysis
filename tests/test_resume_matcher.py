"""Tests for resume_matcher.py — match scoring and skill gap analysis."""

from resume_matcher import ResumeMatcher, UserProfile


def _make_profile(**overrides):
    """Create a test UserProfile with defaults."""
    defaults = {
        'name': 'Test',
        'title': 'Data Scientist',
        'experience_years': 3,
        'skills': ['python', 'sql', 'machine learning'],
        'preferred_locations': ['Bangalore'],
        'preferred_companies': [],
        'min_salary_lpa': 10,
        'job_types': ['remote'],
        'industries': [],
    }
    defaults.update(overrides)
    return UserProfile.from_dict(defaults)


class TestMatchScoring:
    """Test match score computation."""

    def test_perfect_skill_match(self):
        profile = _make_profile(skills=['python', 'sql'])
        matcher = ResumeMatcher(profile)
        job = {
            'title': 'Data Scientist',
            'company': 'Test Corp',
            'location': 'Bangalore',
            'description': 'Need python and sql experience.',
        }
        score, breakdown = matcher.calculate_match_score(job)
        assert score > 50
        assert breakdown['skills']['score'] > 0

    def test_no_skill_overlap_low_score(self):
        profile = _make_profile(skills=['java', 'kotlin'])
        matcher = ResumeMatcher(profile)
        job = {
            'title': 'Frontend Developer',
            'company': 'Web Inc',
            'location': 'Mumbai',
            'description': 'Need react and css expert.',
        }
        score, _ = matcher.calculate_match_score(job)
        assert score < 50

    def test_location_match_adds_score(self):
        profile = _make_profile(preferred_locations=['Bangalore'])
        matcher = ResumeMatcher(profile)
        job_match = {
            'title': 'Engineer',
            'company': 'A',
            'location': 'Bangalore, KA',
            'description': 'python',
        }
        job_no_match = {
            'title': 'Engineer',
            'company': 'A',
            'location': 'Mumbai, MH',
            'description': 'python',
        }
        score_match, _ = matcher.calculate_match_score(job_match)
        score_no, _ = matcher.calculate_match_score(job_no_match)
        assert score_match > score_no

    def test_score_between_0_and_100(self):
        profile = _make_profile()
        matcher = ResumeMatcher(profile)
        job = {
            'title': 'Data Scientist',
            'company': 'Test',
            'location': 'Bangalore',
            'description': 'python sql machine learning remote',
        }
        score, _ = matcher.calculate_match_score(job)
        assert 0 <= score <= 100


class TestSkillGapAnalysis:
    """Test skill gap analysis."""

    def test_identifies_gaps(self, sample_jobs_list):
        profile = _make_profile(skills=['python'])
        matcher = ResumeMatcher(profile)
        matcher.jobs = sample_jobs_list
        gaps = matcher.analyze_skill_gaps()
        assert 'skills_you_have' in gaps
        assert 'skills_to_learn' in gaps
        assert gaps['your_skill_count'] == 1

    def test_full_coverage(self, sample_jobs_list):
        # Give the user every possible skill
        all_skills = set()
        for job in sample_jobs_list:
            desc = str(job.get('description', ''))
            for category_skills in ResumeMatcher.SKILL_CATEGORIES.values():
                for s in category_skills:
                    if s in desc.lower():
                        all_skills.add(s)
        profile = _make_profile(skills=list(all_skills))
        matcher = ResumeMatcher(profile)
        matcher.jobs = sample_jobs_list
        gaps = matcher.analyze_skill_gaps()
        # Should have high coverage
        assert gaps['coverage_percent'] >= 50
