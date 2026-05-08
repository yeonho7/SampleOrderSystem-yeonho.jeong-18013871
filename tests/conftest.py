import json
import pytest
from pathlib import Path


@pytest.fixture
def tmp_data_dir(tmp_path):
    """임시 JSON 데이터 디렉토리를 제공하는 fixture."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    for filename in ("samples.json", "orders.json", "production_jobs.json"):
        (data_dir / filename).write_text("[]", encoding="utf-8")
    return data_dir
