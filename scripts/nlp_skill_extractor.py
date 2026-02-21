"""
NLP-based Skill Extraction and Co-occurrence Analysis.

Uses TF-IDF to analyze skill co-occurrence patterns across jobs,
discover emerging skills, and cluster related skills.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"

# Load known skills from config
_KNOWN_SKILLS = set()
_skills_config = CONFIG_DIR / "skills_config.json"
if _skills_config.exists():
    try:
        with open(_skills_config, "r", encoding="utf-8") as f:
            config = json.load(f)
        for category in config.values():
            if isinstance(category, list):
                _KNOWN_SKILLS.update(s.lower() for s in category)
            elif isinstance(category, dict):
                for sublist in category.values():
                    if isinstance(sublist, list):
                        _KNOWN_SKILLS.update(s.lower() for s in sublist)
    except Exception:
        pass


class SkillCooccurrenceAnalyzer:
    """
    Analyzes skill co-occurrence patterns using TF-IDF.

    Works with the `skills` column (comma-separated strings) from job data.

    Usage:
        analyzer = SkillCooccurrenceAnalyzer()
        results = analyzer.analyze(df)
        emerging = analyzer.discover_emerging_skills()
        clusters = analyzer.find_skill_clusters()
    """

    def __init__(self, known_skills: set = None):
        self.known_skills = known_skills or _KNOWN_SKILLS
        self.tfidf_matrix = None
        self.feature_names = []
        self.skill_docs = []
        self.skill_freq = Counter()

    def analyze(self, df) -> dict:
        """
        Analyze skill co-occurrence from a DataFrame.

        Args:
            df: pandas DataFrame with a 'skills' column (comma-separated strings).

        Returns:
            dict with 'emerging', 'clusters', 'cooccurrence', 'tfidf_scores'.
        """
        if 'skills' not in df.columns:
            return {"error": "No 'skills' column found"}

        # Parse skills: each row's skills become a "document"
        self.skill_docs = []
        self.skill_freq = Counter()
        for raw_skills in df['skills'].dropna():
            if isinstance(raw_skills, str):
                skills = [s.strip().lower() for s in raw_skills.split(',') if s.strip()]
            elif isinstance(raw_skills, list):
                skills = [s.strip().lower() for s in raw_skills if s.strip()]
            else:
                continue

            if skills:
                self.skill_docs.append(' '.join(skills))
                self.skill_freq.update(skills)

        if not self.skill_docs:
            return {"error": "No skill data found"}

        results = {
            "total_skill_mentions": sum(self.skill_freq.values()),
            "unique_skills": len(self.skill_freq),
            "top_skills": dict(self.skill_freq.most_common(20)),
        }

        # TF-IDF analysis
        if HAS_SKLEARN and len(self.skill_docs) >= 2:
            try:
                self.tfidf_matrix, self.feature_names = self._compute_tfidf()
                results["tfidf_scores"] = self._get_tfidf_scores()
                results["emerging"] = self.discover_emerging_skills()
                results["clusters"] = self.find_skill_clusters()
                results["cooccurrence"] = self._get_cooccurrence_pairs()
            except Exception as e:
                results["tfidf_error"] = str(e)
        else:
            results["emerging"] = self._simple_emerging_skills()
            results["clusters"] = {}
            results["cooccurrence"] = []

        return results

    def _compute_tfidf(self):
        """Compute TF-IDF matrix from skill documents."""
        vectorizer = TfidfVectorizer(
            token_pattern=r'[a-zA-Z0-9#+\.\-]+',
            max_features=200,
            min_df=2,
            max_df=0.95,
        )
        matrix = vectorizer.fit_transform(self.skill_docs)
        features = vectorizer.get_feature_names_out().tolist()
        return matrix, features

    def _get_tfidf_scores(self) -> dict:
        """Get average TF-IDF score for each skill."""
        if self.tfidf_matrix is None:
            return {}

        mean_scores = np.asarray(self.tfidf_matrix.mean(axis=0)).flatten()
        scores = {}
        for i, name in enumerate(self.feature_names):
            scores[name] = round(float(mean_scores[i]), 4)

        return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True)[:30])

    def discover_emerging_skills(self, known_skills: set = None) -> list:
        """
        Discover skills NOT in the known set but appearing in the data.

        Returns list of dicts: [{'skill': ..., 'frequency': ..., 'tfidf_score': ...}]
        """
        known = known_skills or self.known_skills
        emerging = []

        tfidf_scores = self._get_tfidf_scores() if self.tfidf_matrix is not None else {}

        for skill, count in self.skill_freq.most_common(100):
            if skill not in known and len(skill) > 1:
                emerging.append({
                    "skill": skill,
                    "frequency": count,
                    "tfidf_score": tfidf_scores.get(skill, 0),
                })

        # Sort by frequency descending
        emerging.sort(key=lambda x: x["frequency"], reverse=True)
        return emerging[:20]

    def _simple_emerging_skills(self) -> list:
        """Fallback emerging skill discovery without TF-IDF."""
        emerging = []
        for skill, count in self.skill_freq.most_common(100):
            if skill not in self.known_skills and len(skill) > 1:
                emerging.append({
                    "skill": skill,
                    "frequency": count,
                    "tfidf_score": 0,
                })
        return emerging[:20]

    def find_skill_clusters(self, threshold: float = 0.3) -> dict:
        """
        Group related skills by cosine similarity on TF-IDF vectors.

        Returns dict mapping cluster representative → list of related skills.
        """
        if self.tfidf_matrix is None or len(self.feature_names) < 3:
            return {}

        # Compute skill-skill similarity (transpose: features as rows)
        skill_vectors = self.tfidf_matrix.T
        sim_matrix = cosine_similarity(skill_vectors)

        # Simple agglomerative approach: group skills by similarity
        assigned = set()
        clusters = {}

        for i in range(len(self.feature_names)):
            if self.feature_names[i] in assigned:
                continue

            cluster_leader = self.feature_names[i]
            cluster_members = [cluster_leader]
            assigned.add(cluster_leader)

            for j in range(i + 1, len(self.feature_names)):
                if self.feature_names[j] in assigned:
                    continue
                if sim_matrix[i, j] >= threshold:
                    cluster_members.append(self.feature_names[j])
                    assigned.add(self.feature_names[j])

            if len(cluster_members) > 1:
                clusters[cluster_leader] = cluster_members

        return clusters

    def _get_cooccurrence_pairs(self, top_n: int = 15) -> list:
        """
        Get top co-occurring skill pairs.

        Returns list of dicts: [{'skills': [a, b], 'count': n}]
        """
        pair_counts = Counter()
        for doc in self.skill_docs:
            skills = doc.split()
            for i in range(len(skills)):
                for j in range(i + 1, len(skills)):
                    pair = tuple(sorted([skills[i], skills[j]]))
                    pair_counts[pair] += 1

        result = []
        for (s1, s2), count in pair_counts.most_common(top_n):
            result.append({"skills": [s1, s2], "count": count})

        return result
