# 💼 LinkedIn Job Trend Analysis

> **An end-to-end data analytics project that collects real job postings, analyzes market trends, and helps job seekers understand what skills companies actually demand — all presented through an interactive visual dashboard.**

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 📌 1. Project Overview

**What does this project do?**

Imagine you're searching for a tech job in India — Data Scientist, Software Engineer, or any role. Before applying, you'd want to know:

- *"What skills are companies actually asking for right now?"*
- *"Which cities have the most job openings?"*
- *"What salary can I expect for my experience level?"*
- *"Which companies are hiring the most?"*
- *"How well does my resume match the current market?"*

This project **automatically answers all of these questions** by:

1. **Collecting** hundreds of real job postings from job portals and APIs
2. **Cleaning & organizing** the raw data (removing duplicates, standardizing formats)
3. **Analyzing** the data to reveal trends, patterns, and insights
4. **Visualizing** everything in a beautiful, interactive web dashboard
5. **Matching** your resume to the best-fit jobs and predicting your expected salary

> **In simple terms:** This is like having a personal job market researcher that works 24/7, reads every job posting for you, and tells you exactly what the market looks like.

---

## 📌 2. Core Concepts Explained

Here are the key ideas behind this project, explained simply:

| Concept | What It Means |
|---------|---------------|
| **Web Scraping** | Automatically visiting job websites and extracting job listings — like copy-pasting, but done by a program for hundreds of jobs at once |
| **API Data Collection** | Fetching job data from official services (like Adzuna) that provide structured data through a digital "door" designed for programs |
| **Data Cleaning** | Raw job data is messy — different companies write "Bangalore", "Bengaluru", or "BLR". Cleaning means standardizing everything into one consistent format |
| **NLP (Natural Language Processing)** | Teaching the computer to "read" job descriptions and extract skills like Python, SQL, or Machine Learning from plain text |
| **Skill Extraction** | Scanning each job description to identify which technical skills (Python, AWS, SQL, etc.) the company is looking for |
| **Resume Matching** | Comparing your skills against each job's requirements and calculating a "match percentage" — like a compatibility score |
| **Salary Prediction** | Using a trained Machine Learning model to estimate what salary you can expect based on your role, location, and skills |
| **Trend Forecasting** | Looking at how skill demand has changed over time and predicting which skills will grow or decline in the future |
| **Interactive Dashboard** | A visual web page (like a website) where all the charts, tables, and insights are displayed — no coding needed to use it |

---

## 📌 3. Methodology — How the Project Works

The project follows a structured **data analytics pipeline** — a step-by-step process where each stage feeds into the next:

```
 ┌──────────────────────────────────────────────────────────────────────────┐
 │                        PROJECT WORKFLOW                                  │
 │                                                                          │
 │   STEP 1: DATA COLLECTION                                               │
 │   ├── Fetch jobs from Adzuna API (real listings)                        │
 │   ├── Fetch jobs from RemoteOK API (remote jobs)                        │
 │   └── Generate sample data for testing/demos                            │
 │                           ▼                                              │
 │   STEP 2: DATA CLEANING & PROCESSING                                    │
 │   ├── Remove duplicate job posts                                        │
 │   ├── Standardize city names, job titles, company names                 │
 │   ├── Parse salary ranges into numbers                                  │
 │   └── Extract skills from job descriptions using NLP                    │
 │                           ▼                                              │
 │   STEP 3: DATA ANALYSIS                                                  │
 │   ├── Count top job titles, companies, locations                        │
 │   ├── Rank the most in-demand skills                                    │
 │   ├── Analyze experience level distribution                             │
 │   └── Calculate salary statistics by role & location                    │
 │                           ▼                                              │
 │   STEP 4: MACHINE LEARNING                                               │
 │   ├── Train a salary prediction model (Gradient Boosting)               │
 │   ├── Build a resume matching algorithm (skill-based scoring)           │
 │   └── Forecast future skill demand (linear regression)                  │
 │                           ▼                                              │
 │   STEP 5: VISUALIZATION & DASHBOARD                                      │
 │   ├── Generate charts: bar graphs, pie charts, trend lines              │
 │   ├── Build interactive Streamlit dashboard (6 pages)                   │
 │   └── Export reports to Excel, PDF, CSV                                 │
 │                                                                          │
 └──────────────────────────────────────────────────────────────────────────┘
```

### What happens at each step:

**Step 1 — Data Collection:**
The system connects to job listing APIs (Adzuna, RemoteOK) and fetches real job postings. Each posting includes the job title, company name, location, description, and sometimes salary. This is like automatically browsing hundreds of LinkedIn job pages and noting down the details.

**Step 2 — Data Cleaning:**
Real-world data is messy. The same company might be listed as "TCS", "Tata Consultancy Services", or "tata consultancy". The cleaner module standardizes all such variations, removes duplicate listings, and fills in missing information where possible.

**Step 3 — Data Analysis:**
Once the data is clean, the analyzer counts things: How many jobs mention "Python"? Which city has the most openings? What's the average salary for a Data Scientist in Pune? All these statistics are computed and saved as structured reports.

**Step 4 — Machine Learning:**
The system uses the analyzed data to build intelligent features:
- A **salary predictor** learns the relationship between job role, location, skills, and salary to estimate what you should earn
- A **resume matcher** compares your profile against all jobs and ranks them by fit
- A **trend forecaster** looks at historical skill demand to predict the future

**Step 5 — Visualization & Dashboard:**
All insights are presented in a beautiful interactive dashboard. You can explore charts, filter data, upload your resume, and get personalized recommendations — all in your web browser.

---

## 📌 4. Input Datasets & APIs Used

### 📊 Where does the data come from?

| Source | Type | What It Provides | Access |
|--------|------|-------------------|--------|
| **Adzuna API** | Real-Time API | Real job listings across Indian cities — titles, companies, locations, salaries, descriptions | Free API key from [developer.adzuna.com](https://developer.adzuna.com/) |
| **RemoteOK API** | Real-Time API | Remote/global tech job listings with tags and salary ranges | Free, no API key needed |
| **Sample Data Generator** | Built-in | 1,000+ realistic synthetic job records for testing and demos when APIs aren't available | No setup needed |

### 📁 Data Files Used

| File | Location | Description |
|------|----------|-------------|
| `jobs_india_*.csv` | `data/raw/` | Raw collected job data in spreadsheet format (CSV) — one row per job |
| `jobs_india_*.json` | `data/raw/` | Raw collected job data in JSON format (machine-readable) |
| `jobs_cleaned.csv` | `data/processed/` | Cleaned, deduplicated, standardized job data |
| `jobs.db` | `data/` | SQLite database storing all jobs for fast querying |
| `skills_config.json` | `config/` | Master list of 100+ technical skills organized by category — the "vocabulary" used to identify skills in job descriptions |
| `user_profile.json` | `config/` | Your personal profile (skills, experience, preferred locations) for job matching |
| `settings.yaml` | `config/` | Project configuration — search keywords, target cities, notification settings |

### 📋 What does a single job record look like?

Each job record stored in the system contains:

| Field | Example | Meaning |
|-------|---------|---------|
| `title` | Data Scientist | The job role being advertised |
| `company` | Infosys | The company offering the job |
| `location` | Bangalore, Karnataka | Where the job is based |
| `skills` | python, sql, machine learning, pandas | Skills extracted from the job description |
| `experience_level` | Mid-Level | Required experience tier |
| `salary_min` / `salary_max` | 800000 / 1500000 | Salary range in INR (when available) |
| `post_date` | 2026-01-15 | When the job was posted |
| `source` | Adzuna India | Which API/source the job came from |

---

## 📌 5. Working Flow — How to Run the Project

### 🔧 One-Time Setup

```bash
# 1. Clone (download) the project
git clone https://github.com/rohitmane45/LinkedIn-Job-Trend-Analysis.git
cd LinkedIn-Job-Trend-Analysis

# 2. Create a virtual environment (isolated workspace)
python -m venv .venv
.venv\Scripts\activate        # On Windows
# source .venv/bin/activate   # On Mac/Linux

# 3. Install all required libraries
pip install -r requirements.txt
```

### 🚀 Running the Full Pipeline

```bash
# Runs everything automatically: data collection → cleaning → analysis → dashboard
python scripts/master_flow.py

# Or with specific options:
python scripts/master_flow.py --local    # Use already-downloaded data
python scripts/master_flow.py --realtime # Fetch fresh data from APIs
```

### 📊 Launching the Dashboard

```bash
python -m streamlit run scripts/streamlit_app.py
# Opens at → http://localhost:8501
```

### 🖥️ The Dashboard Has 6 Pages

| Page | What You'll See |
|------|-----------------|
| **🏠 Overview** | Total jobs analyzed, top companies, locations, and experience distribution — the big picture |
| **📊 Skill Trends** | Which skills are most in-demand right now, ranked and categorized |
| **🏢 Companies** | Which companies are hiring the most, with visual breakdowns |
| **💰 Salary Predictor** | Enter a job title, location, and skills → get an estimated salary range |
| **📄 Resume Match** | Upload your PDF resume → instantly see matching jobs ranked by compatibility |
| **🔮 Forecast** | Which skills are rising, stable, or declining — predicted 90 days into the future |

### 🔄 Other Useful Commands

```bash
python scripts/cli.py scrape         # Fetch fresh job data
python scripts/cli.py analyze        # Run analysis on existing data
python scripts/cli.py match          # Find jobs matching your profile
python scripts/cli.py export --excel # Export data to Excel/PDF
python scripts/cli.py insights       # Generate AI-powered market insights
```

---

## 📌 6. Techniques & Technologies Used

### 🛠️ Programming & Libraries

| Technology | What It Does in This Project |
|------------|------------------------------|
| **Python 3.9+** | The programming language used for the entire project |
| **Pandas** | Reading, filtering, and manipulating job data in table format |
| **NumPy** | Mathematical operations — averages, percentiles, trends |
| **Requests** | Making HTTP calls to job APIs to fetch data |
| **BeautifulSoup** | Parsing raw HTML web pages to extract useful information |
| **Plotly** | Creating interactive charts (bar graphs, pie charts, scatter plots) |
| **Streamlit** | Building the interactive web dashboard — no HTML/CSS needed |
| **Scikit-learn** | Machine learning library used for salary prediction model |
| **PDFPlumber** | Reading and extracting text from uploaded PDF resumes |
| **SQLite** | Lightweight database for storing and querying job records |
| **YAML / JSON** | Configuration file formats for settings and data storage |

### 🤖 Machine Learning & AI Techniques

| Technique | Where It's Used | How It Works (Simply) |
|-----------|-----------------|----------------------|
| **Gradient Boosting Regressor** | Salary Prediction | Learns from hundreds of past job-salary pairs to predict salary for new jobs. It builds many small "decision trees" that each correct the previous one's mistakes |
| **TF-IDF + Cosine Similarity** | Resume Matching | Converts skills into numerical vectors and measures how "close" your resume is to each job — like measuring distance between two points |
| **Linear Regression** | Skill Trend Forecasting | Draws a trend line through historical skill counts over time and extends it into the future to predict demand |
| **NLP Pattern Matching** | Skill Extraction | Scans job descriptions word-by-word looking for known skill names (Python, SQL, etc.) using a master dictionary of 100+ skills |
| **Sentence Transformers** | Semantic Matching (Optional) | Advanced AI that understands meaning — knows "ML" and "Machine Learning" mean the same thing, even if written differently |

### 🌐 APIs & External Services

| API / Service | Purpose | Cost |
|---------------|---------|------|
| **Adzuna API** | Fetching real job listings from India (Bangalore, Pune, Mumbai, etc.) | Free (requires registration) |
| **RemoteOK API** | Fetching remote tech job listings globally | Free (no key needed) |
| **FastAPI** | Exposing project data as a REST API for programmatic access | Open-source |
| **GitHub Actions** | Automated CI/CD — runs tests automatically on every code push | Free for public repos |

### 📐 Data Processing Techniques

| Technique | What It Does |
|-----------|--------------|
| **Deduplication** | Removes duplicate job postings (same job from different sources) |
| **Fuzzy Matching** | Recognizes that "Bengaluru" and "Bangalore" are the same city |
| **Normalization** | Standardizes formats — "sr. developer" → "Senior Developer" |
| **Missing Value Handling** | Fills in missing salary, location, or experience data using smart defaults |
| **Feature Engineering** | Creates new data columns from existing ones (e.g., extracting "years of experience" from text) |

---

## 📌 7. Project Structure

```
LinkedIn-Job-Trend-Analysis/
│
├── config/                     ← Settings & configuration files
│   ├── settings.yaml           ← Search keywords, cities, notifications
│   ├── skills_config.json      ← Master dictionary of 100+ technical skills
│   ├── user_profile.json       ← Your profile for job matching
│   └── alerts/                 ← Saved job alert filters
│
├── data/                       ← All data files
│   ├── raw/                    ← Original collected job data (CSV + JSON)
│   ├── processed/              ← Cleaned & standardized data
│   ├── exports/                ← Exported reports (Excel, PDF, CSV)
│   └── jobs.db                 ← SQLite database
│
├── scripts/                    ← All Python code
│   ├── master_flow.py          ← 🚀 Main entry point — runs everything
│   ├── cli.py                  ← Command-line interface
│   ├── scraper_v2.py           ← Fetches jobs from APIs
│   ├── cleaner.py              ← Cleans & standardizes data
│   ├── analyze_jobs.py         ← Computes statistics & insights
│   ├── streamlit_app.py        ← 📊 Interactive dashboard (6 pages)
│   ├── salary_predictor.py     ← 💰 ML salary prediction
│   ├── resume_matcher.py       ← 📄 Resume-to-job matching
│   ├── resume_parser.py        ← Extracts info from PDF resumes
│   ├── trend_tracker.py        ← 🔮 Skill trend forecasting
│   ├── visualize_data.py       ← Chart generation
│   ├── api_server.py           ← REST API server
│   └── ...                     ← Supporting modules
│
├── models/                     ← Trained ML models
│   └── salary_model.pkl        ← Saved salary prediction model
│
├── outputs/                    ← Generated outputs
│   ├── visualizations/         ← PNG chart images
│   └── reports/                ← Analysis reports (HTML, JSON)
│
├── tests/                      ← Automated tests (112 tests)
├── .github/workflows/          ← CI/CD pipeline configuration
├── requirements.txt            ← Python library dependencies
├── Dockerfile                  ← Docker container setup
└── docker-compose.yml          ← Multi-container deployment
```

---

## 📌 8. Key Results & Deliverables

This project produces the following outputs:

| Output | Format | Description |
|--------|--------|-------------|
| **Interactive Dashboard** | Web (Streamlit) | 6-page visual dashboard accessible in your browser |
| **Skills Ranking Report** | JSON / HTML | Top 50+ in-demand skills ranked by frequency |
| **Company Hiring Report** | JSON / HTML | Top hiring companies with job counts |
| **Salary Estimates** | Dashboard | Predicted salary ranges for any role + location |
| **Resume Match Results** | Dashboard | Your top job matches with compatibility scores |
| **Skill Forecast** | Dashboard | 90-day predictions for rising and declining skills |
| **Excel Export** | `.xlsx` | Multi-sheet workbook with all analysis data |
| **PDF Report** | `.pdf` | Professional formatted analysis report |
| **REST API** | JSON endpoints | Programmatic access to all project data |

---

## 👤 Author

**Rohit Mane**

## 📄 License

MIT License — free to use, modify, and distribute.

---

> *Built with ❤️ using Python, Streamlit, Plotly, and Machine Learning*
