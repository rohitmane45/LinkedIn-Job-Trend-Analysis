"""
Job Data Analyzer
=================
This script performs comprehensive analysis on cleaned job data,
including skill demand analysis, city-based trends, and generates visualizations.

Author: LinkedIn Job Analysis Project
Date: January 2026
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import Counter
from pathlib import Path
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set style for matplotlib
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")


class JobAnalyzer:
    """
    A class to analyze job posting data and generate insights.
    """
    
    def __init__(self, data_dir: str = "../data/processed", output_dir: str = "../visualizations"):
        """
        Initialize the analyzer.
        
        Args:
            data_dir: Directory containing cleaned data
            output_dir: Directory to save visualizations
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.df = None
        self.analysis_results = {}
        
    def load_data(self, filepath: str = None) -> pd.DataFrame:
        """
        Load cleaned job data.
        
        Args:
            filepath: Path to data file (optional)
            
        Returns:
            DataFrame with job data
        """
        if filepath:
            path = Path(filepath)
        else:
            # Find latest cleaned data file
            json_files = list(self.data_dir.glob("jobs_cleaned_*.json"))
            if not json_files:
                csv_files = list(self.data_dir.glob("jobs_cleaned_*.csv"))
                if not csv_files:
                    raise FileNotFoundError("No cleaned data files found. Run cleaner.py first.")
                path = max(csv_files, key=lambda x: x.stat().st_mtime)
            else:
                path = max(json_files, key=lambda x: x.stat().st_mtime)
        
        logger.info(f"Loading data from: {path}")
        
        if path.suffix == '.json':
            self.df = pd.read_json(path)
        else:
            self.df = pd.read_csv(path)
            # Parse skills column if it's a string
            if 'skills_normalized' in self.df.columns:
                self.df['skills_normalized'] = self.df['skills_normalized'].apply(
                    lambda x: x.split(',') if isinstance(x, str) else x
                )
        
        logger.info(f"Loaded {len(self.df)} job records")
        return self.df
    
    # ==================== SKILL ANALYSIS ====================
    
    def analyze_skill_demand(self) -> pd.DataFrame:
        """
        Analyze overall skill demand across all jobs.
        
        Returns:
            DataFrame with skill counts and percentages
        """
        logger.info("Analyzing overall skill demand...")
        
        # Flatten all skills
        all_skills = []
        for skills in self.df['skills_normalized']:
            if isinstance(skills, list):
                all_skills.extend(skills)
        
        # Count skills
        skill_counts = Counter(all_skills)
        
        # Create DataFrame
        skill_df = pd.DataFrame(
            skill_counts.most_common(),
            columns=['skill', 'count']
        )
        skill_df['percentage'] = (skill_df['count'] / len(self.df) * 100).round(2)
        
        self.analysis_results['skill_demand'] = skill_df
        logger.info(f"Found {len(skill_df)} unique skills")
        
        return skill_df
    
    def analyze_skills_by_city(self, top_n_skills: int = 15, top_n_cities: int = 10) -> pd.DataFrame:
        """
        Analyze skill demand by city.
        
        Args:
            top_n_skills: Number of top skills to include
            top_n_cities: Number of top cities to include
            
        Returns:
            DataFrame with skill counts per city
        """
        logger.info("Analyzing skills by city...")
        
        # Get top cities
        city_col = 'city_standardized' if 'city_standardized' in self.df.columns else 'city'
        top_cities = self.df[city_col].value_counts().head(top_n_cities).index.tolist()
        
        # Get top skills
        skill_demand = self.analyze_skill_demand()
        top_skills = skill_demand.head(top_n_skills)['skill'].tolist()
        
        # Create skill-city matrix
        skill_city_data = []
        
        for city in top_cities:
            city_jobs = self.df[self.df[city_col] == city]
            city_skills = []
            for skills in city_jobs['skills_normalized']:
                if isinstance(skills, list):
                    city_skills.extend(skills)
            
            skill_counts = Counter(city_skills)
            
            for skill in top_skills:
                skill_city_data.append({
                    'city': city,
                    'skill': skill,
                    'count': skill_counts.get(skill, 0),
                    'percentage': skill_counts.get(skill, 0) / len(city_jobs) * 100 if len(city_jobs) > 0 else 0
                })
        
        skill_city_df = pd.DataFrame(skill_city_data)
        self.analysis_results['skills_by_city'] = skill_city_df
        
        return skill_city_df
    
    def analyze_skills_by_role(self, top_n_skills: int = 15) -> pd.DataFrame:
        """
        Analyze skill demand by role category.
        
        Args:
            top_n_skills: Number of top skills to include
            
        Returns:
            DataFrame with skill counts per role
        """
        logger.info("Analyzing skills by role...")
        
        # Get top skills
        skill_demand = self.analyze_skill_demand()
        top_skills = skill_demand.head(top_n_skills)['skill'].tolist()
        
        # Get role categories
        role_col = 'role_category' if 'role_category' in self.df.columns else 'title_standardized'
        roles = self.df[role_col].unique()
        
        # Create skill-role matrix
        skill_role_data = []
        
        for role in roles:
            role_jobs = self.df[self.df[role_col] == role]
            role_skills = []
            for skills in role_jobs['skills_normalized']:
                if isinstance(skills, list):
                    role_skills.extend(skills)
            
            skill_counts = Counter(role_skills)
            
            for skill in top_skills:
                skill_role_data.append({
                    'role': role,
                    'skill': skill,
                    'count': skill_counts.get(skill, 0),
                    'percentage': skill_counts.get(skill, 0) / len(role_jobs) * 100 if len(role_jobs) > 0 else 0
                })
        
        skill_role_df = pd.DataFrame(skill_role_data)
        self.analysis_results['skills_by_role'] = skill_role_df
        
        return skill_role_df
    
    # ==================== CITY ANALYSIS ====================
    
    def analyze_jobs_by_city(self) -> pd.DataFrame:
        """
        Analyze job distribution by city.
        
        Returns:
            DataFrame with job counts per city
        """
        logger.info("Analyzing jobs by city...")
        
        city_col = 'city_standardized' if 'city_standardized' in self.df.columns else 'city'
        
        city_counts = self.df[city_col].value_counts().reset_index()
        city_counts.columns = ['city', 'job_count']
        city_counts['percentage'] = (city_counts['job_count'] / len(self.df) * 100).round(2)
        
        self.analysis_results['jobs_by_city'] = city_counts
        
        return city_counts
    
    def analyze_roles_by_city(self) -> pd.DataFrame:
        """
        Analyze role distribution by city.
        
        Returns:
            DataFrame with role counts per city
        """
        logger.info("Analyzing roles by city...")
        
        city_col = 'city_standardized' if 'city_standardized' in self.df.columns else 'city'
        role_col = 'role_category' if 'role_category' in self.df.columns else 'title_standardized'
        
        role_city = self.df.groupby([city_col, role_col]).size().reset_index(name='count')
        role_city_pivot = role_city.pivot(index=city_col, columns=role_col, values='count').fillna(0)
        
        self.analysis_results['roles_by_city'] = role_city_pivot
        
        return role_city_pivot
    
    # ==================== VISUALIZATIONS ====================
    
    def plot_top_skills_bar(self, top_n: int = 15, save: bool = True) -> plt.Figure:
        """
        Create bar chart of top skills.
        
        Args:
            top_n: Number of skills to show
            save: Whether to save the figure
            
        Returns:
            Matplotlib figure
        """
        logger.info(f"Creating top {top_n} skills bar chart...")
        
        if 'skill_demand' not in self.analysis_results:
            self.analyze_skill_demand()
        
        skill_df = self.analysis_results['skill_demand'].head(top_n)
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        colors = sns.color_palette("viridis", top_n)
        bars = ax.barh(skill_df['skill'], skill_df['count'], color=colors)
        
        # Add value labels
        for bar, pct in zip(bars, skill_df['percentage']):
            ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2,
                   f'{pct:.1f}%', va='center', fontsize=10)
        
        ax.set_xlabel('Number of Job Postings', fontsize=12)
        ax.set_ylabel('Skill', fontsize=12)
        ax.set_title(f'Top {top_n} Most In-Demand Skills', fontsize=14, fontweight='bold')
        ax.invert_yaxis()
        
        plt.tight_layout()
        
        if save:
            filepath = self.output_dir / 'top_skills_bar.png'
            fig.savefig(filepath, dpi=300, bbox_inches='tight')
            logger.info(f"Saved: {filepath}")
        
        return fig
    
    def plot_skills_city_heatmap(self, top_n_skills: int = 12, top_n_cities: int = 8, save: bool = True) -> plt.Figure:
        """
        Create heatmap of skills by city.
        
        Args:
            top_n_skills: Number of skills
            top_n_cities: Number of cities
            save: Whether to save the figure
            
        Returns:
            Matplotlib figure
        """
        logger.info("Creating skills by city heatmap...")
        
        if 'skills_by_city' not in self.analysis_results:
            self.analyze_skills_by_city(top_n_skills, top_n_cities)
        
        skill_city_df = self.analysis_results['skills_by_city']
        
        # Pivot for heatmap
        heatmap_data = skill_city_df.pivot(
            index='skill',
            columns='city',
            values='percentage'
        ).fillna(0)
        
        fig, ax = plt.subplots(figsize=(14, 10))
        
        sns.heatmap(
            heatmap_data,
            annot=True,
            fmt='.1f',
            cmap='YlOrRd',
            ax=ax,
            cbar_kws={'label': '% of Jobs Requiring Skill'}
        )
        
        ax.set_title('Skill Demand by City (% of Jobs)', fontsize=14, fontweight='bold')
        ax.set_xlabel('City', fontsize=12)
        ax.set_ylabel('Skill', fontsize=12)
        
        plt.tight_layout()
        
        if save:
            filepath = self.output_dir / 'skills_city_heatmap.png'
            fig.savefig(filepath, dpi=300, bbox_inches='tight')
            logger.info(f"Saved: {filepath}")
        
        return fig
    
    def plot_skills_role_heatmap(self, top_n_skills: int = 12, save: bool = True) -> plt.Figure:
        """
        Create heatmap of skills by role category.
        
        Args:
            top_n_skills: Number of skills
            save: Whether to save the figure
            
        Returns:
            Matplotlib figure
        """
        logger.info("Creating skills by role heatmap...")
        
        if 'skills_by_role' not in self.analysis_results:
            self.analyze_skills_by_role(top_n_skills)
        
        skill_role_df = self.analysis_results['skills_by_role']
        
        # Pivot for heatmap
        heatmap_data = skill_role_df.pivot(
            index='skill',
            columns='role',
            values='percentage'
        ).fillna(0)
        
        fig, ax = plt.subplots(figsize=(14, 10))
        
        sns.heatmap(
            heatmap_data,
            annot=True,
            fmt='.1f',
            cmap='Blues',
            ax=ax,
            cbar_kws={'label': '% of Jobs Requiring Skill'}
        )
        
        ax.set_title('Skill vs Role Matrix (% of Jobs)', fontsize=14, fontweight='bold')
        ax.set_xlabel('Role Category', fontsize=12)
        ax.set_ylabel('Skill', fontsize=12)
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        if save:
            filepath = self.output_dir / 'skills_role_heatmap.png'
            fig.savefig(filepath, dpi=300, bbox_inches='tight')
            logger.info(f"Saved: {filepath}")
        
        return fig
    
    def plot_jobs_by_city(self, top_n: int = 10, save: bool = True) -> plt.Figure:
        """
        Create bar chart of job distribution by city.
        
        Args:
            top_n: Number of cities to show
            save: Whether to save the figure
            
        Returns:
            Matplotlib figure
        """
        logger.info("Creating jobs by city chart...")
        
        if 'jobs_by_city' not in self.analysis_results:
            self.analyze_jobs_by_city()
        
        city_df = self.analysis_results['jobs_by_city'].head(top_n)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        colors = sns.color_palette("coolwarm", top_n)
        bars = ax.bar(city_df['city'], city_df['job_count'], color=colors)
        
        # Add value labels
        for bar, pct in zip(bars, city_df['percentage']):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                   f'{pct:.1f}%', ha='center', fontsize=10)
        
        ax.set_xlabel('City', fontsize=12)
        ax.set_ylabel('Number of Jobs', fontsize=12)
        ax.set_title(f'Job Distribution by City (Top {top_n})', fontsize=14, fontweight='bold')
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        if save:
            filepath = self.output_dir / 'jobs_by_city.png'
            fig.savefig(filepath, dpi=300, bbox_inches='tight')
            logger.info(f"Saved: {filepath}")
        
        return fig
    
    def plot_role_distribution(self, save: bool = True) -> plt.Figure:
        """
        Create pie chart of role category distribution.
        
        Args:
            save: Whether to save the figure
            
        Returns:
            Matplotlib figure
        """
        logger.info("Creating role distribution chart...")
        
        role_col = 'role_category' if 'role_category' in self.df.columns else 'title_standardized'
        role_counts = self.df[role_col].value_counts()
        
        fig, ax = plt.subplots(figsize=(10, 10))
        
        colors = sns.color_palette("Set3", len(role_counts))
        wedges, texts, autotexts = ax.pie(
            role_counts.values,
            labels=role_counts.index,
            autopct='%1.1f%%',
            colors=colors,
            explode=[0.02] * len(role_counts)
        )
        
        ax.set_title('Job Distribution by Role Category', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        if save:
            filepath = self.output_dir / 'role_distribution.png'
            fig.savefig(filepath, dpi=300, bbox_inches='tight')
            logger.info(f"Saved: {filepath}")
        
        return fig
    
    def create_interactive_skill_chart(self, top_n: int = 20, save: bool = True):
        """
        Create interactive Plotly bar chart of top skills.
        
        Args:
            top_n: Number of skills
            save: Whether to save HTML file
        """
        logger.info("Creating interactive skill chart...")
        
        if 'skill_demand' not in self.analysis_results:
            self.analyze_skill_demand()
        
        skill_df = self.analysis_results['skill_demand'].head(top_n)
        
        fig = px.bar(
            skill_df,
            x='count',
            y='skill',
            orientation='h',
            color='percentage',
            color_continuous_scale='Viridis',
            title=f'Top {top_n} Most In-Demand Skills',
            labels={'count': 'Number of Jobs', 'skill': 'Skill', 'percentage': '% of Jobs'}
        )
        
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=600
        )
        
        if save:
            filepath = self.output_dir / 'interactive_skills.html'
            fig.write_html(str(filepath))
            logger.info(f"Saved: {filepath}")
        
        return fig
    
    def create_interactive_heatmap(self, save: bool = True):
        """
        Create interactive Plotly heatmap of skills by city.
        
        Args:
            save: Whether to save HTML file
        """
        logger.info("Creating interactive heatmap...")
        
        if 'skills_by_city' not in self.analysis_results:
            self.analyze_skills_by_city()
        
        skill_city_df = self.analysis_results['skills_by_city']
        
        heatmap_data = skill_city_df.pivot(
            index='skill',
            columns='city',
            values='percentage'
        ).fillna(0)
        
        fig = px.imshow(
            heatmap_data,
            color_continuous_scale='YlOrRd',
            title='Skill Demand by City (%)',
            labels={'color': '% of Jobs'}
        )
        
        fig.update_layout(height=700)
        
        if save:
            filepath = self.output_dir / 'interactive_heatmap.html'
            fig.write_html(str(filepath))
            logger.info(f"Saved: {filepath}")
        
        return fig
    
    # ==================== RECOMMENDATIONS ====================
    
    def generate_recommendations(self) -> dict:
        """
        Generate job demand recommendations based on analysis.
        
        Returns:
            Dictionary with recommendations
        """
        logger.info("Generating recommendations...")
        
        recommendations = {
            'top_skills_overall': [],
            'skills_by_city': {},
            'emerging_skills': [],
            'role_skill_combos': [],
            'city_recommendations': []
        }
        
        # Top overall skills
        if 'skill_demand' in self.analysis_results:
            top_skills = self.analysis_results['skill_demand'].head(10)
            recommendations['top_skills_overall'] = [
                {
                    'skill': row['skill'],
                    'demand_percentage': row['percentage'],
                    'recommendation': f"High demand - {row['percentage']:.1f}% of jobs require this skill"
                }
                for _, row in top_skills.iterrows()
            ]
        
        # Skills by city
        if 'skills_by_city' in self.analysis_results:
            skill_city_df = self.analysis_results['skills_by_city']
            cities = skill_city_df['city'].unique()
            
            for city in cities:
                city_data = skill_city_df[skill_city_df['city'] == city].nlargest(5, 'percentage')
                recommendations['skills_by_city'][city] = [
                    {'skill': row['skill'], 'demand': f"{row['percentage']:.1f}%"}
                    for _, row in city_data.iterrows()
                ]
        
        # Role-skill recommendations
        if 'skills_by_role' in self.analysis_results:
            skill_role_df = self.analysis_results['skills_by_role']
            roles = skill_role_df['role'].unique()
            
            for role in roles:
                role_data = skill_role_df[skill_role_df['role'] == role].nlargest(3, 'percentage')
                if not role_data.empty:
                    top_skills_str = ', '.join(role_data['skill'].tolist())
                    recommendations['role_skill_combos'].append({
                        'role': role,
                        'top_skills': top_skills_str,
                        'recommendation': f"Focus on {top_skills_str} for {role} positions"
                    })
        
        # City recommendations
        if 'jobs_by_city' in self.analysis_results:
            top_cities = self.analysis_results['jobs_by_city'].head(5)
            for _, row in top_cities.iterrows():
                recommendations['city_recommendations'].append({
                    'city': row['city'],
                    'job_count': row['job_count'],
                    'market_share': f"{row['percentage']:.1f}%",
                    'recommendation': f"Strong job market with {row['job_count']} openings"
                })
        
        self.analysis_results['recommendations'] = recommendations
        
        return recommendations
    
    def export_analysis_report(self, filename: str = None):
        """
        Export complete analysis to Excel file.
        
        Args:
            filename: Output filename
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"job_analysis_report_{timestamp}.xlsx"
        
        filepath = self.output_dir / filename
        
        logger.info(f"Exporting analysis report to {filepath}...")
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Sheet 1: Overview
            overview_data = {
                'Metric': ['Total Jobs Analyzed', 'Unique Skills', 'Unique Cities', 'Unique Companies'],
                'Value': [
                    len(self.df),
                    len(self.analysis_results.get('skill_demand', [])),
                    self.df['city_standardized'].nunique() if 'city_standardized' in self.df.columns else 'N/A',
                    self.df['company'].nunique()
                ]
            }
            pd.DataFrame(overview_data).to_excel(writer, sheet_name='Overview', index=False)
            
            # Sheet 2: Top Skills
            if 'skill_demand' in self.analysis_results:
                self.analysis_results['skill_demand'].to_excel(writer, sheet_name='Top Skills', index=False)
            
            # Sheet 3: Skills by City
            if 'skills_by_city' in self.analysis_results:
                skill_city_pivot = self.analysis_results['skills_by_city'].pivot(
                    index='skill', columns='city', values='percentage'
                ).fillna(0)
                skill_city_pivot.to_excel(writer, sheet_name='Skills by City')
            
            # Sheet 4: Skills by Role
            if 'skills_by_role' in self.analysis_results:
                skill_role_pivot = self.analysis_results['skills_by_role'].pivot(
                    index='skill', columns='role', values='percentage'
                ).fillna(0)
                skill_role_pivot.to_excel(writer, sheet_name='Skills by Role')
            
            # Sheet 5: Jobs by City
            if 'jobs_by_city' in self.analysis_results:
                self.analysis_results['jobs_by_city'].to_excel(writer, sheet_name='Jobs by City', index=False)
            
            # Sheet 6: Recommendations
            if 'recommendations' in self.analysis_results:
                recs = self.analysis_results['recommendations']
                if recs['top_skills_overall']:
                    pd.DataFrame(recs['top_skills_overall']).to_excel(
                        writer, sheet_name='Recommendations', index=False
                    )
        
        logger.info(f"Report exported to: {filepath}")
    
    def run_full_analysis(self):
        """
        Run complete analysis pipeline.
        """
        logger.info("Starting full analysis pipeline...")
        
        # Load data
        self.load_data()
        
        # Run all analyses
        self.analyze_skill_demand()
        self.analyze_skills_by_city()
        self.analyze_skills_by_role()
        self.analyze_jobs_by_city()
        
        # Generate visualizations
        self.plot_top_skills_bar()
        self.plot_skills_city_heatmap()
        self.plot_skills_role_heatmap()
        self.plot_jobs_by_city()
        self.plot_role_distribution()
        
        # Create interactive charts
        self.create_interactive_skill_chart()
        self.create_interactive_heatmap()
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Export report
        self.export_analysis_report()
        
        logger.info("Full analysis complete!")
        
        return self.analysis_results


def main():
    """Main entry point for the analyzer."""
    analyzer = JobAnalyzer(
        data_dir="../data/processed",
        output_dir="../visualizations"
    )
    
    results = analyzer.run_full_analysis()
    
    print("\n" + "="*50)
    print("ANALYSIS COMPLETE!")
    print("="*50)
    
    print("\n📊 TOP 10 MOST IN-DEMAND SKILLS:")
    print("-"*40)
    for i, row in results['skill_demand'].head(10).iterrows():
        print(f"  {i+1}. {row['skill'].capitalize()}: {row['percentage']:.1f}% of jobs")
    
    print("\n🏙️ TOP 5 CITIES BY JOB COUNT:")
    print("-"*40)
    for i, row in results['jobs_by_city'].head(5).iterrows():
        print(f"  {i+1}. {row['city']}: {row['job_count']} jobs ({row['percentage']:.1f}%)")
    
    print("\n💡 KEY RECOMMENDATIONS:")
    print("-"*40)
    if 'recommendations' in results:
        for rec in results['recommendations']['role_skill_combos'][:5]:
            print(f"  • {rec['recommendation']}")
    
    print(f"\n📁 Visualizations saved to: ../visualizations/")
    print(f"📁 Report saved to: ../visualizations/")
    
    return results


if __name__ == "__main__":
    main()
