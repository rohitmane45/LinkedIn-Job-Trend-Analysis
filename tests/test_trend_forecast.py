"""Tests for the trend forecasting functionality."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from trend_tracker import TrendTracker


class TestForecastSkills:
    """Test linear regression skill forecasting."""

    def _make_tracker_with_history(self, snapshots):
        """Create a TrendTracker with injected snapshot history."""
        tracker = TrendTracker()
        tracker.history = {'snapshots': snapshots, 'created_at': '2026-01-01T00:00:00'}
        return tracker

    def test_forecast_with_growth(self):
        snapshots = [
            {'date': '2026-01-01', 'top_skills': {'python': 10, 'sql': 5}},
            {'date': '2026-01-15', 'top_skills': {'python': 15, 'sql': 6}},
            {'date': '2026-02-01', 'top_skills': {'python': 20, 'sql': 7}},
        ]
        tracker = self._make_tracker_with_history(snapshots)
        forecasts = tracker.forecast_skills(horizon_days=30)
        assert len(forecasts) > 0
        # Python should show positive growth
        python_forecast = next((f for f in forecasts if f['skill'] == 'python'), None)
        assert python_forecast is not None
        assert python_forecast['growth_rate'] > 0
        assert python_forecast['predicted_count'] > python_forecast['current_count']

    def test_forecast_returns_required_keys(self):
        snapshots = [
            {'date': '2026-01-01', 'top_skills': {'react': 50}},
            {'date': '2026-02-01', 'top_skills': {'react': 60}},
        ]
        tracker = self._make_tracker_with_history(snapshots)
        forecasts = tracker.forecast_skills()
        if forecasts:
            f = forecasts[0]
            assert 'skill' in f
            assert 'current_count' in f
            assert 'predicted_count' in f
            assert 'growth_rate' in f
            assert 'confidence' in f

    def test_forecast_empty_history(self):
        tracker = self._make_tracker_with_history([])
        forecasts = tracker.forecast_skills()
        assert forecasts == []

    def test_forecast_single_snapshot(self):
        snapshots = [
            {'date': '2026-01-01', 'top_skills': {'python': 10}},
        ]
        tracker = self._make_tracker_with_history(snapshots)
        forecasts = tracker.forecast_skills()
        # Need at least 2 data points
        assert forecasts == []

    def test_confidence_between_0_and_1(self):
        snapshots = [
            {'date': '2026-01-01', 'top_skills': {'python': 10}},
            {'date': '2026-01-15', 'top_skills': {'python': 20}},
            {'date': '2026-02-01', 'top_skills': {'python': 30}},
        ]
        tracker = self._make_tracker_with_history(snapshots)
        forecasts = tracker.forecast_skills()
        for f in forecasts:
            assert 0 <= f['confidence'] <= 1

    def test_predicted_count_non_negative(self):
        # Sharply declining data
        snapshots = [
            {'date': '2026-01-01', 'top_skills': {'cobol': 100}},
            {'date': '2026-02-01', 'top_skills': {'cobol': 50}},
            {'date': '2026-03-01', 'top_skills': {'cobol': 10}},
        ]
        tracker = self._make_tracker_with_history(snapshots)
        forecasts = tracker.forecast_skills(horizon_days=365)
        for f in forecasts:
            assert f['predicted_count'] >= 0


class TestGrowthRankings:

    def test_growth_rankings_structure(self):
        snapshots = [
            {'date': '2026-01-01', 'top_skills': {'python': 10, 'cobol': 50, 'sql': 20}},
            {'date': '2026-02-01', 'top_skills': {'python': 30, 'cobol': 30, 'sql': 20}},
        ]
        tracker = TrendTracker()
        tracker.history = {'snapshots': snapshots, 'created_at': '2026-01-01'}
        rankings = tracker.get_growth_rankings()
        assert 'rising' in rankings
        assert 'stable' in rankings
        assert 'declining' in rankings
        assert isinstance(rankings['rising'], list)

    def test_empty_rankings(self):
        tracker = TrendTracker()
        tracker.history = {'snapshots': [], 'created_at': '2026-01-01'}
        rankings = tracker.get_growth_rankings()
        assert rankings == {'rising': [], 'stable': [], 'declining': []}
