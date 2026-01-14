"""
Project Cleanup Script
=====================
Clean up unwanted files, logs, and old outputs while keeping recent data.

Usage:
    python cleanup_project.py --dry-run  # Preview what will be deleted
    python cleanup_project.py            # Actually delete files
"""

import os
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import shutil

class ProjectCleaner:
    """Clean up project directory."""
    
    def __init__(self, project_root: str = ".."):
        self.project_root = Path(project_root).resolve()
        self.files_to_delete = []
        self.dirs_to_delete = []
        self.files_to_keep = []
        
    def find_log_files(self):
        """Find all log files in the project."""
        log_files = []
        for pattern in ['*.log', '*.log.*']:
            log_files.extend(self.project_root.rglob(pattern))
        return log_files
    
    def find_pycache_dirs(self):
        """Find all __pycache__ directories."""
        return list(self.project_root.rglob('__pycache__'))
    
    def find_old_outputs(self, keep_recent: int = 3):
        """
        Find old output files, keeping only the most recent ones.
        
        Args:
            keep_recent: Number of recent files to keep per category
        """
        outputs_dir = self.project_root / 'outputs' / 'visualizations'
        
        if not outputs_dir.exists():
            return [], []
        
        # Group files by type
        file_groups = {}
        for file in outputs_dir.glob('*.png'):
            # Extract base name without timestamp
            name = file.stem
            # Group by pattern (e.g., 'jobs_by_city', 'skills_demand')
            if name not in file_groups:
                file_groups[name] = []
            file_groups[name].append(file)
        
        to_delete = []
        to_keep = []
        
        for group_name, files in file_groups.items():
            # Sort by modification time (newest first)
            sorted_files = sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Keep recent, mark rest for deletion
            to_keep.extend(sorted_files[:keep_recent])
            to_delete.extend(sorted_files[keep_recent:])
        
        return to_delete, to_keep
    
    def find_old_data_files(self, keep_recent: int = 5):
        """
        Find old data files, keeping only recent ones.
        
        Args:
            keep_recent: Number of recent files to keep
        """
        data_dir = self.project_root / 'data' / 'raw'
        
        if not data_dir.exists():
            return [], []
        
        # Find all CSV and JSON files (excluding backups)
        data_files = []
        for pattern in ['jobs_*.csv', 'jobs_*.json']:
            data_files.extend(data_dir.glob(pattern))
        
        # Sort by modification time (newest first)
        sorted_files = sorted(data_files, key=lambda f: f.stat().st_mtime, reverse=True)
        
        to_keep = sorted_files[:keep_recent]
        to_delete = sorted_files[keep_recent:]
        
        return to_delete, to_keep
    
    def find_old_backups(self, keep_days: int = 7):
        """
        Find old backup files older than specified days.
        
        Args:
            keep_days: Keep backups from last N days
        """
        backup_dir = self.project_root / 'data' / 'raw' / 'backups'
        
        if not backup_dir.exists():
            return []
        
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        old_backups = []
        
        for backup_file in backup_dir.glob('*'):
            if backup_file.stat().st_mtime < cutoff_date.timestamp():
                old_backups.append(backup_file)
        
        return old_backups
    
    def find_temp_files(self):
        """Find temporary files."""
        temp_patterns = ['*.tmp', '*.temp', '*~', '.DS_Store', 'Thumbs.db']
        temp_files = []
        
        for pattern in temp_patterns:
            temp_files.extend(self.project_root.rglob(pattern))
        
        return temp_files
    
    def scan_project(self):
        """Scan entire project for cleanable files."""
        print("🔍 Scanning project for cleanable files...\n")
        
        # Find log files
        log_files = self.find_log_files()
        if log_files:
            self.files_to_delete.extend(log_files)
            print(f"📋 Found {len(log_files)} log files")
        
        # Find __pycache__ directories
        pycache_dirs = self.find_pycache_dirs()
        if pycache_dirs:
            self.dirs_to_delete.extend(pycache_dirs)
            print(f"📦 Found {len(pycache_dirs)} __pycache__ directories")
        
        # Find old outputs (keep 3 most recent)
        old_outputs, kept_outputs = self.find_old_outputs(keep_recent=3)
        if old_outputs:
            self.files_to_delete.extend(old_outputs)
            self.files_to_keep.extend(kept_outputs)
            print(f"📊 Found {len(old_outputs)} old visualization files (keeping {len(kept_outputs)} recent)")
        
        # Find old data files (keep 5 most recent)
        old_data, kept_data = self.find_old_data_files(keep_recent=5)
        if old_data:
            self.files_to_delete.extend(old_data)
            self.files_to_keep.extend(kept_data)
            print(f"💾 Found {len(old_data)} old data files (keeping {len(kept_data)} recent)")
        
        # Find old backups (older than 7 days)
        old_backups = self.find_old_backups(keep_days=7)
        if old_backups:
            self.files_to_delete.extend(old_backups)
            print(f"🗄️ Found {len(old_backups)} old backup files (>7 days)")
        
        # Find temp files
        temp_files = self.find_temp_files()
        if temp_files:
            self.files_to_delete.extend(temp_files)
            print(f"🗑️ Found {len(temp_files)} temporary files")
        
        print(f"\n{'='*60}")
        print(f"Total files to delete: {len(self.files_to_delete)}")
        print(f"Total directories to delete: {len(self.dirs_to_delete)}")
        print(f"Total files to keep: {len(self.files_to_keep)}")
        print(f"{'='*60}\n")
    
    def show_preview(self):
        """Show preview of what will be deleted."""
        print("\n📋 DELETION PREVIEW\n")
        
        if self.files_to_delete:
            print("Files to delete:")
            for file in sorted(self.files_to_delete)[:20]:  # Show first 20
                size = file.stat().st_size / 1024  # KB
                rel_path = file.relative_to(self.project_root)
                print(f"  - {rel_path} ({size:.1f} KB)")
            
            if len(self.files_to_delete) > 20:
                print(f"  ... and {len(self.files_to_delete) - 20} more files")
        
        if self.dirs_to_delete:
            print("\nDirectories to delete:")
            for dir_path in sorted(self.dirs_to_delete)[:10]:
                rel_path = dir_path.relative_to(self.project_root)
                print(f"  - {rel_path}/")
            
            if len(self.dirs_to_delete) > 10:
                print(f"  ... and {len(self.dirs_to_delete) - 10} more directories")
        
        if self.files_to_keep:
            print("\n✅ Files to KEEP (recent):")
            for file in sorted(self.files_to_keep)[:10]:
                rel_path = file.relative_to(self.project_root)
                print(f"  ✓ {rel_path}")
            
            if len(self.files_to_keep) > 10:
                print(f"  ... and {len(self.files_to_keep) - 10} more files")
        
        print()
    
    def calculate_space_to_free(self):
        """Calculate total space that will be freed."""
        total_size = 0
        
        for file in self.files_to_delete:
            try:
                total_size += file.stat().st_size
            except:
                pass
        
        for dir_path in self.dirs_to_delete:
            try:
                for file in dir_path.rglob('*'):
                    if file.is_file():
                        total_size += file.stat().st_size
            except:
                pass
        
        return total_size
    
    def cleanup(self, dry_run: bool = False):
        """
        Perform the cleanup.
        
        Args:
            dry_run: If True, only show what would be deleted
        """
        if dry_run:
            print("\n🔍 DRY RUN MODE - No files will be deleted\n")
            self.show_preview()
            
            space_to_free = self.calculate_space_to_free()
            print(f"💾 Space to be freed: {space_to_free / (1024*1024):.2f} MB")
            return
        
        print("\n🗑️ STARTING CLEANUP\n")
        
        deleted_files = 0
        deleted_dirs = 0
        errors = []
        
        # Delete files
        for file in self.files_to_delete:
            try:
                file.unlink()
                deleted_files += 1
                print(f"✓ Deleted: {file.relative_to(self.project_root)}")
            except Exception as e:
                errors.append(f"Failed to delete {file}: {e}")
        
        # Delete directories
        for dir_path in self.dirs_to_delete:
            try:
                shutil.rmtree(dir_path)
                deleted_dirs += 1
                print(f"✓ Deleted: {dir_path.relative_to(self.project_root)}/")
            except Exception as e:
                errors.append(f"Failed to delete {dir_path}: {e}")
        
        print(f"\n{'='*60}")
        print(f"✅ Cleanup complete!")
        print(f"   - Deleted {deleted_files} files")
        print(f"   - Deleted {deleted_dirs} directories")
        
        if errors:
            print(f"\n⚠️ Errors encountered:")
            for error in errors:
                print(f"   - {error}")
        
        print(f"{'='*60}\n")
    
    def create_project_structure_summary(self):
        """Create a summary of the cleaned project structure."""
        summary_file = self.project_root / 'PROJECT_STRUCTURE.md'
        
        with open(summary_file, 'w') as f:
            f.write("# LinkedIn Job Analysis - Project Structure\n\n")
            f.write(f"Last cleaned: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Directory Structure\n\n")
            f.write("```\n")
            f.write("Linkedin-Job-Analysis/\n")
            f.write("├── data/\n")
            f.write("│   ├── raw/              # Raw scraped data (keep 5 recent files)\n")
            f.write("│   └── processed/        # Cleaned data\n")
            f.write("├── scripts/\n")
            f.write("│   ├── scraper_v2.py     # Main scraper\n")
            f.write("│   ├── scraper_india.py  # Indian cities scraper\n")
            f.write("│   ├── visualize_data.py # Visualization module\n")
            f.write("│   └── cleanup_project.py # This cleanup script\n")
            f.write("├── outputs/\n")
            f.write("│   └── visualizations/   # Charts and graphs (keep 3 recent per type)\n")
            f.write("├── notebooks/            # Jupyter notebooks\n")
            f.write("└── docs/                 # Documentation\n")
            f.write("```\n\n")
            
            f.write("## Cleanup Rules\n\n")
            f.write("- **Log files**: Deleted on cleanup\n")
            f.write("- **__pycache__**: Deleted on cleanup\n")
            f.write("- **Data files**: Keep 5 most recent\n")
            f.write("- **Visualizations**: Keep 3 most recent per type\n")
            f.write("- **Backups**: Keep files from last 7 days\n")
            f.write("- **Temp files**: Deleted on cleanup\n")
        
        print(f"📄 Created project structure summary: PROJECT_STRUCTURE.md")


def main():
    parser = argparse.ArgumentParser(description='Clean up project files')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Preview what will be deleted without actually deleting')
    parser.add_argument('--keep-outputs', type=int, default=3,
                       help='Number of recent output files to keep (default: 3)')
    parser.add_argument('--keep-data', type=int, default=5,
                       help='Number of recent data files to keep (default: 5)')
    
    args = parser.parse_args()
    
    print("="*60)
    print("🧹 LinkedIn Job Analysis - Project Cleanup")
    print("="*60)
    
    cleaner = ProjectCleaner()
    cleaner.scan_project()
    
    if args.dry_run:
        cleaner.cleanup(dry_run=True)
        print("\n💡 To actually delete files, run without --dry-run flag")
    else:
        # Confirm before deletion
        print("\n⚠️  WARNING: This will permanently delete files!")
        response = input("Continue? (yes/no): ").strip().lower()
        
        if response == 'yes':
            cleaner.cleanup(dry_run=False)
            cleaner.create_project_structure_summary()
        else:
            print("\n❌ Cleanup cancelled")
    
    print("\n✨ Done!")


if __name__ == "__main__":
    main()
