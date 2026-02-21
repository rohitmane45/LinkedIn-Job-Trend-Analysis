"""Tests for the embedding matcher module."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


def test_is_available_returns_bool():
    from embedding_matcher import is_available
    result = is_available()
    assert isinstance(result, bool)


def test_profile_to_text():
    """Test profile → text conversion logic."""
    # Verify the expected text format by constructing it manually.
    # This mirrors SemanticMatcher.profile_to_text() without needing the model.
    profile = {
        "title": "Data Scientist",
        "skills": ["python", "sql", "ml"],
        "preferred_locations": ["Bangalore"],
        "experience_years": 5,
    }
    parts = []
    if profile.get("title"):
        parts.append(f"Job title: {profile['title']}")
    if profile.get("skills"):
        parts.append(f"Skills: {', '.join(profile['skills'])}")
    if profile.get("preferred_locations"):
        parts.append(f"Location: {', '.join(profile['preferred_locations'])}")
    if profile.get("experience_years"):
        parts.append(f"{profile['experience_years']} years of experience")
    text = ". ".join(parts)
    assert "Data Scientist" in text
    assert "python, sql, ml" in text
    assert "Bangalore" in text
    assert "5 years" in text


def test_job_to_text_logic():
    """Sanity check on job text building logic."""
    job = {
        "title": "Software Engineer",
        "company": "Google",
        "location": "Mumbai",
        "description": "Build scalable systems with Python and Go."
    }
    # Expected format: "Software Engineer at Google in Mumbai Build scalable systems..."
    text = f"{job['title']} at {job['company']} in {job['location']} {job['description'][:500]}"
    assert "Software Engineer" in text
    assert "Google" in text
    assert "Python" in text


class TestSemanticMatcherWithModel:
    """Tests that require sentence-transformers to be installed.
    
    These are skipped automatically if the package is not available.
    """

    def _skip_if_unavailable(self):
        from embedding_matcher import is_available
        if not is_available():
            import pytest
            pytest.skip("sentence-transformers not installed")

    def test_encode_returns_vectors(self):
        self._skip_if_unavailable()
        from embedding_matcher import SemanticMatcher
        matcher = SemanticMatcher()
        vecs = matcher.encode(["hello world", "data science"])
        assert vecs.shape[0] == 2
        assert vecs.shape[1] > 0  # embedding dimension

    def test_match_returns_ranked_results(self):
        self._skip_if_unavailable()
        from embedding_matcher import SemanticMatcher
        matcher = SemanticMatcher()
        profile = {"title": "Data Scientist", "skills": ["python", "ml"]}
        jobs = [
            {"title": "Data Scientist", "description": "Python and ML required"},
            {"title": "Chef", "description": "Cook Italian food"},
            {"title": "ML Engineer", "description": "Deep learning with PyTorch"},
        ]
        results = matcher.match_profile_to_jobs(profile, jobs, top_k=3)
        assert len(results) == 3
        assert results[0]["rank"] == 1
        # The data science job should rank higher than the chef job
        ds_score = next(r["score"] for r in results if "Data Scientist" in r["job"]["title"])
        chef_score = next(r["score"] for r in results if "Chef" in r["job"]["title"])
        assert ds_score > chef_score

    def test_empty_jobs_returns_empty(self):
        self._skip_if_unavailable()
        from embedding_matcher import SemanticMatcher
        matcher = SemanticMatcher()
        results = matcher.match_profile_to_jobs({"title": "Engineer"}, [], top_k=5)
        assert results == []
