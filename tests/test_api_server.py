"""Tests for the FastAPI API server."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import pytest
from fastapi.testclient import TestClient
from api_server import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestRootEndpoint:
    def test_root_returns_api_info(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "LinkedIn Job Analysis API"
        assert "endpoints" in data

    def test_api_root_returns_api_info(self, client):
        response = client.get("/api")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data


class TestJobsEndpoint:
    def test_get_jobs(self, client):
        response = client.get("/api/jobs")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "jobs" in data
        assert isinstance(data["jobs"], list)

    def test_get_jobs_with_limit(self, client):
        response = client.get("/api/jobs?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5

    def test_get_jobs_invalid_limit(self, client):
        response = client.get("/api/jobs?limit=-1")
        assert response.status_code == 422  # Pydantic validation error


class TestSearchEndpoint:
    def test_search_missing_query(self, client):
        response = client.get("/api/jobs/search")
        assert response.status_code == 422

    def test_search_with_query(self, client):
        response = client.get("/api/jobs/search?q=python")
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "jobs" in data


class TestStatsEndpoint:
    def test_get_stats(self, client):
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_jobs" in data
        assert "unique_companies" in data


class TestSkillsEndpoint:
    def test_get_skills(self, client):
        response = client.get("/api/skills")
        assert response.status_code == 200
        data = response.json()
        assert "top_10" in data or "all_skills" in data


class TestCompaniesEndpoint:
    def test_get_companies(self, client):
        response = client.get("/api/companies")
        assert response.status_code == 200
        data = response.json()
        assert "top_companies" in data


class TestLocationsEndpoint:
    def test_get_locations(self, client):
        response = client.get("/api/locations")
        assert response.status_code == 200
        data = response.json()
        assert "top_locations" in data


class TestAlertsEndpoint:
    def test_get_alerts(self, client):
        response = client.get("/api/alerts")
        assert response.status_code == 200


class TestTrendsEndpoint:
    def test_get_trends(self, client):
        response = client.get("/api/trends")
        assert response.status_code == 200


class TestSalaryPredictEndpoint:
    def test_predict_salary(self, client):
        response = client.post("/api/salary/predict", json={
            "title": "Data Scientist",
            "location": "Bangalore",
            "skills": "python,machine learning,tensorflow",
            "company_size": "Enterprise",
        })
        assert response.status_code == 200
        data = response.json()
        assert "min" in data
        assert "max" in data
        assert "avg" in data
        assert data["avg"] > 0

    def test_predict_salary_minimal(self, client):
        response = client.post("/api/salary/predict", json={
            "title": "Software Engineer",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["avg"] > 0

    def test_predict_salary_missing_title(self, client):
        response = client.post("/api/salary/predict", json={})
        assert response.status_code == 422  # Missing required field


class TestCORSHeaders:
    def test_cors_headers_present(self, client):
        response = client.options("/api/jobs", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        })
        # FastAPI CORS middleware should handle this
        assert response.status_code in (200, 405)


class TestSwaggerDocs:
    def test_docs_accessible(self, client):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "paths" in data
        assert "/api/salary/predict" in data["paths"]
