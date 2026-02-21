"""
ML-backed Salary Predictor for LinkedIn Job Analysis.

Uses GradientBoostingRegressor trained on job data. Falls back to
heuristic predictions when no trained model is available.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from collections import Counter

import numpy as np

try:
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.preprocessing import LabelEncoder
    import joblib
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# ──────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
MODELS_DIR = BASE_DIR / "models"
MODEL_PATH = MODELS_DIR / "salary_model.pkl"
METADATA_PATH = CONFIG_DIR / "salary_model.json"

MODELS_DIR.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────────────────────
# Heuristic tables (fallback when no ML model exists)
# ──────────────────────────────────────────────────────────────
BASE_SALARIES = {
    "data scientist":       {"min": 12, "max": 25},
    "senior data scientist": {"min": 20, "max": 35},
    "machine learning engineer": {"min": 15, "max": 30},
    "data engineer":        {"min": 10, "max": 22},
    "data analyst":         {"min": 6,  "max": 15},
    "software engineer":    {"min": 8,  "max": 20},
    "senior software engineer": {"min": 16, "max": 30},
    "backend developer":    {"min": 8,  "max": 18},
    "full stack developer": {"min": 8,  "max": 20},
    "devops engineer":      {"min": 10, "max": 22},
    "product manager":      {"min": 12, "max": 28},
    "business analyst":     {"min": 6,  "max": 16},
}

LOCATION_MULTIPLIERS = {
    "bangalore": 1.15, "bengaluru": 1.15,
    "mumbai": 1.10,
    "hyderabad": 1.05,
    "delhi": 1.05, "delhi ncr": 1.05, "gurgaon": 1.10, "noida": 1.00,
    "pune": 1.00,
    "chennai": 0.95,
    "kolkata": 0.90,
}

COMPANY_SIZE_MULTIPLIERS = {
    "Enterprise": 1.15,
    "Large": 1.05,
    "Medium": 0.95,
    "Small": 0.85,
    "Startup": 0.80,
}

PREMIUM_SKILLS = {
    "machine learning", "deep learning", "ai", "kubernetes", "aws",
    "azure", "gcp", "spark", "tensorflow", "pytorch", "docker",
    "kafka", "airflow", "snowflake", "databricks", "mlops",
}


class SalaryPredictor:
    """
    ML-backed salary predictor with heuristic fallback.

    Usage:
        predictor = SalaryPredictor()
        predictor.train(jobs_with_salary)          # train on data
        result = predictor.predict(job_info)        # predict
        market = predictor.analyze_market(jobs)     # market analysis
    """

    def __init__(self):
        self.model = None
        self.label_encoders = {}
        self._title_classes = []
        self._location_classes = []
        self._company_size_classes = []
        self._load_model()

    # ──────────────────────────────────────────────────────────
    # Model persistence
    # ──────────────────────────────────────────────────────────
    def _load_model(self):
        """Load a previously trained model from disk."""
        if not HAS_SKLEARN:
            return
        if MODEL_PATH.exists():
            try:
                bundle = joblib.load(MODEL_PATH)
                self.model = bundle.get("model")
                self._title_classes = bundle.get("title_classes", [])
                self._location_classes = bundle.get("location_classes", [])
                self._company_size_classes = bundle.get("company_size_classes", [])
                print("✅ Loaded trained salary model")
            except Exception as e:
                print(f"⚠️ Could not load salary model: {e}")
                self.model = None

    def _save_model(self, n_samples: int = 0):
        """Persist the trained model and metadata."""
        bundle = {
            "model": self.model,
            "title_classes": self._title_classes,
            "location_classes": self._location_classes,
            "company_size_classes": self._company_size_classes,
        }
        joblib.dump(bundle, MODEL_PATH)

        metadata = {
            "trained_at": datetime.now().isoformat(),
            "model_type": "GradientBoostingRegressor",
            "n_training_samples": n_samples,
            "features": [
                "title_encoded", "location_encoded", "company_size_encoded",
                "skill_count", "premium_skill_count", "experience_level"
            ],
        }
        with open(METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        print(f"💾 Salary model saved ({n_samples} samples)")

    # ──────────────────────────────────────────────────────────
    # Feature engineering
    # ──────────────────────────────────────────────────────────
    @staticmethod
    def _normalize_title(title: str) -> str:
        """Map a job title to a canonical role name."""
        title_lower = title.lower().strip()
        for canonical in BASE_SALARIES:
            if canonical in title_lower:
                return canonical
        # Broad fallback mapping
        if "data" in title_lower and "scien" in title_lower:
            return "data scientist"
        if "data" in title_lower and "analy" in title_lower:
            return "data analyst"
        if "data" in title_lower and "eng" in title_lower:
            return "data engineer"
        if "ml" in title_lower or "machine" in title_lower:
            return "machine learning engineer"
        if "backend" in title_lower:
            return "backend developer"
        if "full" in title_lower and "stack" in title_lower:
            return "full stack developer"
        if "devops" in title_lower:
            return "devops engineer"
        if "product" in title_lower and "manag" in title_lower:
            return "product manager"
        if "business" in title_lower and "analy" in title_lower:
            return "business analyst"
        if "senior" in title_lower or "sr" in title_lower:
            return "senior software engineer"
        if "software" in title_lower or "swe" in title_lower:
            return "software engineer"
        return "software engineer"  # neutral default

    @staticmethod
    def _normalize_location(location: str) -> str:
        """Extract city from a location string."""
        city = location.lower().split(",")[0].strip()
        return city

    @staticmethod
    def _parse_skills(skills) -> list:
        """Parse skills field into a list."""
        if isinstance(skills, list):
            return [s.strip().lower() for s in skills]
        if isinstance(skills, str):
            return [s.strip().lower() for s in skills.split(",") if s.strip()]
        return []

    @staticmethod
    def _detect_experience_level(title: str) -> int:
        """Return numeric experience level from title keywords."""
        t = title.lower()
        if any(k in t for k in ["head", "director", "vp", "chief", "principal"]):
            return 4
        if any(k in t for k in ["senior", "sr.", "sr ", "lead", "staff"]):
            return 3
        if any(k in t for k in ["junior", "jr.", "jr ", "intern", "trainee", "fresher"]):
            return 1
        return 2  # mid-level default

    def _encode_categorical(self, values: list, known_classes: list) -> list:
        """Encode categorical values, assigning -1 to unseen categories."""
        class_to_idx = {c: i for i, c in enumerate(known_classes)}
        return [class_to_idx.get(v, -1) for v in values]

    def _build_features(self, jobs: list) -> np.ndarray:
        """Convert list of job dicts to feature matrix."""
        titles = [self._normalize_title(j.get("title", "")) for j in jobs]
        locations = [self._normalize_location(j.get("location", j.get("city", ""))) for j in jobs]
        company_sizes = [j.get("company_size", "Medium") for j in jobs]

        title_enc = self._encode_categorical(titles, self._title_classes)
        loc_enc = self._encode_categorical(locations, self._location_classes)
        size_enc = self._encode_categorical(company_sizes, self._company_size_classes)

        features = []
        for i, job in enumerate(jobs):
            skills = self._parse_skills(job.get("skills", ""))
            skill_count = len(skills)
            premium_count = len([s for s in skills if s in PREMIUM_SKILLS])
            exp_level = self._detect_experience_level(job.get("title", ""))

            features.append([
                title_enc[i],
                loc_enc[i],
                size_enc[i],
                skill_count,
                premium_count,
                exp_level,
            ])

        return np.array(features, dtype=float)

    # ──────────────────────────────────────────────────────────
    # Training
    # ──────────────────────────────────────────────────────────
    def train(self, jobs_data: list) -> dict:
        """
        Train the ML salary model.

        Args:
            jobs_data: list of dicts, each with at least 'title' and 'salary_avg'
                       (or 'salary_min'/'salary_max'). Other useful fields:
                       'location', 'city', 'skills', 'company_size'.

        Returns:
            dict with training metrics.
        """
        if not HAS_SKLEARN:
            print("⚠️ scikit-learn not installed — cannot train ML model")
            return {"error": "scikit-learn not installed"}

        # Filter to jobs with salary info
        valid_jobs = []
        targets = []
        for job in jobs_data:
            salary = self._extract_salary_target(job)
            if salary is not None and salary > 0:
                valid_jobs.append(job)
                targets.append(salary)

        if len(valid_jobs) < 5:
            # Augment with heuristic-generated data
            print(f"⚠️ Only {len(valid_jobs)} salary samples — augmenting with heuristic data")
            synth_jobs, synth_targets = self._generate_synthetic_training_data(jobs_data)
            valid_jobs.extend(synth_jobs)
            targets.extend(synth_targets)

        if len(valid_jobs) < 3:
            print("⚠️ Not enough data to train — using heuristic mode")
            return {"mode": "heuristic", "samples": 0}

        # Build class lists from training data
        self._title_classes = sorted(set(
            self._normalize_title(j.get("title", "")) for j in valid_jobs
        ))
        self._location_classes = sorted(set(
            self._normalize_location(j.get("location", j.get("city", ""))) for j in valid_jobs
        ))
        self._company_size_classes = sorted(set(
            j.get("company_size", "Medium") for j in valid_jobs
        ))

        X = self._build_features(valid_jobs)
        y = np.array(targets, dtype=float)

        self.model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42,
        )
        self.model.fit(X, y)

        # Score on training data (for reporting)
        y_pred = self.model.predict(X)
        mae = float(np.mean(np.abs(y - y_pred)))
        r2 = float(self.model.score(X, y))

        self._save_model(n_samples=len(valid_jobs))

        metrics = {
            "mode": "ml",
            "samples": len(valid_jobs),
            "mae_lpa": round(mae, 2),
            "r2_score": round(r2, 4),
        }
        print(f"✅ Salary model trained: {metrics}")
        return metrics

    def train_from_data(self, jobs_data: list) -> dict:
        """Alias for train() — backward compatibility."""
        return self.train(jobs_data)

    @staticmethod
    def _extract_salary_target(job: dict):
        """Extract average salary from a job dict."""
        if "salary_avg" in job and job["salary_avg"]:
            return float(job["salary_avg"])
        s_min = job.get("salary_min")
        s_max = job.get("salary_max")
        if s_min and s_max:
            return (float(s_min) + float(s_max)) / 2
        if s_min:
            return float(s_min)
        if s_max:
            return float(s_max)
        return None

    def _generate_synthetic_training_data(self, real_jobs: list):
        """
        Generate synthetic salary-labeled data from real jobs using heuristics.
        Adds noise so the model can learn patterns rather than memorize.
        """
        synth_jobs = []
        synth_targets = []
        rng = np.random.RandomState(42)

        for job in real_jobs:
            title = job.get("title", "")
            canonical = self._normalize_title(title)
            if canonical not in BASE_SALARIES:
                continue

            base = BASE_SALARIES[canonical]
            base_avg = (base["min"] + base["max"]) / 2

            # Location multiplier
            loc = self._normalize_location(job.get("location", job.get("city", "")))
            loc_mult = LOCATION_MULTIPLIERS.get(loc, 1.0)

            # Company size multiplier
            size = job.get("company_size", "Medium")
            size_mult = COMPANY_SIZE_MULTIPLIERS.get(size, 1.0)

            # Skill premium
            skills = self._parse_skills(job.get("skills", ""))
            premium_count = len([s for s in skills if s in PREMIUM_SKILLS])
            skill_bonus = 1 + (premium_count * 0.03)

            # Experience factor
            exp = self._detect_experience_level(title)
            exp_mult = {1: 0.75, 2: 1.0, 3: 1.3, 4: 1.6}.get(exp, 1.0)

            salary = base_avg * loc_mult * size_mult * skill_bonus * exp_mult
            # Add ±10% noise
            noise = rng.uniform(0.90, 1.10)
            salary *= noise

            synth_jobs.append(job)
            synth_targets.append(round(salary, 2))

        return synth_jobs, synth_targets

    # ──────────────────────────────────────────────────────────
    # Prediction
    # ──────────────────────────────────────────────────────────
    def predict(self, job_info: dict) -> dict:
        """
        Predict salary for a job.

        Args:
            job_info: dict with 'title', optionally 'location'/'city',
                      'skills', 'company_size'.

        Returns:
            dict with 'min', 'max', 'avg', 'currency', 'unit', 'confidence', 'method'.
        """
        if self.model is not None and HAS_SKLEARN:
            return self._ml_predict(job_info)
        return self._heuristic_predict(job_info)

    def _ml_predict(self, job_info: dict) -> dict:
        """Predict using the trained ML model."""
        X = self._build_features([job_info])
        avg = float(self.model.predict(X)[0])
        avg = max(avg, 1.0)  # floor at 1 LPA

        spread = max(avg * 0.15, 2.0)
        return {
            "min": round(avg - spread, 2),
            "max": round(avg + spread, 2),
            "avg": round(avg, 2),
            "currency": "INR",
            "unit": "LPA",
            "confidence": "high" if avg > 3 else "medium",
            "method": "ml_model",
        }

    def _heuristic_predict(self, job_info: dict) -> dict:
        """Predict using rule-based heuristics (fallback)."""
        title = job_info.get("title", "")
        canonical = self._normalize_title(title)
        base = BASE_SALARIES.get(canonical, {"min": 6, "max": 15})
        base_avg = (base["min"] + base["max"]) / 2

        location = job_info.get("location", job_info.get("city", ""))
        loc = self._normalize_location(location)
        loc_mult = LOCATION_MULTIPLIERS.get(loc, 1.0)

        size = job_info.get("company_size", "Medium")
        size_mult = COMPANY_SIZE_MULTIPLIERS.get(size, 1.0)

        skills = self._parse_skills(job_info.get("skills", ""))
        premium_count = len([s for s in skills if s in PREMIUM_SKILLS])
        skill_bonus = 1 + (premium_count * 0.03)

        exp = self._detect_experience_level(title)
        exp_mult = {1: 0.75, 2: 1.0, 3: 1.3, 4: 1.6}.get(exp, 1.0)

        avg = base_avg * loc_mult * size_mult * skill_bonus * exp_mult
        s_min = base["min"] * loc_mult * size_mult * exp_mult
        s_max = base["max"] * loc_mult * size_mult * skill_bonus * exp_mult

        return {
            "min": round(s_min, 2),
            "max": round(s_max, 2),
            "avg": round(avg, 2),
            "currency": "INR",
            "unit": "LPA",
            "confidence": "medium",
            "method": "heuristic",
        }

    # ──────────────────────────────────────────────────────────
    # Market analysis
    # ──────────────────────────────────────────────────────────
    def analyze_market(self, jobs_data: list) -> dict:
        """
        Analyze salary landscape across a set of jobs.

        Returns per-title, per-location, and per-company-size salary stats.
        """
        predictions = []
        for job in jobs_data:
            pred = self.predict(job)
            pred["title"] = job.get("title", "Unknown")
            pred["location"] = job.get("location", job.get("city", "Unknown"))
            pred["company_size"] = job.get("company_size", "Unknown")
            predictions.append(pred)

        # Group by title
        by_title = {}
        for p in predictions:
            canonical = self._normalize_title(p["title"])
            by_title.setdefault(canonical, []).append(p["avg"])

        title_stats = {}
        for title, salaries in by_title.items():
            title_stats[title] = {
                "avg": round(float(np.mean(salaries)), 2),
                "min": round(float(np.min(salaries)), 2),
                "max": round(float(np.max(salaries)), 2),
                "count": len(salaries),
            }

        # Group by location
        by_location = {}
        for p in predictions:
            loc = self._normalize_location(p["location"])
            by_location.setdefault(loc, []).append(p["avg"])

        location_stats = {}
        for loc, salaries in by_location.items():
            location_stats[loc] = {
                "avg": round(float(np.mean(salaries)), 2),
                "count": len(salaries),
            }

        return {
            "total_jobs_analyzed": len(predictions),
            "role_averages": title_stats,
            "location_averages": location_stats,
            "overall_avg": round(float(np.mean([p["avg"] for p in predictions])), 2) if predictions else 0,
            "method": "ml_model" if self.model else "heuristic",
        }


# ──────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────
def main():
    """Train the salary model from salary_model.json samples + CSV data."""
    predictor = SalaryPredictor()

    # Load existing salary samples from config
    training_data = []
    if METADATA_PATH.exists():
        try:
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
            for sample in config.get("salary_samples", []):
                training_data.append({
                    "title": sample.get("title", ""),
                    "location": sample.get("location", ""),
                    "salary_min": sample.get("salary_min"),
                    "salary_max": sample.get("salary_max"),
                })
        except Exception as e:
            print(f"⚠️ Could not load salary samples: {e}")

    # Load jobs from CSV for synthetic augmentation
    try:
        import pandas as pd
        data_dir = BASE_DIR / "data" / "raw"
        csv_files = list(data_dir.glob("*.csv"))
        all_jobs = []
        for csv_file in csv_files:
            df = pd.read_csv(csv_file)
            for _, row in df.iterrows():
                all_jobs.append(row.to_dict())
        if all_jobs:
            training_data.extend(all_jobs)
            print(f"📊 Loaded {len(all_jobs)} jobs from {len(csv_files)} CSV files")
    except Exception as e:
        print(f"⚠️ Could not load CSV data: {e}")

    # Train
    if training_data:
        metrics = predictor.train(training_data)
        print(f"\n📈 Training results: {json.dumps(metrics, indent=2)}")
    else:
        print("⚠️ No training data found")

    # Demo prediction
    demo_job = {
        "title": "Data Scientist",
        "location": "Bangalore, Karnataka",
        "skills": "python,machine learning,tensorflow,aws,docker",
        "company_size": "Enterprise",
    }
    result = predictor.predict(demo_job)
    print(f"\n🔮 Demo prediction for Data Scientist @ Bangalore:")
    print(f"   Salary: ₹{result['min']}L - ₹{result['max']}L (avg ₹{result['avg']}L)")
    print(f"   Method: {result['method']}, Confidence: {result['confidence']}")


if __name__ == "__main__":
    main()
