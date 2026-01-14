# LinkedIn Job Trend Analysis

A comprehensive data analysis project for scraping, cleaning, analyzing, and visualizing job market trends from job postings.

## 🎯 Project Overview

This project analyzes job market trends to identify:
- Most in-demand technical skills
- Geographic distribution of job opportunities
- Role-specific skill requirements
- Career recommendations based on market data

## 📁 Project Structure

```
linkedin_job_analysis/
│
├── data/
│   ├── raw/              # Raw scraped data
│   └── processed/        # Cleaned and processed data
├── notebooks/
│   └── job_analysis.ipynb  # Interactive Jupyter notebook
├── scripts/
│   ├── scraper.py        # Web scraping script
│   ├── cleaner.py        # Data cleaning script
│   └── analyzer.py       # Analysis and visualization script
├── visualizations/       # Output charts and reports
├── requirements.txt      # Python dependencies
└── README.md
```

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- pip package manager

### Installation

1. Clone or navigate to the project directory:
```bash
cd linkedin_job_analysis
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Analysis

#### Option 1: Using Python Scripts

```bash
# Step 1: Generate/Scrape data
cd scripts
python scraper.py

# Step 2: Clean the data
python cleaner.py

# Step 3: Run analysis and generate visualizations
python analyzer.py
```

#### Option 2: Using Jupyter Notebook (Recommended)

```bash
jupyter notebook notebooks/job_analysis.ipynb
```

## 📊 Output Deliverables

After running the analysis, you'll get:

### Visualizations (PNG files)
- `top_skills_bar.png` - Top 15 most in-demand skills
- `skills_city_heatmap.png` - Skill demand by city
- `skills_role_heatmap.png` - Skill vs role matrix
- `jobs_by_city.png` - Job distribution by city
- `role_distribution.png` - Job distribution by role category

### Interactive Charts (HTML files)
- `interactive_skills.html` - Interactive skill demand chart
- `interactive_heatmap.html` - Interactive skill-city heatmap

### Reports (Excel)
- `job_analysis_report_[timestamp].xlsx` - Complete analysis report

## 🔧 Key Features

### Data Collection
- Sample data generation for testing
- Built-in support for Indeed scraping
- Rate limiting and user-agent rotation
- Error handling and logging

### Data Cleaning
- Job title standardization
- Skill normalization
- Location parsing
- Duplicate removal

### Analysis
- Skill demand frequency
- Geographic analysis
- Role-based analysis
- Trend identification

### Visualization
- Publication-ready charts
- Interactive Plotly visualizations
- Heatmaps for cross-analysis
- Export to multiple formats

## 📈 Sample Insights

After analysis, you'll discover:
- **Top Skills**: Python, SQL, and cloud technologies dominate
- **Hot Cities**: San Francisco, New York, Seattle lead in tech jobs
- **Role Trends**: Data Science & ML roles show highest growth
- **Skill Combos**: Which skills pair together for specific roles

## ⚠️ Notes on Web Scraping

LinkedIn has anti-scraping measures. This project includes:
- **Sample data generator** for development/testing
- **Indeed scraper** as an alternative source
- **Rate limiting** to avoid blocking

For production use, consider:
- LinkedIn API (requires approval)
- Job aggregator APIs
- Public job datasets

## 🛠️ Customization

### Adding New Skills
Edit the `SKILLS_DICTIONARY` in `scraper.py`:
```python
SKILLS_DICTIONARY = {
    'python', 'java', 'your_new_skill', ...
}
```

### Modifying Title Mappings
Edit `TITLE_MAPPING` in `cleaner.py`:
```python
TITLE_MAPPING = {
    r'your_pattern': 'Standardized Title',
    ...
}
```

## 📝 License

This project is for educational purposes.

## 🤝 Contributing

Feel free to fork and enhance this project!

---

**Happy Analyzing! 📊**
