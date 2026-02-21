"""Tests for scheduler.py — verify pipeline script path is correct."""

from pathlib import Path


def test_pipeline_script_exists():
    """The scheduler must reference a pipeline script that actually exists."""
    scripts_dir = Path(__file__).parent.parent / 'scripts'
    pipeline_script = scripts_dir / 'master_flow.py'
    assert pipeline_script.exists(), f"Pipeline script not found: {pipeline_script}"


def test_scheduler_imports():
    """Verify scheduler module can be imported without errors."""
    from scheduler import PipelineScheduler
    s = PipelineScheduler()
    assert s is not None
