"""
Job Data Visualization Module
=============================
Visualize collected job data with interactive charts and dashboards.

Usage:
    python visualize_data.py
    python visualize_data.py --file ../data/raw/jobs_india_20260114_204358.csv
"""

import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import argparse
from datetime import datetime
import numpy as np
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# Set style for all plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Custom color palettes
CITY_COLORS = {
    'Bangalore': '#FF6B6B',
    'Mumbai': '#4ECDC4',
    'Pune': '#45B7D1',
    'Hyderabad': '#96CEB4',
    'Delhi': '#FFEAA7',
    'Chennai': '#DDA0DD',
    'Kolkata': '#98D8C8',
    'Noida': '#F7DC6F',
    'Gurgaon': '#BB8FCE',
    'Ahmedabad': '#85C1E9',
}

SKILL_COLORS = sns.color_palette("husl", 20)


class JobDataVisualizer:
    """Visualize job market data with various chart types."""
    
    def __init__(self, data_path: str = None):
        """
        Initialize visualizer with data.
        
        Args:
            data_path: Path to CSV or JSON data file
        """
        self.output_dir = Path("../outputs/visualizations")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if data_path:
            self.load_data(data_path)
        else:
            self.df = None
    
    def load_data(self, data_path: str):
        """Load data from file."""
        path = Path(data_path)
        
        if path.suffix == '.csv':
            self.df = pd.read_csv(path)
            # Convert skills string back to list if needed
            if 'skills' in self.df.columns and isinstance(self.df['skills'].iloc[0], str):
                self.df['skills'] = self.df['skills'].apply(
                    lambda x: x.split(',') if pd.notna(x) and x else []
                )
        elif path.suffix == '.json':
            self.df = pd.read_json(path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
        
        print(f"✅ Loaded {len(self.df)} jobs from {path.name}")
        return self.df
    
    def find_latest_data_file(self) -> Path:
        """Find the most recent data file."""
        data_dir = Path("../data/raw")
        
        # Look for India-specific files first
        india_files = list(data_dir.glob("jobs_india_*.csv"))
        if india_files:
            return max(india_files, key=lambda x: x.stat().st_mtime)
        
        # Fall back to any jobs file
        all_files = list(data_dir.glob("jobs_*.csv"))
        if all_files:
            return max(all_files, key=lambda x: x.stat().st_mtime)
        
        raise FileNotFoundError("No data files found in ../data/raw/")
    
    def plot_jobs_by_city(self, save: bool = True, show: bool = True):
        """Create bar chart of jobs by city."""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        city_counts = self.df['city'].value_counts()
        colors = [CITY_COLORS.get(city, '#95A5A6') for city in city_counts.index]
        
        bars = ax.bar(city_counts.index, city_counts.values, color=colors, edgecolor='white', linewidth=1.5)
        
        # Add value labels on bars
        for bar, value in zip(bars, city_counts.values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
                   f'{value}', ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        ax.set_xlabel('City', fontsize=12, fontweight='bold')
        ax.set_ylabel('Number of Jobs', fontsize=12, fontweight='bold')
        ax.set_title('🏙️ Job Openings by City', fontsize=16, fontweight='bold', pad=20)
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        if save:
            plt.savefig(self.output_dir / 'jobs_by_city.png', dpi=150, bbox_inches='tight')
            print(f"📊 Saved: jobs_by_city.png")
        
        if show:
            plt.show()
        plt.close()
    
    def plot_jobs_by_title(self, top_n: int = 15, save: bool = True, show: bool = True):
        """Create horizontal bar chart of jobs by title."""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        title_counts = self.df['title'].value_counts().head(top_n)
        
        colors = sns.color_palette("viridis", len(title_counts))
        
        bars = ax.barh(range(len(title_counts)), title_counts.values, color=colors)
        ax.set_yticks(range(len(title_counts)))
        ax.set_yticklabels(title_counts.index)
        
        # Add value labels
        for i, (bar, value) in enumerate(zip(bars, title_counts.values)):
            ax.text(value + 2, i, f'{value}', va='center', fontsize=10, fontweight='bold')
        
        ax.set_xlabel('Number of Jobs', fontsize=12, fontweight='bold')
        ax.set_title(f'💼 Top {top_n} Job Titles', fontsize=16, fontweight='bold', pad=20)
        ax.invert_yaxis()
        
        plt.tight_layout()
        
        if save:
            plt.savefig(self.output_dir / 'jobs_by_title.png', dpi=150, bbox_inches='tight')
            print(f"📊 Saved: jobs_by_title.png")
        
        if show:
            plt.show()
        plt.close()
    
    def plot_top_companies(self, top_n: int = 15, save: bool = True, show: bool = True):
        """Create bar chart of top hiring companies."""
        fig, ax = plt.subplots(figsize=(14, 8))
        
        company_counts = self.df['company'].value_counts().head(top_n)
        
        colors = sns.color_palette("rocket", len(company_counts))
        
        bars = ax.barh(range(len(company_counts)), company_counts.values, color=colors)
        ax.set_yticks(range(len(company_counts)))
        ax.set_yticklabels(company_counts.index)
        
        # Add value labels
        for i, (bar, value) in enumerate(zip(bars, company_counts.values)):
            ax.text(value + 0.5, i, f'{value}', va='center', fontsize=10, fontweight='bold')
        
        ax.set_xlabel('Number of Job Openings', fontsize=12, fontweight='bold')
        ax.set_title(f'🏢 Top {top_n} Hiring Companies', fontsize=16, fontweight='bold', pad=20)
        ax.invert_yaxis()
        
        plt.tight_layout()
        
        if save:
            plt.savefig(self.output_dir / 'top_companies.png', dpi=150, bbox_inches='tight')
            print(f"📊 Saved: top_companies.png")
        
        if show:
            plt.show()
        plt.close()
    
    def plot_skills_demand(self, top_n: int = 20, save: bool = True, show: bool = True):
        """Create bar chart of most in-demand skills."""
        # Extract all skills
        all_skills = []
        for skills in self.df['skills']:
            if isinstance(skills, list):
                all_skills.extend(skills)
            elif isinstance(skills, str) and skills:
                all_skills.extend(skills.split(','))
        
        skill_counts = Counter(all_skills)
        top_skills = dict(skill_counts.most_common(top_n))
        
        fig, ax = plt.subplots(figsize=(14, 10))
        
        colors = sns.color_palette("mako", len(top_skills))
        
        bars = ax.barh(list(top_skills.keys()), list(top_skills.values()), color=colors)
        
        # Add value labels
        for bar, value in zip(bars, top_skills.values()):
            ax.text(value + 2, bar.get_y() + bar.get_height()/2, 
                   f'{value}', va='center', fontsize=10, fontweight='bold')
        
        ax.set_xlabel('Demand (Number of Job Listings)', fontsize=12, fontweight='bold')
        ax.set_title(f'🔧 Top {top_n} In-Demand Skills', fontsize=16, fontweight='bold', pad=20)
        ax.invert_yaxis()
        
        plt.tight_layout()
        
        if save:
            plt.savefig(self.output_dir / 'skills_demand.png', dpi=150, bbox_inches='tight')
            print(f"📊 Saved: skills_demand.png")
        
        if show:
            plt.show()
        plt.close()
    
    def plot_skills_by_city(self, top_n_skills: int = 10, save: bool = True, show: bool = True):
        """Create heatmap of skills demand by city."""
        # Get top skills overall
        all_skills = []
        for skills in self.df['skills']:
            if isinstance(skills, list):
                all_skills.extend(skills)
        
        top_skills = [skill for skill, _ in Counter(all_skills).most_common(top_n_skills)]
        
        # Create skill-city matrix
        cities = self.df['city'].unique()
        skill_city_matrix = pd.DataFrame(0, index=top_skills, columns=cities)
        
        for _, row in self.df.iterrows():
            city = row['city']
            skills = row['skills'] if isinstance(row['skills'], list) else []
            for skill in skills:
                if skill in top_skills:
                    skill_city_matrix.loc[skill, city] += 1
        
        fig, ax = plt.subplots(figsize=(12, 10))
        
        sns.heatmap(skill_city_matrix, annot=True, fmt='d', cmap='YlOrRd',
                   linewidths=0.5, ax=ax, cbar_kws={'label': 'Number of Jobs'})
        
        ax.set_title('🗺️ Skills Demand Heatmap by City', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('City', fontsize=12, fontweight='bold')
        ax.set_ylabel('Skill', fontsize=12, fontweight='bold')
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        if save:
            plt.savefig(self.output_dir / 'skills_by_city_heatmap.png', dpi=150, bbox_inches='tight')
            print(f"📊 Saved: skills_by_city_heatmap.png")
        
        if show:
            plt.show()
        plt.close()
    
    def plot_job_titles_by_city(self, save: bool = True, show: bool = True):
        """Create grouped bar chart of job titles by city."""
        # Get top job titles
        top_titles = self.df['title'].value_counts().head(8).index.tolist()
        
        # Filter data
        df_filtered = self.df[self.df['title'].isin(top_titles)]
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Create pivot table
        pivot = df_filtered.groupby(['city', 'title']).size().unstack(fill_value=0)
        
        pivot.plot(kind='bar', ax=ax, width=0.8, colormap='tab20')
        
        ax.set_xlabel('City', fontsize=12, fontweight='bold')
        ax.set_ylabel('Number of Jobs', fontsize=12, fontweight='bold')
        ax.set_title('📊 Job Titles Distribution by City', fontsize=16, fontweight='bold', pad=20)
        ax.legend(title='Job Title', bbox_to_anchor=(1.02, 1), loc='upper left')
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        if save:
            plt.savefig(self.output_dir / 'job_titles_by_city.png', dpi=150, bbox_inches='tight')
            print(f"📊 Saved: job_titles_by_city.png")
        
        if show:
            plt.show()
        plt.close()
    
    def plot_city_pie_chart(self, save: bool = True, show: bool = True):
        """Create pie chart of job distribution by city."""
        fig, ax = plt.subplots(figsize=(10, 10))
        
        city_counts = self.df['city'].value_counts()
        colors = [CITY_COLORS.get(city, '#95A5A6') for city in city_counts.index]
        
        wedges, texts, autotexts = ax.pie(
            city_counts.values,
            labels=city_counts.index,
            autopct='%1.1f%%',
            colors=colors,
            explode=[0.05] * len(city_counts),
            shadow=True,
            startangle=90
        )
        
        # Style the text
        for autotext in autotexts:
            autotext.set_fontsize(11)
            autotext.set_fontweight('bold')
        
        ax.set_title('🥧 Job Distribution by City', fontsize=16, fontweight='bold', pad=20)
        
        plt.tight_layout()
        
        if save:
            plt.savefig(self.output_dir / 'city_distribution_pie.png', dpi=150, bbox_inches='tight')
            print(f"📊 Saved: city_distribution_pie.png")
        
        if show:
            plt.show()
        plt.close()
    
    def plot_skills_wordcloud(self, save: bool = True, show: bool = True):
        """Create word cloud of skills."""
        try:
            from wordcloud import WordCloud
        except ImportError:
            print("⚠️ wordcloud not installed. Run: pip install wordcloud")
            return
        
        # Extract all skills
        all_skills = []
        for skills in self.df['skills']:
            if isinstance(skills, list):
                all_skills.extend(skills)
        
        skill_text = ' '.join(all_skills)
        
        wordcloud = WordCloud(
            width=1200,
            height=600,
            background_color='white',
            colormap='viridis',
            max_words=100,
            relative_scaling=0.5,
            min_font_size=10
        ).generate(skill_text)
        
        fig, ax = plt.subplots(figsize=(15, 8))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        ax.set_title('☁️ Skills Word Cloud', fontsize=16, fontweight='bold', pad=20)
        
        plt.tight_layout()
        
        if save:
            plt.savefig(self.output_dir / 'skills_wordcloud.png', dpi=150, bbox_inches='tight')
            print(f"📊 Saved: skills_wordcloud.png")
        
        if show:
            plt.show()
        plt.close()
    
    def create_summary_dashboard(self, save: bool = True, show: bool = True):
        """Create a comprehensive summary dashboard."""
        fig = plt.figure(figsize=(20, 16))
        
        # Create grid
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. Jobs by City (top left)
        ax1 = fig.add_subplot(gs[0, 0])
        city_counts = self.df['city'].value_counts()
        colors = [CITY_COLORS.get(city, '#95A5A6') for city in city_counts.index]
        ax1.bar(city_counts.index, city_counts.values, color=colors)
        ax1.set_title('🏙️ Jobs by City', fontweight='bold')
        ax1.tick_params(axis='x', rotation=45)
        
        # 2. Top Job Titles (top middle)
        ax2 = fig.add_subplot(gs[0, 1])
        title_counts = self.df['title'].value_counts().head(8)
        ax2.barh(title_counts.index, title_counts.values, color=sns.color_palette("viridis", 8))
        ax2.set_title('💼 Top Job Titles', fontweight='bold')
        ax2.invert_yaxis()
        
        # 3. Top Companies (top right)
        ax3 = fig.add_subplot(gs[0, 2])
        company_counts = self.df['company'].value_counts().head(8)
        ax3.barh(company_counts.index, company_counts.values, color=sns.color_palette("rocket", 8))
        ax3.set_title('🏢 Top Companies', fontweight='bold')
        ax3.invert_yaxis()
        
        # 4. City Distribution Pie (middle left)
        ax4 = fig.add_subplot(gs[1, 0])
        colors = [CITY_COLORS.get(city, '#95A5A6') for city in city_counts.index]
        ax4.pie(city_counts.values, labels=city_counts.index, autopct='%1.1f%%', colors=colors)
        ax4.set_title('🥧 City Distribution', fontweight='bold')
        
        # 5. Top Skills (middle center + right)
        ax5 = fig.add_subplot(gs[1, 1:])
        all_skills = []
        for skills in self.df['skills']:
            if isinstance(skills, list):
                all_skills.extend(skills)
        skill_counts = Counter(all_skills).most_common(15)
        skills, counts = zip(*skill_counts)
        ax5.barh(skills, counts, color=sns.color_palette("mako", 15))
        ax5.set_title('🔧 Top 15 In-Demand Skills', fontweight='bold')
        ax5.invert_yaxis()
        
        # 6. Skills Heatmap by City (bottom)
        ax6 = fig.add_subplot(gs[2, :])
        top_skills = [s for s, _ in Counter(all_skills).most_common(10)]
        cities = self.df['city'].unique()
        skill_city_matrix = pd.DataFrame(0, index=top_skills, columns=cities)
        for _, row in self.df.iterrows():
            city = row['city']
            skills = row['skills'] if isinstance(row['skills'], list) else []
            for skill in skills:
                if skill in top_skills:
                    skill_city_matrix.loc[skill, city] += 1
        sns.heatmap(skill_city_matrix, annot=True, fmt='d', cmap='YlOrRd', ax=ax6)
        ax6.set_title('🗺️ Skills Demand by City', fontweight='bold')
        
        # Main title
        fig.suptitle(f'📈 Job Market Analysis Dashboard\n{len(self.df)} Jobs | {self.df["city"].nunique()} Cities | {datetime.now().strftime("%Y-%m-%d")}',
                    fontsize=18, fontweight='bold', y=0.98)
        
        plt.tight_layout()
        
        if save:
            plt.savefig(self.output_dir / 'summary_dashboard.png', dpi=150, bbox_inches='tight')
            print(f"📊 Saved: summary_dashboard.png")
        
        if show:
            plt.show()
        plt.close()
    
    def generate_all_visualizations(self, show: bool = False):
        """Generate all visualization charts."""
        print("\n" + "="*60)
        print("📊 Generating All Visualizations...")
        print("="*60 + "\n")
        
        self.plot_jobs_by_city(save=True, show=show)
        self.plot_jobs_by_title(save=True, show=show)
        self.plot_top_companies(save=True, show=show)
        self.plot_skills_demand(save=True, show=show)
        self.plot_skills_by_city(save=True, show=show)
        self.plot_job_titles_by_city(save=True, show=show)
        self.plot_city_pie_chart(save=True, show=show)
        self.plot_skills_wordcloud(save=True, show=show)
        self.create_summary_dashboard(save=True, show=show)
        
        print("\n" + "="*60)
        print(f"✅ All visualizations saved to: {self.output_dir.absolute()}")
        print("="*60)
    
    def print_statistics(self):
        """Print summary statistics."""
        print("\n" + "="*60)
        print("📈 DATA SUMMARY STATISTICS")
        print("="*60)
        
        print(f"\n📋 Total Jobs: {len(self.df):,}")
        print(f"🏙️ Cities: {self.df['city'].nunique()}")
        print(f"🏢 Companies: {self.df['company'].nunique()}")
        print(f"💼 Unique Job Titles: {self.df['title'].nunique()}")
        
        # Skills count
        all_skills = []
        for skills in self.df['skills']:
            if isinstance(skills, list):
                all_skills.extend(skills)
        print(f"🔧 Unique Skills: {len(set(all_skills))}")
        
        print(f"\n📍 Jobs per City:")
        for city, count in self.df['city'].value_counts().items():
            pct = count / len(self.df) * 100
            print(f"   {city}: {count} ({pct:.1f}%)")
        
        print(f"\n💼 Top 10 Job Titles:")
        for title, count in self.df['title'].value_counts().head(10).items():
            print(f"   {title}: {count}")
        
        print(f"\n🔧 Top 10 Skills:")
        skill_counts = Counter(all_skills).most_common(10)
        for skill, count in skill_counts:
            print(f"   {skill}: {count}")
        
        print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(description='Visualize job data')
    parser.add_argument('--file', help='Path to data file (CSV or JSON)')
    parser.add_argument('--show', action='store_true', help='Show plots interactively')
    parser.add_argument('--stats', action='store_true', help='Print statistics only')
    
    args = parser.parse_args()
    
    visualizer = JobDataVisualizer()
    
    # Load data
    if args.file:
        visualizer.load_data(args.file)
    else:
        try:
            latest_file = visualizer.find_latest_data_file()
            print(f"📁 Using latest file: {latest_file}")
            visualizer.load_data(str(latest_file))
        except FileNotFoundError as e:
            print(f"❌ {e}")
            return
    
    # Print statistics
    visualizer.print_statistics()
    
    if not args.stats:
        # Generate all visualizations
        visualizer.generate_all_visualizations(show=args.show)


if __name__ == "__main__":
    main()
