"""Tests for the ML-backed SalaryPredictor."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from salary_predictor import SalaryPredictor


class TestHeuristicPrediction:
    """Test heuristic fallback predictions (no trained model)."""

    def setup_method(self):
        self.predictor = SalaryPredictor()
        self.predictor.model = None  # Force heuristic mode

    def test_predict_returns_required_keys(self):
        result = self.predictor.predict({"title": "Data Scientist"})
        assert "min" in result
        assert "max" in result
        assert "avg" in result
        assert "currency" in result
        assert "unit" in result
        assert "confidence" in result
        assert "method" in result

    def test_heuristic_method_label(self):
        result = self.predictor.predict({"title": "Data Scientist"})
        assert result["method"] == "heuristic"

    def test_min_less_than_max(self):
        result = self.predictor.predict({"title": "Software Engineer"})
        assert result["min"] <= result["max"]
        assert result["min"] <= result["avg"] <= result["max"]

    def test_location_affects_salary(self):
        bangalore = self.predictor.predict({
            "title": "Data Scientist",
            "location": "Bangalore, Karnataka"
        })
        kolkata = self.predictor.predict({
            "title": "Data Scientist",
            "location": "Kolkata, West Bengal"
        })
        assert bangalore["avg"] > kolkata["avg"]

    def test_senior_earns_more(self):
        senior = self.predictor.predict({"title": "Senior Software Engineer"})
        junior = self.predictor.predict({"title": "Software Engineer"})
        assert senior["avg"] > junior["avg"]

    def test_enterprise_pays_more_than_small(self):
        enterprise = self.predictor.predict({
            "title": "Data Scientist",
            "company_size": "Enterprise"
        })
        small = self.predictor.predict({
            "title": "Data Scientist",
            "company_size": "Small"
        })
        assert enterprise["avg"] > small["avg"]

    def test_premium_skills_boost_salary(self):
        with_premium = self.predictor.predict({
            "title": "Data Scientist",
            "skills": "python,machine learning,tensorflow,aws,docker,kubernetes"
        })
        without_premium = self.predictor.predict({
            "title": "Data Scientist",
            "skills": "excel,powerpoint"
        })
        assert with_premium["avg"] > without_premium["avg"]

    def test_missing_fields_handled(self):
        """Predict should work even with minimal input."""
        result = self.predictor.predict({})
        assert result["avg"] > 0
        assert result["method"] == "heuristic"

    def test_unknown_title_still_predicts(self):
        result = self.predictor.predict({"title": "Chief Meme Officer"})
        assert result["avg"] > 0


class TestTitleNormalization:
    """Test job title normalization logic."""

    def test_data_scientist(self):
        assert SalaryPredictor._normalize_title("Data Scientist") == "data scientist"

    def test_senior_in_title(self):
        result = SalaryPredictor._normalize_title("Senior Backend Developer")
        # Should match something reasonable
        assert result in ["backend developer", "senior software engineer"]

    def test_ml_engineer(self):
        assert SalaryPredictor._normalize_title("Machine Learning Engineer") == "machine learning engineer"

    def test_full_stack(self):
        assert SalaryPredictor._normalize_title("Full Stack Developer") == "full stack developer"


class TestExperienceDetection:
    """Test experience level detection from title."""

    def test_senior_level(self):
        assert SalaryPredictor._detect_experience_level("Senior Data Scientist") == 3

    def test_junior_level(self):
        assert SalaryPredictor._detect_experience_level("Junior Developer") == 1

    def test_mid_level_default(self):
        assert SalaryPredictor._detect_experience_level("Data Analyst") == 2

    def test_director_level(self):
        assert SalaryPredictor._detect_experience_level("Director of Engineering") == 4


class TestTrainAndPredict:
    """Test training and ML prediction round-trip."""

    def test_train_with_salary_data(self):
        predictor = SalaryPredictor()
        jobs = [
            {"title": "Data Scientist", "location": "Bangalore", "salary_min": 15, "salary_max": 25, "skills": "python,ml"},
            {"title": "Software Engineer", "location": "Mumbai", "salary_min": 10, "salary_max": 18, "skills": "java"},
            {"title": "Data Analyst", "location": "Delhi", "salary_min": 6, "salary_max": 12, "skills": "sql,excel"},
            {"title": "DevOps Engineer", "location": "Pune", "salary_min": 12, "salary_max": 20, "skills": "docker,aws"},
            {"title": "Product Manager", "location": "Bangalore", "salary_min": 18, "salary_max": 30, "skills": "agile"},
        ]
        metrics = predictor.train(jobs)
        assert metrics["mode"] == "ml"
        assert metrics["samples"] >= 5

    def test_predict_after_train_uses_ml(self):
        predictor = SalaryPredictor()
        jobs = [
            {"title": "Data Scientist", "location": "Bangalore", "salary_min": 15, "salary_max": 25, "skills": "python,ml"},
            {"title": "Software Engineer", "location": "Mumbai", "salary_min": 10, "salary_max": 18, "skills": "java"},
            {"title": "Data Analyst", "location": "Delhi", "salary_min": 6, "salary_max": 12, "skills": "sql"},
            {"title": "DevOps Engineer", "location": "Pune", "salary_min": 12, "salary_max": 20, "skills": "docker"},
            {"title": "Product Manager", "location": "Hyderabad", "salary_min": 18, "salary_max": 28, "skills": "agile"},
        ]
        predictor.train(jobs)
        result = predictor.predict({"title": "Data Scientist", "location": "Bangalore"})
        assert result["method"] == "ml_model"
        assert result["avg"] > 0

    def test_train_with_insufficient_data_augments(self):
        predictor = SalaryPredictor()
        # Only 2 salary samples — should augment
        jobs = [
            {"title": "Data Scientist", "location": "Mumbai", "salary_min": 15, "salary_max": 25},
            {"title": "Software Engineer", "location": "Delhi", "salary_min": 10, "salary_max": 18},
            # These have no salary — used for synthetic augmentation
            {"title": "Data Analyst", "location": "Pune", "skills": "sql,excel"},
            {"title": "DevOps Engineer", "location": "Bangalore", "skills": "docker,aws"},
        ]
        metrics = predictor.train(jobs)
        # Should still train (via augmentation)
        assert metrics.get("samples", 0) >= 2 or metrics.get("mode") == "heuristic"


class TestMarketAnalysis:
    """Test market analysis functionality."""

    def test_analyze_market_returns_stats(self):
        predictor = SalaryPredictor()
        predictor.model = None  # Use heuristic
        jobs = [
            {"title": "Data Scientist", "location": "Bangalore"},
            {"title": "Data Scientist", "location": "Mumbai"},
            {"title": "Software Engineer", "location": "Bangalore"},
        ]
        result = predictor.analyze_market(jobs)
        assert "role_averages" in result
        assert "location_averages" in result
        assert "overall_avg" in result
        assert result["total_jobs_analyzed"] == 3

    def test_analyze_market_empty_list(self):
        predictor = SalaryPredictor()
        predictor.model = None
        result = predictor.analyze_market([])
        assert result["total_jobs_analyzed"] == 0
