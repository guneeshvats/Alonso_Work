# tests/test_tasks.py
from app.celery_worker import sample_task

def test_sample_task():
    """Test the sample Celery task."""
    result = sample_task.apply(args=[2, 3]).get()
    assert result == 5
