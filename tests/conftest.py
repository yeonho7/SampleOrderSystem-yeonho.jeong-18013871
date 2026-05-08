import json
import pytest
from pathlib import Path

from repository.sample_repository import SampleRepository
from repository.order_repository import OrderRepository
from repository.production_job_repository import ProductionJobRepository


@pytest.fixture
def tmp_data_dir(tmp_path):
    for name in ("samples.json", "orders.json", "production_jobs.json"):
        (tmp_path / name).write_text("[]", encoding="utf-8")
    return tmp_path


@pytest.fixture
def repos(tmp_data_dir):
    """3개 Repository를 한번에 제공하는 공통 픽스처."""
    return (
        SampleRepository(tmp_data_dir / "samples.json"),
        OrderRepository(tmp_data_dir / "orders.json"),
        ProductionJobRepository(tmp_data_dir / "production_jobs.json"),
    )
