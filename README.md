# LinkedIn Job Analysis Tool

A comprehensive Python tool for scraping, analyzing, and visualizing job market data. Get insights on in-demand skills, top companies, salary predictions, and personalized job recommendations.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Features

- **Job Scraping** - Fetch real-time job listings from APIs
- **Data Analysis** - Extract insights on skills, companies, locations
- **Visualizations** - Charts and graphs for job market trends
- **Resume Matching** - Match your skills to job listings
- **Salary Prediction** - Predict salary based on role, location, skills
- **Job Alerts** - Get notified when jobs match your criteria
- **Web Dashboard** - View all insights in a web browser
- **REST API** - Access data programmatically
- **Export** - Export to Excel, PDF, CSV

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/Linkedin-Job-Analysis.git
cd Linkedin-Job-Analysis

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Run the Complete Flow

```bash
# Interactive mode - asks for data source (Real-time API or Local)
python scripts/master_flow.py

# Use real-time API data
python scripts/master_flow.py --realtime

# Use local stored data
python scripts/master_flow.py --local

# Quick mode (minimal prompts)
python scripts/master_flow.py --local --quick
```

### Using the CLI

```bash
python scripts/cli.py <command> [options]

# Available commands:
python scripts/cli.py flow              # Run master flow
python scripts/cli.py scrape            # Fetch fresh data from API
python scripts/cli.py analyze           # Analyze job data
python scripts/cli.py dashboard         # Start web dashboard
python scripts/cli.py match --profile   # Create your profile
python scripts/cli.py match             # Find matching jobs
python scripts/cli.py predict "Python Developer" --location Bangalore
python scripts/cli.py export --excel    # Export to Excel
python scripts/cli.py alerts --check    # Check job alerts
python scripts/cli.py insights          # Market insights
```

## Project Structure

```
Linkedin-Job-Analysis/
├── config/
│   ├── settings.yaml           # Configuration
│   ├── alerts/                 # Job alert definitions
│   └── user_profile.json       # Your profile for matching
├── data/
│   ├── raw/                    # Scraped job data (CSV/JSON)
│   ├── processed/              # Cleaned data
│   ├── exports/                # Exported files (Excel, PDF)
│   └── jobs.db                 # SQLite database
├── scripts/
│   ├── master_flow.py          # Main entry point
│   ├── cli.py                  # Command-line interface
│   ├── scraper_india.py        # Job scraper
│   ├── analyze_jobs.py         # Data analysis
│   ├── visualize_data.py       # Create charts
│   ├── generate_report.py      # Generate reports
│   ├── dashboard.py            # Web dashboard
│   ├── api_server.py           # REST API
│   ├── resume_matcher.py       # Resume matching
│   ├── salary_predictor.py     # Salary prediction
│   ├── job_alerts.py           # Job alerts
│   ├── market_insights.py      # AI insights
│   ├── export_manager.py       # Export to Excel/PDF
│   └── ...
├── outputs/
│   ├── visualizations/         # PNG charts
│   └── reports/                # HTML/JSON reports
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    MASTER FLOW                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. SELECT DATA SOURCE                                       │
│     ├── [1] Real-time API (fresh data)                      │
│     └── [2] Local stored data (instant)                     │
│                                                              │
│  2. ANALYZE DATA → Skills, Companies, Locations, Trends     │
│                                                              │
│  3. USER PROFILE → Your skills & preferences                │
│                                                              │
│  4. JOB MATCHING → Find best jobs for you                   │
│                                                              │
│  5. SKILL GAPS → What to learn + Certifications             │
│                                                              │
│  6. VISUALIZATIONS → Charts & Reports                       │
│                                                              │
│  7. DASHBOARD → View at http://localhost:5000               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Screenshots

### Dashboard
- Overview with job statistics
- Skills trending analysis
- Jobs by company/location
- Your profile matches

### Reports
- HTML reports with charts
- Excel exports with multiple sheets
- PDF professional reports

## Configuration

Edit `config/settings.yaml`:

```yaml
scraper:
  keywords:
    - "python developer"
    - "data scientist"
  locations:
    - "Bangalore"
    - "Mumbai"

email:
  enabled: false
  smtp_server: "smtp.gmail.com"
  sender_email: "your_email@gmail.com"

scheduler:
  enabled: false
  run_time: "09:00"
  frequency: "daily"
```

## API Endpoints

Start API server: `python scripts/api_server.py`

| Endpoint | Description |
|----------|-------------|
| `GET /api/jobs` | List all jobs |
| `GET /api/jobs/search?q=python` | Search jobs |
| `GET /api/stats` | Statistics |
| `GET /api/skills` | Skill rankings |
| `GET /api/companies` | Top companies |

## Docker Deployment

```bash
# Build and run
docker-compose up -d

# Access
# Dashboard: http://localhost:5000
# API: http://localhost:8000
```

## Dependencies

- pandas, numpy - Data processing
- matplotlib, seaborn, plotly - Visualization
- requests, beautifulsoup4 - Web scraping
- openpyxl - Excel export
- reportlab - PDF generation
- pyyaml - Configuration
- schedule - Task scheduling

## License

MIT License

## Author

Rohit Mane

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
