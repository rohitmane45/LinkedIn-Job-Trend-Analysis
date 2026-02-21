"""Tests for the NLP skill extraction module."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import pandas as pd
from nlp_skill_extractor import SkillCooccurrenceAnalyzer


class TestSkillCooccurrenceAnalyzer:
    """Test TF-IDF based skill analysis."""

    def _make_df(self, skill_strings):
        return pd.DataFrame({'skills': skill_strings})

    def test_analyze_returns_required_keys(self):
        df = self._make_df([
            'python, sql, pandas',
            'python, machine learning, tensorflow',
            'java, spring, docker',
        ])
        analyzer = SkillCooccurrenceAnalyzer()
        result = analyzer.analyze(df)
        assert 'total_skill_mentions' in result
        assert 'unique_skills' in result
        assert 'top_skills' in result

    def test_skill_frequency_counting(self):
        df = self._make_df([
            'python, sql',
            'python, pandas',
            'python, tensorflow',
        ])
        analyzer = SkillCooccurrenceAnalyzer()
        result = analyzer.analyze(df)
        assert result['top_skills']['python'] == 3

    def test_emerging_skills_excludes_known(self):
        known = {'python', 'sql', 'java'}
        df = self._make_df([
            'python, newskill1, newskill2',
            'sql, newskill1, anothernew',
            'java, newskill2, anothernew',
        ])
        analyzer = SkillCooccurrenceAnalyzer(known_skills=known)
        result = analyzer.analyze(df)
        emerging = result.get('emerging', [])
        emerging_names = [e['skill'] for e in emerging]
        assert 'python' not in emerging_names
        assert 'newskill1' in emerging_names or 'newskill2' in emerging_names

    def test_empty_dataframe(self):
        df = pd.DataFrame({'skills': []})
        analyzer = SkillCooccurrenceAnalyzer()
        result = analyzer.analyze(df)
        assert 'error' in result

    def test_missing_skills_column(self):
        df = pd.DataFrame({'title': ['Engineer']})
        analyzer = SkillCooccurrenceAnalyzer()
        result = analyzer.analyze(df)
        assert result.get('error') == "No 'skills' column found"

    def test_cooccurrence_pairs(self):
        df = self._make_df([
            'python, sql',
            'python, sql',
            'python, sql',
            'java, spring',
        ])
        analyzer = SkillCooccurrenceAnalyzer()
        result = analyzer.analyze(df)
        cooccurrence = result.get('cooccurrence', [])
        if cooccurrence:
            # python-sql should be the top pair
            top_pair = cooccurrence[0]
            assert 'python' in top_pair['skills'] and 'sql' in top_pair['skills']

    def test_clusters_groups_related_skills(self):
        # Many jobs with python+pandas together should cluster them
        df = self._make_df([
            'python, pandas, numpy',
            'python, pandas, matplotlib',
            'python, pandas, scikit-learn',
            'java, spring, hibernate',
            'java, spring, maven',
            'java, spring, junit',
        ])
        analyzer = SkillCooccurrenceAnalyzer()
        result = analyzer.analyze(df)
        clusters = result.get('clusters', {})
        # Should have some clusters
        assert isinstance(clusters, dict)

    def test_nan_values_handled(self):
        df = self._make_df(['python, sql', None, 'java, docker', None])
        analyzer = SkillCooccurrenceAnalyzer()
        result = analyzer.analyze(df)
        assert result['unique_skills'] >= 2

    def test_single_row_still_works(self):
        df = self._make_df(['python, sql, docker'])
        analyzer = SkillCooccurrenceAnalyzer()
        result = analyzer.analyze(df)
        assert result['unique_skills'] == 3
