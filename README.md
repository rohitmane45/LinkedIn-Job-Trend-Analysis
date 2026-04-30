<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge" alt="License"/>
  <img src="https://img.shields.io/badge/CI-Passing-48bb78?style=for-the-badge&logo=github-actions&logoColor=white" alt="CI"/>
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/Dashboard-Live-6c63ff?style=for-the-badge" alt="Dashboard"/>
</p>



<p align="center">
  <strong>An end-to-end data intelligence platform that scrapes, analyzes, and visualizes LinkedIn job market trends across India — featuring AI-powered salary prediction, resume matching, skill forecasting, and an interactive dashboard.</strong>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-screenshots">Screenshots</a> •
  <a href="#%EF%B8%8F-architecture">Architecture</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-project-structure">Project Structure</a> •
  <a href="#-api-reference">API</a> •
  <a href="#-contributing">Contributing</a>
</p>

---

## 🎯 Overview

**JobAnalytics** is a production-grade data science project that transforms raw LinkedIn job postings into actionable career intelligence. Built with a modular Python pipeline and a premium glassmorphic dashboard, it serves as both an analytical tool and a portfolio-quality demonstration of full-stack data engineering.

> **Why this project?** The Indian tech job market is vast and constantly shifting. JobAnalytics brings clarity — tracking 50+ skills, 100+ companies, and 10+ cities to reveal what's trending, what pays well, and where your career should go next.

---

## ✨ Features

| Module | Description |
|--------|-------------|
| 🔍 **Smart Scraper** | Multi-keyword, multi-city job scraping with rate limiting, retry logic, and anti-detection measures |
| 🧹 **Data Cleaner** | NLP-powered skill extraction, deduplication, salary normalization, and company classification |
| 📊 **Analytics Engine** | Aggregation of skills, titles, companies, locations, experience levels, and market trends |
| 🤖 **Salary Predictor** | ML-based salary estimation using role, city, experience, and skill inputs (scikit-learn) |
| 📄 **Resume Matcher** | Profile-to-job matching with skill gap analysis and personalized learning recommendations |
| 📈 **Trend Forecaster** | 90-day demand forecasting with confidence intervals for top skills |
| 🏢 **Company Explorer** | Filterable company directory with hiring volume, skill stacks, and type classification |
| 🖥️ **Interactive Dashboard** | Premium glassmorphic web UI with Chart.js visualizations, animated counters, and real-time API data |
| 📬 **Notifications** | Configurable email, Slack, and Discord alerts for new job matches |
| 📦 **Export Manager** | One-click export to Excel, PDF, and HTML report formats |
| ⏰ **Scheduler** | Automated daily/weekly pipeline runs with cron-style scheduling |
| 🐳 **Docker Support** | Containerized deployment with Docker Compose for dashboard, API, and scheduler services |

---

## 📸 Screenshots


### Dashboard Overview
<!-- Replace the path below with your actual screenshot -->
<p align="center">
  <img src="D:\Projects\Linkedin-Job-Analysis\assets\screenshots\image.png" alt="Dashboard Overview — Stats, Top Skills, Experience Distribution, Jobs by City" width="90%" />
</p>


### AI Salary Predictor
<p align="center">
  <img src="D:\Projects\Linkedin-Job-Analysis\assets\screenshots\salarypre.png" alt="Salary Predictor — Role, City, Experience based ML Prediction" width="90%" />
</p>

### Resume Match & Skill Gap Analysis
<p align="center">
  <img src="D:\Projects\Linkedin-Job-Analysis\assets\screenshots\resumematch.png" alt="Resume Matcher — Job Matching Scores and Skill Gap Analysis" width="90%" />
</p>

### 90-Day Demand Forecast
<p align="center">
  <img src="D:\Projects\Linkedin-Job-Analysis\assets\screenshots\skillforecast.png" alt="Forecast — 90-Day Skill Demand Predictions with Confidence Levels" width="90%" />
</p>

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                       JobAnalytics Pipeline                        │
├──────────┬──────────┬───────────┬──────────┬──────────┬────────────┤
│          │          │           │          │          │            │
│  SCRAPER │  CLEANER │ ANALYZER  │ ML MODELS│ MATCHER  │  EXPORTER  │
│          │          │           │          │          │            │
│ • API    │ • NLP    │ • Skills  │ • Salary │ • Resume │ • Excel    │
│ • Multi  │ • Dedup  │ • Titles  │   Pred.  │   Match  │ • PDF      │
│   city   │ • Norm.  │ • Cities  │ • Trend  │ • Skill  │ • HTML     │
│ • Rate   │ • Skill  │ • Comps.  │   Forec. │   Gaps   │ • JSON     │
│   limit  │   Extr.  │ • Trends  │          │          │            │
└────┬─────┴────┬─────┴─────┬─────┴────┬─────┴────┬─────┴──────┬─────┘
     │          │           │          │          │            │
     ▼          ▼           ▼          ▼          ▼            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                   │
│  SQLite DB  │  JSON Files  │  CSV Exports  │  Trained Models (.pkl) │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                    ┌───────────▼────────────┐
                    │   DASHBOARD SERVER     │
                    │  (Python HTTP + API)   │
                    │                        │
                    │  GET /api/data         │
                    │  GET /api/salary/...   │
                    │  Static file server    │
                    └───────────┬────────────┘
                                │
                    ┌───────────▼────────────┐
                    │   GLASSMORPHIC UI      │
                    │  HTML + CSS + JS       │
                    │                        │
                    │  • Chart.js visuals    │
                    │  • Animated counters   │
                    │  • Real-time API fetch │
                    │  • Responsive layout   │
                    └────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **pip** (package manager)
- **Git**

### 1. Clone the Repository

```bash
git clone https://github.com/rohitmane45/LinkedIn-Job-Trend-Analysis.git
cd LinkedIn-Job-Trend-Analysis
```

### 2. Create Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Full Pipeline

```bash
# Interactive mode — walks you through each step
python scripts/master_flow.py

# Quick mode — runs everything automatically
python scripts/master_flow.py --quick --local

# Just launch the dashboard
python scripts/master_flow.py --dashboard-only
```

### 5. Open the Dashboard

Navigate to **http://localhost:8080/index.html** in your browser.

---

## 🐳 Docker Deployment

```bash
# Build and start all services
docker-compose up --build

# Start only the dashboard
docker-compose up dashboard

# Run with scheduler automation
docker-compose --profile automation up
```

| Service | Port | Description |
|---------|------|-------------|
| `dashboard` | `5000` | Interactive web dashboard |
| `api` | `8000` | RESTful API server |
| `scheduler` | — | Automated pipeline runner |

---

## 🛠️ Tech Stack

<table>
  <tr>
    <th>Layer</th>
    <th>Technology</th>
    <th>Purpose</th>
  </tr>
  <tr>
    <td rowspan="3"><strong>Backend</strong></td>
    <td><img src="https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white"/></td>
    <td>Core pipeline, scraping, analysis, ML</td>
  </tr>
  <tr>
    <td><img src="https://img.shields.io/badge/scikit--learn-F7931E?style=flat&logo=scikitlearn&logoColor=white"/></td>
    <td>Salary prediction model</td>
  </tr>
  <tr>
    <td><img src="https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white"/></td>
    <td>RESTful API endpoints</td>
  </tr>
  <tr>
    <td rowspan="3"><strong>Frontend</strong></td>
    <td><img src="https://img.shields.io/badge/HTML5-E34F26?style=flat&logo=html5&logoColor=white"/></td>
    <td>Dashboard structure</td>
  </tr>
  <tr>
    <td><img src="https://img.shields.io/badge/CSS3-1572B6?style=flat&logo=css3&logoColor=white"/></td>
    <td>Glassmorphic + Neumorphic design</td>
  </tr>
  <tr>
    <td><img src="https://img.shields.io/badge/Chart.js-FF6384?style=flat&logo=chartdotjs&logoColor=white"/></td>
    <td>Interactive data visualizations</td>
  </tr>
  <tr>
    <td rowspan="2"><strong>Data</strong></td>
    <td><img src="https://img.shields.io/badge/Pandas-150458?style=flat&logo=pandas&logoColor=white"/></td>
    <td>Data manipulation & analysis</td>
  </tr>
  <tr>
    <td><img src="https://img.shields.io/badge/SQLite-003B57?style=flat&logo=sqlite&logoColor=white"/></td>
    <td>Persistent job data storage</td>
  </tr>
  <tr>
    <td rowspan="2"><strong>DevOps</strong></td>
    <td><img src="https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white"/></td>
    <td>Containerized deployment</td>
  </tr>
  <tr>
    <td><img src="https://img.shields.io/badge/GitHub%20Actions-2088FF?style=flat&logo=github-actions&logoColor=white"/></td>
    <td>CI/CD — Lint & test pipeline</td>
  </tr>
</table>

---

## 📁 Project Structure

```
LinkedIn-Job-Trend-Analysis/
├── 📂 scripts/                    # Core pipeline modules
│   ├── master_flow.py             # 🎮 Main orchestrator (9-step pipeline)
│   ├── scraper_v2.py              # 🔍 Advanced job scraper
│   ├── scraper_india.py           # 🇮🇳 India-specific scraper
│   ├── cleaner.py                 # 🧹 Data cleaning & normalization
│   ├── analyze_jobs.py            # 📊 Statistical analysis engine
│   ├── nlp_skill_extractor.py     # 🧠 NLP-based skill extraction
│   ├── salary_predictor.py        # 💰 ML salary prediction model
│   ├── resume_matcher.py          # 📄 Resume-job matching engine
│   ├── resume_parser.py           # 📑 PDF resume parser
│   ├── embedding_matcher.py       # 🔗 Semantic similarity matching
│   ├── trend_tracker.py           # 📈 Skill trend analysis
│   ├── market_insights.py         # 🔬 Market intelligence reports
│   ├── dashboard_server.py        # 🖥️ Dashboard HTTP + API server
│   ├── api_server.py              # 🌐 FastAPI REST endpoints
│   ├── dashboard.py               # 📊 Legacy dashboard
│   ├── streamlit_app.py           # 🎨 Streamlit dashboard (alt.)
│   ├── visualize_data.py          # 📉 Matplotlib/Seaborn charts
│   ├── generate_report.py         # 📝 HTML/PDF report generator
│   ├── export_manager.py          # 📦 Excel/PDF/JSON exporter
│   ├── job_alerts.py              # 🔔 Job alert system
│   ├── notification_manager.py    # 📬 Email/Slack/Discord notifs
│   ├── scheduler.py               # ⏰ Automated scheduling
│   ├── database.py                # 💾 SQLite database manager
│   ├── data_source_manager.py     # 📡 Data source selection
│   ├── cli.py                     # ⌨️ Command-line interface
│   └── skills_loader.py           # 📚 Skills configuration loader
│
├── 📂 templates/                  # Dashboard frontend
│   ├── index.html                 # 🏠 Main dashboard page
│   ├── styles.css                 # 🎨 Glassmorphic design system
│   └── app.js                     # ⚡ Client-side logic & Chart.js
│
├── 📂 config/                     # Configuration files
│   ├── settings.yaml              # ⚙️ App configuration
│   ├── skills_config.json         # 🧩 Tracked skills & categories
│   └── salary_model.json          # 💰 Salary model parameters
│
├── 📂 models/                     # Trained ML models
│   └── salary_model.pkl           # 🤖 Serialized salary predictor
│
├── 📂 data/                       # Data storage
│   ├── raw/                       # 📥 Raw scraped JSON files
│   ├── processed/                 # 🔄 Cleaned & transformed data
│   ├── exports/                   # 📤 Exported files (Excel, PDF)
│   └── jobs.db                    # 💾 SQLite database
│
├── 📂 outputs/                    # Generated outputs
│   ├── reports/                   # 📊 Analysis reports (JSON, HTML)
│   └── visualizations/            # 📉 Charts & graphs (PNG)
│
├── 📂 tests/                      # Test suite (12 test modules)
│   ├── conftest.py                # Test fixtures & configuration
│   ├── test_analyze_jobs.py       # Analysis engine tests
│   ├── test_salary_predictor.py   # Salary model tests
│   ├── test_resume_matcher.py     # Resume matcher tests
│   └── ...                        # Additional test modules
│
├── 📂 notebooks/                  # Jupyter notebooks
│   └── job_analysis.ipynb         # 🔬 Exploratory data analysis
│
├── 📂 .github/workflows/         # CI/CD
│   └── ci.yml                     # ✅ Lint (ruff) + Test (pytest)
│
├── Dockerfile                     # 🐳 Container image definition
├── docker-compose.yml             # 🐳 Multi-service orchestration
├── requirements.txt               # 📦 Python dependencies
├── LICENSE                        # 📜 MIT License
└── README.md                      # 📖 You are here
```

---

## 🔌 API Reference

The dashboard server exposes a lightweight JSON API:

### `GET /api/data`

Returns the complete dataset used by the dashboard.

<details>
<summary><strong>Response Schema</strong></summary>

```json
{
  "overview": {
    "total_jobs": 1200,
    "total_companies": 85,
    "total_cities": 6,
    "total_skills": 50,
    "last_updated": "2026-04-30T08:00:00",
    "top_skills": { "Python": 450, "SQL": 380, "AWS": 310 },
    "experience_distribution": { "Entry Level": 300, "Mid Level": 600, "Senior": 300 },
    "top_titles": { "Data Scientist": 150, "Software Engineer": 130 },
    "jobs_by_city": { "Bangalore": 400, "Mumbai": 250 }
  },
  "skills": { "trends": [...], "categories": {...} },
  "companies": [...],
  "salary": { "base_salaries": {...}, "city_multipliers": {...} },
  "resume": { "user_profile": {...}, "matches": [...], "have_skills": [...], "gap_skills": [...] },
  "forecast": { "skills": [...], "emerging": [...] }
}
```

</details>

### `GET /api/salary/predict`

Predicts salary based on input parameters.

| Parameter | Type | Example | Description |
|-----------|------|---------|-------------|
| `role` | string | `Data Scientist` | Job role/title |
| `city` | string | `Bangalore` | City name |
| `exp` | integer | `3` | Years of experience |

```bash
curl "http://localhost:8080/api/salary/predict?role=Data+Scientist&city=Bangalore&exp=3"
```

```json
{
  "low": 16.9,
  "high": 22.3,
  "median": 19.6,
  "gauge_pct": 56
}
```

---

## ⚡ CLI Commands

```bash
# Full interactive pipeline
python scripts/master_flow.py

# Quick run with local data
python scripts/master_flow.py --quick --local

# Fetch fresh data from API
python scripts/master_flow.py --realtime

# Launch only the dashboard
python scripts/master_flow.py --dashboard-only

# Run the scraper standalone
python scripts/scraper_india.py

# Run analysis on existing data
python scripts/analyze_jobs.py

# Generate reports
python scripts/generate_report.py --format html

# Export data to Excel
python scripts/export_manager.py --excel

# Start the scheduler
python scripts/scheduler.py --start

# Run tests
python -m pytest tests/ -v
```

---

## 🧪 Testing

The project includes a comprehensive test suite with **12 test modules** covering all major components:

```bash
# Run all tests
python -m pytest tests/ -v --tb=short

# Run specific module tests
python -m pytest tests/test_salary_predictor.py -v
python -m pytest tests/test_resume_matcher.py -v

# Run with coverage
python -m pytest tests/ --cov=scripts --cov-report=html
```

**CI/CD**: Tests run automatically on every push and pull request via GitHub Actions (Python 3.10, 3.11).

---

## 🔧 Configuration

Copy and customize the settings file:

```bash
cp config/settings.example.yaml config/settings.yaml
```

Key configuration options:

```yaml
# Scraping targets
scraper:
  keywords: ["data scientist", "python developer", "ml engineer"]
  locations: ["Bangalore", "Mumbai", "Delhi", "Hyderabad", "Pune"]
  max_jobs_per_search: 50

# Notification channels
email:
  enabled: true
  smtp_server: "smtp.gmail.com"

slack:
  enabled: true
  webhook_url: "https://hooks.slack.com/services/..."

# Scheduler
scheduler:
  enabled: true
  run_time: "09:00"
  frequency: "daily"
```

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'feat: add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

Please ensure your code passes linting and all tests before submitting:

```bash
ruff check scripts/ tests/
python -m pytest tests/ -v
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/rohitmane45">
        <img src="https://github.com/rohitmane45.png" width="100px;" alt="Rohit Mane" style="border-radius:50%"/>
        <br />
        <sub><b>Rohit Mane</b></sub>
      </a>
      <br />
      <sub>AI & Data Science</sub>
      <br />
      <a href="https://github.com/rohitmane45">GitHub</a> •
      <a href="https://linkedin.com/in/rohitmane45">LinkedIn</a>
    </td>
  </tr>
</table>

---

<p align="center">
  <strong>⭐ If this project helped you, consider giving it a star!</strong>
  <br/>
  <br/>
  <img src="https://img.shields.io/github/stars/rohitmane45/LinkedIn-Job-Trend-Analysis?style=social" alt="Stars"/>
  <img src="https://img.shields.io/github/forks/rohitmane45/LinkedIn-Job-Trend-Analysis?style=social" alt="Forks"/>
</p>
