"""
Semantic Job Matching with Embeddings
=======================================
Uses sentence-transformers to compute cosine similarity between
a user's profile and job descriptions for semantic (meaning-based) matching.

Gracefully falls back if sentence-transformers is not installed.

Usage:
    from embedding_matcher import SemanticMatcher
    matcher = SemanticMatcher()
    results = matcher.match_profile_to_jobs(profile_dict, jobs_list)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typing import Dict, List, Optional

# ──────────────────────────────────────────────────────────────
# Model configuration
# ──────────────────────────────────────────────────────────────
DEFAULT_MODEL = "all-MiniLM-L6-v2"


def _check_dependencies():
    """Check if sentence-transformers is installed."""
    try:
        from sentence_transformers import SentenceTransformer  # noqa: F401
        return True
    except ImportError:
        return False


SENTENCE_TRANSFORMERS_AVAILABLE = _check_dependencies()


# ──────────────────────────────────────────────────────────────
# SemanticMatcher
# ──────────────────────────────────────────────────────────────

class SemanticMatcher:
    """
    Semantic job matcher using sentence-transformers embeddings.

    Encodes profile text and job descriptions as dense vectors,
    then ranks jobs by cosine similarity.

    Usage:
        matcher = SemanticMatcher()
        results = matcher.match_profile_to_jobs(profile, jobs)
    """

    def __init__(self, model_name: str = DEFAULT_MODEL):
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers is required for semantic matching.\n"
                "Install with: pip install sentence-transformers\n"
                "Note: this will also install PyTorch (~2GB)."
            )
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: List[str]):
        """Encode a list of texts into embedding vectors."""
        return self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)

    def cosine_similarity(self, vec_a, vec_b_matrix):
        """Compute cosine similarity between a vector and a matrix of vectors."""
        import numpy as np
        # Normalize
        a_norm = vec_a / (np.linalg.norm(vec_a) + 1e-10)
        b_norms = vec_b_matrix / (np.linalg.norm(vec_b_matrix, axis=1, keepdims=True) + 1e-10)
        return np.dot(b_norms, a_norm)

    def profile_to_text(self, profile: Dict) -> str:
        """Convert a profile dict to a descriptive text for embedding."""
        parts = []
        if profile.get("title"):
            parts.append(f"Job title: {profile['title']}")
        if profile.get("skills"):
            skills = profile["skills"]
            if isinstance(skills, list):
                skills = ", ".join(skills)
            parts.append(f"Skills: {skills}")
        if profile.get("preferred_locations"):
            locs = profile["preferred_locations"]
            if isinstance(locs, list):
                locs = ", ".join(locs)
            parts.append(f"Location: {locs}")
        if profile.get("experience_years"):
            parts.append(f"{profile['experience_years']} years of experience")
        return ". ".join(parts) if parts else "software engineer"

    def job_to_text(self, job: Dict) -> str:
        """Convert a job dict to a descriptive text for embedding."""
        parts = []
        if job.get("title"):
            parts.append(job["title"])
        if job.get("company"):
            parts.append(f"at {job['company']}")
        if job.get("location") or job.get("city"):
            parts.append(f"in {job.get('location') or job.get('city')}")
        if job.get("description"):
            # Truncate to first 500 chars to keep embedding manageable
            desc = str(job["description"])[:500]
            parts.append(desc)
        elif job.get("skills"):
            skills = job["skills"]
            if isinstance(skills, list):
                skills = ", ".join(skills)
            parts.append(f"Skills: {skills}")
        return " ".join(parts)

    def match_profile_to_jobs(
        self,
        profile: Dict,
        jobs: List[Dict],
        top_k: int = 15,
    ) -> List[Dict]:
        """
        Match a profile against a list of jobs using semantic similarity.

        Args:
            profile: User profile dict (title, skills, etc.)
            jobs: List of job dicts
            top_k: Number of top matches to return

        Returns:
            List of dicts: [{'job': {...}, 'score': 0-100, 'rank': 1}, ...]
        """
        import numpy as np

        if not jobs:
            return []

        profile_text = self.profile_to_text(profile)
        job_texts = [self.job_to_text(job) for job in jobs]

        # Encode
        all_texts = [profile_text] + job_texts
        embeddings = self.encode(all_texts)

        profile_vec = embeddings[0]
        job_vecs = embeddings[1:]

        # Compute similarities
        similarities = self.cosine_similarity(profile_vec, job_vecs)

        # Rank
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for rank, idx in enumerate(top_indices, 1):
            score = float(similarities[idx]) * 100  # Convert to 0-100 scale
            score = max(0, min(100, score))  # Clamp
            results.append({
                "job": jobs[idx],
                "score": round(score, 1),
                "rank": rank,
            })

        return results


# ──────────────────────────────────────────────────────────────
# Convenience functions
# ──────────────────────────────────────────────────────────────

def is_available() -> bool:
    """Check if semantic matching is available."""
    return SENTENCE_TRANSFORMERS_AVAILABLE


def quick_match(profile: Dict, jobs: List[Dict], top_k: int = 10) -> List[Dict]:
    """Quick one-liner for semantic matching."""
    matcher = SemanticMatcher()
    return matcher.match_profile_to_jobs(profile, jobs, top_k=top_k)
