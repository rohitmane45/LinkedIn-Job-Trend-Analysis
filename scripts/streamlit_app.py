"""
LinkedIn Job Analysis — Professional Dashboard
=================================================
Interactive multi-page dashboard with PDF resume upload,
live job matching, skill forecasts, and apply links.

Usage:
    python -m streamlit run scripts/streamlit_app.py
"""

import sys
import os
import io
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from pathlib import Path
from datetime import datetime

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from dashboard_data import (
    load_latest_analysis,
    load_user_profile,
    load_job_matches,
    load_alert_matches,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"

# ════════════════════════════════════════════════════════════════
# Page Config
# ════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="LinkedIn Job Analysis",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ════════════════════════════════════════════════════════════════
# Premium CSS — Glassmorphism + Dark Theme
# ════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Global ────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
.main .block-container {
    padding: 1.2rem 2rem 2rem 2rem;
    max-width: 1400px;
}

/* ── Sidebar ───────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0f1a 0%, #111827 50%, #0a0f1a 100%);
    border-right: 1px solid rgba(99, 102, 241, 0.15);
}
section[data-testid="stSidebar"] .stRadio > label {
    color: #94a3b8 !important;
}

/* ── Glass Card (for metrics) ──────────────────── */
[data-testid="stMetric"] {
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 16px;
    padding: 20px 24px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(99, 102, 241, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.08);
}
[data-testid="stMetric"] label {
    color: #94a3b8 !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #818cf8 !important;
    font-weight: 700 !important;
    font-size: 1.6rem !important;
}

/* ── Hero Banner ───────────────────────────────── */
.hero-banner {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 40%, #4338ca 100%);
    border-radius: 20px;
    padding: 2.5rem 3rem;
    margin-bottom: 1.8rem;
    border: 1px solid rgba(129, 140, 248, 0.2);
    box-shadow: 0 20px 60px rgba(67, 56, 202, 0.2);
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(129, 140, 248, 0.15) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-banner h1 {
    color: #e0e7ff;
    font-weight: 800;
    font-size: 2rem;
    margin: 0 0 0.3rem 0;
}
.hero-banner p {
    color: #a5b4fc;
    font-size: 1rem;
    margin: 0;
    font-weight: 400;
}

/* ── Glass Panel ───────────────────────────────── */
.glass-panel {
    background: rgba(15, 23, 42, 0.5);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}

/* ── Match Card ────────────────────────────────── */
.match-card {
    background: rgba(15, 23, 42, 0.45);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(99, 102, 241, 0.12);
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.8rem;
    transition: all 0.25s ease;
}
.match-card:hover {
    border-color: rgba(129, 140, 248, 0.3);
    box-shadow: 0 8px 30px rgba(99, 102, 241, 0.1);
    transform: translateY(-1px);
}
.match-title {
    color: #e2e8f0; font-weight: 600; font-size: 1.05rem; margin: 0;
}
.match-company {
    color: #818cf8; font-weight: 500; font-size: 0.9rem;
}
.match-meta {
    color: #64748b; font-size: 0.8rem; margin-top: 4px;
}
.match-score {
    font-size: 1.8rem; font-weight: 800; text-align: center; line-height: 1;
}
.match-score-label {
    font-size: 0.7rem; color: #64748b; text-align: center; text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* ── Skill Badge ───────────────────────────────── */
.skill-badge {
    display: inline-block;
    background: rgba(99, 102, 241, 0.15);
    color: #a5b4fc;
    border: 1px solid rgba(99, 102, 241, 0.25);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.78rem;
    font-weight: 500;
    margin: 2px 3px;
}
.skill-badge-matched {
    background: rgba(34, 197, 94, 0.15);
    color: #86efac;
    border-color: rgba(34, 197, 94, 0.3);
}

/* ── Apply Button ──────────────────────────────── */
.apply-btn {
    display: inline-block;
    background: linear-gradient(135deg, #4338ca, #6366f1);
    color: white !important;
    text-decoration: none !important;
    padding: 6px 16px;
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 600;
    margin: 2px 4px;
    transition: all 0.2s ease;
}
.apply-btn:hover {
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
    transform: translateY(-1px);
}
.apply-btn-alt {
    background: linear-gradient(135deg, #1e40af, #3b82f6);
}

/* ── Tabs ──────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] {
    border-radius: 10px 10px 0 0;
    padding: 8px 20px;
    font-weight: 500;
}

/* ── Upload Area ───────────────────────────────── */
[data-testid="stFileUploader"] {
    border: 2px dashed rgba(99, 102, 241, 0.3) !important;
    border-radius: 16px;
    padding: 1rem;
}
[data-testid="stFileUploader"]:hover {
    border-color: rgba(129, 140, 248, 0.5) !important;
}

/* ── Scrollbar ─────────────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0f172a; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #475569; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# Data Loaders (cached)
# ════════════════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def get_analysis():
    return load_latest_analysis()

@st.cache_data(ttl=300)
def get_profile():
    return load_user_profile()

@st.cache_data(ttl=300)
def get_matches():
    return load_job_matches()

@st.cache_data(ttl=300)
def load_jobs_df():
    csv_files = list(DATA_DIR.glob("jobs_*.csv"))
    if csv_files:
        latest = max(csv_files, key=lambda f: f.stat().st_mtime)
        return pd.read_csv(latest)
    return pd.DataFrame()

@st.cache_data(ttl=300)
def load_jobs_list():
    df = load_jobs_df()
    if df.empty:
        return []
    return df.fillna("").to_dict("records")

@st.cache_data(ttl=300)
def extract_skills_from_jobs():
    """Extract skill counts from raw job data."""
    df = load_jobs_df()
    if df.empty or "skills" not in df.columns:
        return {}
    from collections import Counter
    counter = Counter()
    for raw in df["skills"].dropna():
        for skill in str(raw).split(","):
            s = skill.strip().lower()
            if s and len(s) > 1:
                counter[s] += 1
    return dict(counter.most_common(100))

@st.cache_data(ttl=300)
def extract_experience_from_jobs():
    """Extract experience level distribution from raw job data."""
    df = load_jobs_df()
    if df.empty or "experience_level" not in df.columns:
        return {}
    counts = df["experience_level"].dropna().value_counts().to_dict()
    return {str(k): int(v) for k, v in counts.items() if str(k).strip()}


# ════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════
ACCENT = "#818cf8"
COLORS = [
    "#818cf8", "#f472b6", "#34d399", "#fbbf24", "#60a5fa",
    "#a78bfa", "#fb923c", "#2dd4bf", "#f87171", "#38bdf8",
]
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#cbd5e1", family="Inter, sans-serif", size=13),
    margin=dict(l=40, r=30, t=50, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)

def make_apply_links(title: str, company: str) -> str:
    """Generate LinkedIn + Google job search links."""
    q = urllib.parse.quote(f"{title} {company}")
    li_url = f"https://www.linkedin.com/jobs/search/?keywords={q}"
    g_url = f"https://www.google.com/search?q={urllib.parse.quote(f'{title} {company} apply job')}"
    return (
        f'<a class="apply-btn" href="{li_url}" target="_blank">🔗 LinkedIn</a>'
        f'<a class="apply-btn apply-btn-alt" href="{g_url}" target="_blank">🔍 Google</a>'
    )

def render_skill_badges(skills, matched=None):
    matched = set(s.lower() for s in (matched or []))
    html = ""
    for s in skills:
        cls = "skill-badge-matched" if s.lower() in matched else ""
        html += f'<span class="skill-badge {cls}">{s}</span>'
    return html


# ════════════════════════════════════════════════════════════════
# Sidebar
# ════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0 0.5rem 0;">
        <div style="font-size: 2.2rem;">💼</div>
        <div style="font-size: 1.1rem; font-weight: 700; color: #e0e7ff; letter-spacing: -0.02em;">
            Job Analysis
        </div>
        <div style="font-size: 0.75rem; color: #64748b; margin-top: 2px;">
            LinkedIn Market Intelligence
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    page = st.radio(
        "Navigate",
        [
            "🏠 Overview",
            "📊 Skill Trends",
            "🏢 Companies",
            "💰 Salary Predictor",
            "📄 Resume Match",
            "🔮 Forecast",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("""
    <div style="text-align:center; color:#475569; font-size:0.7rem; margin-top:2rem; line-height:1.6;">
        LinkedIn Job Analysis v3.0<br>
        Built with Streamlit + Plotly
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# PAGE: Overview
# ════════════════════════════════════════════════════════════════
def page_overview():
    st.markdown("""
    <div class="hero-banner">
        <h1>💼 Job Market Intelligence</h1>
        <p>Real-time insights from LinkedIn job postings across India</p>
    </div>
    """, unsafe_allow_html=True)

    data = get_analysis()
    if not data:
        st.warning("No analysis data found. Run `python scripts/master_flow.py` first.")
        return

    meta = data.get("metadata", {})
    companies = data.get("top_companies", {})
    locations = data.get("top_locations", {})
    skills_counts = extract_skills_from_jobs()
    total_skills = len(skills_counts)

    # ── KPI Row ──
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Jobs Analyzed", f"{meta.get('total_jobs', 0):,}")
    c2.metric("Unique Companies", f"{companies.get('total_unique', 0):,}")
    c3.metric("Locations Covered", f"{locations.get('total_unique', 0):,}")
    c4.metric("Skills Tracked", f"{total_skills}")

    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

    # ── Charts: 2×2 grid ──
    row1_l, row1_r = st.columns(2)

    titles = data.get("top_titles", {}).get("data", {})
    if titles:
        with row1_l:
            items = dict(list(titles.items())[:10])
            fig = go.Figure(go.Bar(
                x=list(items.values()),
                y=list(items.keys()),
                orientation="h",
                marker=dict(
                    color=list(items.values()),
                    colorscale=[[0, "#312e81"], [1, "#818cf8"]],
                    line=dict(width=0),
                ),
            ))
            fig.update_layout(
                title="🏷️ Top Job Titles",
                yaxis=dict(autorange="reversed"),
                height=400,
                **PLOTLY_LAYOUT,
            )
            st.plotly_chart(fig, use_container_width=True)

    exp = data.get("experience_levels", {}) or extract_experience_from_jobs()
    if exp:
        with row1_r:
            fig = go.Figure(go.Pie(
                labels=list(exp.keys()),
                values=list(exp.values()),
                hole=0.5,
                marker=dict(colors=COLORS),
                textinfo="label+percent",
                textfont=dict(size=12),
            ))
            fig.update_layout(title="🎯 Experience Distribution", height=400, **PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

    row2_l, row2_r = st.columns(2)

    loc_data = locations.get("data", {})
    if loc_data:
        with row2_l:
            items = dict(list(loc_data.items())[:10])
            fig = go.Figure(go.Bar(
                x=list(items.keys()),
                y=list(items.values()),
                marker=dict(
                    color=list(items.values()),
                    colorscale=[[0, "#1e3a5f"], [1, "#38bdf8"]],
                    line=dict(width=0),
                ),
            ))
            fig.update_layout(
                title="📍 Jobs by Location",
                xaxis=dict(tickangle=-40),
                height=400,
                **PLOTLY_LAYOUT,
            )
            st.plotly_chart(fig, use_container_width=True)

    comp_data = companies.get("data", {})
    if comp_data:
        with row2_r:
            items = dict(list(comp_data.items())[:10])
            fig = go.Figure(go.Bar(
                x=list(items.keys()),
                y=list(items.values()),
                marker=dict(
                    color=list(items.values()),
                    colorscale=[[0, "#1a2e05"], [1, "#34d399"]],
                    line=dict(width=0),
                ),
            ))
            fig.update_layout(
                title="🏢 Top Hiring Companies",
                xaxis=dict(tickangle=-40),
                height=400,
                **PLOTLY_LAYOUT,
            )
            st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════════
# PAGE: Skill Trends
# ════════════════════════════════════════════════════════════════
def page_skills():
    st.markdown("""
    <div class="hero-banner">
        <h1>📊 Skill Trends & Analysis</h1>
        <p>Discover in-demand skills and market trends</p>
    </div>
    """, unsafe_allow_html=True)

    data = get_analysis()

    # Get skills from analysis or extract from raw CSV
    skills = {}
    if data:
        skills_data = data.get("skills", {})
        skills = skills_data.get("top_10", {}) if isinstance(skills_data, dict) else {}
        if not skills:
            skills = skills_data.get("data", {}) if isinstance(skills_data, dict) else {}
    if not skills:
        skills = extract_skills_from_jobs()
    if not skills:
        st.info("No skill data available. Run the pipeline to generate data.")
        return

    col1, col2 = st.columns(2)

    with col1:
        top_n = st.slider("Display top N skills", 5, 30, 15, key="skills_n")
        items = dict(list(skills.items())[:top_n])
        fig = go.Figure(go.Bar(
            x=list(items.values()),
            y=list(items.keys()),
            orientation="h",
            marker=dict(
                color=list(items.values()),
                colorscale=[[0, "#312e81"], [0.5, "#6366f1"], [1, "#a78bfa"]],
                line=dict(width=0),
            ),
        ))
        fig.update_layout(
            title=f"🛠️ Top {top_n} In-Demand Skills",
            yaxis=dict(autorange="reversed"),
            height=500,
            **PLOTLY_LAYOUT,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        try:
            from skills_loader import SKILL_CATEGORIES
            cat_counts = {}
            for cat, cat_skills in SKILL_CATEGORIES.items():
                count = sum(skills.get(s, 0) for s in cat_skills)
                if count > 0:
                    cat_counts[cat] = count
            if cat_counts:
                fig = go.Figure(go.Pie(
                    labels=list(cat_counts.keys()),
                    values=list(cat_counts.values()),
                    hole=0.45,
                    marker=dict(colors=COLORS),
                    textinfo="label+percent",
                ))
                fig.update_layout(title="📂 Skills by Category", height=500, **PLOTLY_LAYOUT)
                st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            st.info("Category breakdown unavailable.")

    # ── Skills Table ──
    st.markdown("### 📋 Complete Skills Data")
    df = pd.DataFrame(
        [{"Skill": k, "Mentions": v} for k, v in skills.items()]
    ).sort_values("Mentions", ascending=False).reset_index(drop=True)
    df.index += 1
    df.index.name = "Rank"
    st.dataframe(df, use_container_width=True)


# ════════════════════════════════════════════════════════════════
# PAGE: Companies
# ════════════════════════════════════════════════════════════════
def page_companies():
    st.markdown("""
    <div class="hero-banner">
        <h1>🏢 Company Insights</h1>
        <p>Top hiring companies and market distribution</p>
    </div>
    """, unsafe_allow_html=True)

    data = get_analysis()
    if not data:
        st.warning("No analysis data found.")
        return

    companies = data.get("top_companies", {}).get("data", {})
    if not companies:
        st.info("No company data available.")
        return

    top_n = st.slider("Show top N companies", 5, 30, 15, key="comp_n")

    col1, col2 = st.columns([2, 1])

    with col1:
        items = dict(list(companies.items())[:top_n])
        fig = go.Figure(go.Bar(
            x=list(items.keys()),
            y=list(items.values()),
            marker=dict(
                color=list(items.values()),
                colorscale=[[0, "#064e3b"], [1, "#34d399"]],
                line=dict(width=0),
            ),
        ))
        fig.update_layout(
            title=f"Top {top_n} Companies by Job Postings",
            xaxis=dict(tickangle=-45),
            height=450,
            **PLOTLY_LAYOUT,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        top5 = dict(list(companies.items())[:5])
        fig = go.Figure(go.Pie(
            labels=list(top5.keys()),
            values=list(top5.values()),
            hole=0.5,
            marker=dict(colors=COLORS[:5]),
        ))
        fig.update_layout(title="Top 5 Share", height=450, **PLOTLY_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

    df = pd.DataFrame(
        [{"Company": k, "Job Postings": v} for k, v in companies.items()]
    ).sort_values("Job Postings", ascending=False).reset_index(drop=True)
    df.index += 1
    df.index.name = "Rank"
    st.dataframe(df, use_container_width=True)


# ════════════════════════════════════════════════════════════════
# PAGE: Salary Predictor
# ════════════════════════════════════════════════════════════════
def page_salary():
    st.markdown("""
    <div class="hero-banner">
        <h1>💰 Salary Predictor</h1>
        <p>ML-backed salary estimates powered by Gradient Boosting</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("Job Title", "Data Scientist", key="sal_title")
        location = st.text_input("Location", "Bangalore", key="sal_loc")
    with col2:
        skills_in = st.text_input("Skills (comma-separated)", "python, machine learning, sql", key="sal_skills")
        company_size = st.selectbox("Company Size", ["Enterprise", "Large", "Medium", "Small", "Startup"], key="sal_size")

    if st.button("🔮 Predict Salary", use_container_width=True, type="primary"):
        try:
            from salary_predictor import SalaryPredictor
            predictor = SalaryPredictor()
            result = predictor.predict({
                "title": title, "location": location,
                "skills": skills_in, "company_size": company_size,
            })

            st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            c1.metric("Minimum", f"₹{result['min']:.1f} LPA")
            c2.metric("Expected", f"₹{result['avg']:.1f} LPA")
            c3.metric("Maximum", f"₹{result['max']:.1f} LPA")

            c4, c5 = st.columns(2)
            c4.metric("Confidence", result.get("confidence", "N/A"))
            c5.metric("Method", result.get("method", "Heuristic"))

            # Range indicator
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=[result["min"]], y=["Range"], orientation="h", name="Min",
                marker=dict(color="#f87171"), text=[f"₹{result['min']:.1f}L"], textposition="inside",
            ))
            fig.add_trace(go.Bar(
                x=[result["avg"] - result["min"]], y=["Range"], orientation="h", name="Avg",
                marker=dict(color="#818cf8"), text=[f"₹{result['avg']:.1f}L"], textposition="inside",
            ))
            fig.add_trace(go.Bar(
                x=[result["max"] - result["avg"]], y=["Range"], orientation="h", name="Max",
                marker=dict(color="#34d399"), text=[f"₹{result['max']:.1f}L"], textposition="inside",
            ))
            fig.update_layout(barmode="stack", showlegend=False, height=100, **PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Prediction failed: {e}")


# ════════════════════════════════════════════════════════════════
# PAGE: Resume Match (with PDF Upload)
# ════════════════════════════════════════════════════════════════
def page_resume():
    st.markdown("""
    <div class="hero-banner">
        <h1>📄 Resume Match</h1>
        <p>Upload your PDF resume and instantly find matching jobs</p>
    </div>
    """, unsafe_allow_html=True)

    # ── PDF Upload Section ──
    uploaded = st.file_uploader(
        "📤 Upload your resume (PDF)", type=["pdf"],
        help="We'll extract your skills and match you to jobs instantly",
    )

    profile_data = None

    if uploaded is not None:
        # Parse the uploaded PDF
        try:
            import pdfplumber
            from resume_parser import parse_resume_text

            with pdfplumber.open(io.BytesIO(uploaded.read())) as pdf:
                text = "\n".join(
                    page.extract_text() or "" for page in pdf.pages
                )

            if text.strip():
                profile_data = parse_resume_text(text)
                st.success(f"✅ Resume parsed! Extracted {len(text):,} characters from {uploaded.name}")
            else:
                st.error("Could not extract text from this PDF. Try a text-based PDF.")
        except ImportError:
            st.error("pdfplumber not installed. Run: `pip install pdfplumber`")
        except Exception as e:
            st.error(f"Error parsing PDF: {e}")

    # ── Show parsed profile ──
    if profile_data:
        st.markdown("### 👤 Extracted Profile")
        c1, c2, c3 = st.columns(3)
        c1.metric("Detected Title", profile_data.get("title") or "Not detected")
        c2.metric("Experience", f"{profile_data.get('experience_years', 0)} years")
        c3.metric("Skills Found", f"{len(profile_data.get('skills', []))}")

        skills = profile_data.get("skills", [])
        if skills:
            st.markdown(render_skill_badges(skills), unsafe_allow_html=True)

        locations = profile_data.get("preferred_locations", [])
        if locations:
            st.markdown(f"📍 **Locations:** {', '.join(locations)}")

        # ── Live Job Matching ──
        st.markdown("---")
        st.markdown("### 🎯 Your Job Matches")

        jobs = load_jobs_list()
        if not jobs:
            st.warning("No job data found. Run `python scripts/master_flow.py` first.")
            return

        # Run matching
        from resume_matcher import ResumeMatcher, UserProfile
        user = UserProfile.from_dict(profile_data)
        matcher = ResumeMatcher(user)

        scored = []
        for job in jobs:
            score, breakdown = matcher.calculate_match_score(job)
            if score >= 30:
                scored.append((score, breakdown, job))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_matches = scored[:15]

        if not top_matches:
            st.info("No strong matches found. Try uploading a different resume.")
            return

        st.markdown(f"**Found {len(scored)} matches** (showing top {len(top_matches)})")

        for i, (score, breakdown, job) in enumerate(top_matches, 1):
            color = "#34d399" if score >= 70 else "#fbbf24" if score >= 50 else "#f87171"
            matched_skills = breakdown.get("skills", {}).get("matched", [])
            title = job.get("title", "N/A")
            company = job.get("company", "N/A")
            location = job.get("location", "N/A")
            apply_html = make_apply_links(title, company)

            job_skills_raw = str(job.get("skills", ""))
            if job_skills_raw:
                all_job_skills = [s.strip() for s in job_skills_raw.split(",") if s.strip()][:8]
            else:
                all_job_skills = []

            st.markdown(f"""
            <div class="match-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div style="flex:1;">
                        <div class="match-title">{i}. {title}</div>
                        <div class="match-company">{company}</div>
                        <div class="match-meta">📍 {location}</div>
                        <div style="margin-top:8px;">
                            {render_skill_badges(all_job_skills, matched_skills)}
                        </div>
                        <div style="margin-top:8px;">
                            {apply_html}
                        </div>
                    </div>
                    <div style="min-width:70px; padding-left:1rem;">
                        <div class="match-score" style="color:{color};">{score:.0f}%</div>
                        <div class="match-score-label">match</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    else:
        # ── Fallback: show saved profile / matches ──
        profile = get_profile()
        matches = get_matches()

        if profile and profile.get("skills"):
            st.markdown("### 👤 Saved Profile")
            c1, c2, c3 = st.columns(3)
            c1.metric("Name", profile.get("name") or "N/A")
            c2.metric("Title", profile.get("title") or "N/A")
            c3.metric("Experience", f"{profile.get('experience_years', 0)} years")

            skills = profile.get("skills", [])
            if skills:
                st.markdown(render_skill_badges(skills), unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="glass-panel" style="text-align:center; padding:3rem;">
                <div style="font-size:3rem; margin-bottom:1rem;">📤</div>
                <div style="color:#e2e8f0; font-size:1.1rem; font-weight:600;">Upload Your Resume</div>
                <div style="color:#64748b; font-size:0.9rem; margin-top:0.5rem;">
                    Drop a PDF above to instantly discover matching jobs<br>
                    Or create a profile manually: <code>python scripts/resume_matcher.py --profile</code>
                </div>
            </div>
            """, unsafe_allow_html=True)

        if matches:
            st.markdown("---")
            st.markdown(f"### 🎯 Saved Matches ({len(matches)})")
            for i, match in enumerate(matches, 1):
                score = match.get("score", 0)
                color = "#34d399" if score >= 70 else "#fbbf24" if score >= 50 else "#f87171"
                title = match.get("title", "N/A")
                company = match.get("company", "N/A")
                apply_html = make_apply_links(title, company)

                st.markdown(f"""
                <div class="match-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div class="match-title">{i}. {title}</div>
                            <div class="match-company">{company}</div>
                            <div class="match-meta">📍 {match.get('location', 'N/A')}</div>
                            <div style="margin-top:6px;">{apply_html}</div>
                        </div>
                        <div style="min-width:70px;">
                            <div class="match-score" style="color:{color};">{score:.0f}%</div>
                            <div class="match-score-label">match</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# PAGE: Forecast
# ════════════════════════════════════════════════════════════════
def page_forecast():
    st.markdown("""
    <div class="hero-banner">
        <h1>🔮 Skill Demand Forecast</h1>
        <p>90-day predictions based on historical trend analysis</p>
    </div>
    """, unsafe_allow_html=True)

    try:
        from trend_tracker import TrendTracker
        tracker = TrendTracker()
        forecasts = tracker.forecast_skills(horizon_days=90)
        rankings = tracker.get_growth_rankings()
    except Exception as e:
        st.error(f"Could not load forecast data: {e}")
        return

    if not forecasts:
        st.info("Not enough historical data for forecasting. Run the pipeline a few times to build trend history.")
        return

    # ── Growth Summary Cards ──
    rising = rankings.get("rising", [])
    stable = rankings.get("stable", [])
    declining = rankings.get("declining", [])

    c1, c2, c3 = st.columns(3)
    c1.metric("🔥 Rising Skills", len(rising))
    c2.metric("→ Stable Skills", len(stable))
    c3.metric("📉 Declining Skills", len(declining))

    st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)

    # ── Forecast Chart ──
    df = pd.DataFrame(forecasts[:15])
    if not df.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df["skill"].str.upper(),
            y=df["current_count"],
            name="Current",
            marker=dict(color="#6366f1", line=dict(width=0)),
        ))
        fig.add_trace(go.Bar(
            x=df["skill"].str.upper(),
            y=df["predicted_count"],
            name="Predicted (90d)",
            marker=dict(color="#34d399", opacity=0.7, line=dict(width=0)),
        ))
        fig.update_layout(
            title="Current vs Predicted Skill Demand",
            barmode="group",
            xaxis=dict(tickangle=-45),
            height=450,
            **PLOTLY_LAYOUT,
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Growth Rankings ──
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 🔥 Rising")
        for s in rising[:8]:
            f_data = next((f for f in forecasts if f["skill"] == s), {})
            rate = f_data.get("growth_rate", 0)
            st.markdown(f"<span class='skill-badge' style='background:rgba(34,197,94,0.2);color:#86efac;border-color:rgba(34,197,94,0.3);'>"
                        f"↑ {s.upper()} (+{rate:.2f}/day)</span>", unsafe_allow_html=True)

    with col2:
        st.markdown("#### → Stable")
        for s in stable[:8]:
            st.markdown(f"<span class='skill-badge'>{s.upper()}</span>", unsafe_allow_html=True)

    with col3:
        st.markdown("#### 📉 Declining")
        for s in declining[:8]:
            f_data = next((f for f in forecasts if f["skill"] == s), {})
            rate = f_data.get("growth_rate", 0)
            st.markdown(f"<span class='skill-badge' style='background:rgba(248,113,113,0.2);color:#fca5a5;border-color:rgba(248,113,113,0.3);'>"
                        f"↓ {s.upper()} ({rate:.2f}/day)</span>", unsafe_allow_html=True)

    # ── Full Forecast Table ──
    st.markdown("### 📋 Full Forecast Data")
    if not pd.DataFrame(forecasts).empty:
        tbl = pd.DataFrame(forecasts)
        tbl.columns = ["Skill", "Current", "Predicted", "Growth Rate", "Confidence (R²)", "Data Points"]
        tbl["Skill"] = tbl["Skill"].str.upper()
        tbl.index += 1
        st.dataframe(tbl, use_container_width=True)


# ════════════════════════════════════════════════════════════════
# Router
# ════════════════════════════════════════════════════════════════
if "Overview" in page:
    page_overview()
elif "Skill" in page:
    page_skills()
elif "Companies" in page:
    page_companies()
elif "Salary" in page:
    page_salary()
elif "Resume" in page:
    page_resume()
elif "Forecast" in page:
    page_forecast()
