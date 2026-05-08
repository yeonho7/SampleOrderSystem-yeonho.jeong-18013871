"""
TDD Red 단계 — ProductionJobRepository 단위 테스트.

repository/production_job_repository.py 가 아직 존재하지 않으므로
이 파일을 실행하면 ImportError 가 발생하며 전체 테스트가 FAIL 상태여야 한다.
구현 후 모든 테스트가 GREEN 으로 전환되는 것이 목표다.
"""

import json
import pytest
from datetime import datetime, timedelta

from model.production_job import ProductionJob
from repository.production_job_repository import ProductionJobRepository


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def _make_job(order_id="ORD-20260508-0001", sample_id="S-001",
              shortage=20, actual_production=25, total_time=750.0,
              enqueued_at=None):
    job = ProductionJob(
        order_id=order_id,
        sample_id=sample_id,
        shortage=shortage,
        actual_production=actual_production,
        total_time=total_time,
    )
    if enqueued_at is not None:
        job.enqueued_at = enqueued_at
    return job


# ---------------------------------------------------------------------------
# create / find_by_id
# ---------------------------------------------------------------------------

class TestProductionJobRepositoryCreate:

    def test_create_returns_created_job(self, tmp_data_dir):
        repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
        job = _make_job()
        result = repo.create(job)
        assert result.order_id == "ORD-20260508-0001"

    def test_find_by_id_returns_job_after_create(self, tmp_data_dir):
        repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
        repo.create(_make_job(order_id="ORD-20260508-0001"))
        found = repo.find_by_id("ORD-20260508-0001")
        assert found is not None
        assert found.order_id == "ORD-20260508-0001"

    def test_find_by_id_returns_none_when_not_exists(self, tmp_data_dir):
        repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
        result = repo.find_by_id("ORD-99991231-9999")
        assert result is None

    def test_find_by_id_restores_all_fields(self, tmp_data_dir):
        repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
        repo.create(_make_job(
            order_id="ORD-20260508-0002",
            sample_id="S-007",
            shortage=30,
            actual_production=37,
            total_time=1110.0,
        ))
        found = repo.find_by_id("ORD-20260508-0002")
        assert found.sample_id == "S-007"
        assert found.shortage == 30
        assert found.actual_production == 37
        assert found.total_time == 1110.0

    def test_find_by_id_restores_enqueued_at_as_datetime(self, tmp_data_dir):
        repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
        repo.create(_make_job())
        found = repo.find_by_id("ORD-20260508-0001")
        assert isinstance(found.enqueued_at, datetime)


# ---------------------------------------------------------------------------
# find_all
# ---------------------------------------------------------------------------

class TestProductionJobRepositoryFindAll:

    def test_find_all_returns_empty_list_when_no_jobs(self, tmp_data_dir):
        repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
        assert repo.find_all() == []

    def test_find_all_returns_all_created_jobs(self, tmp_data_dir):
        repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
        repo.create(_make_job(order_id="ORD-20260508-0001"))
        repo.create(_make_job(order_id="ORD-20260508-0002"))
        result = repo.find_all()
        assert len(result) == 2

    def test_find_all_returns_production_job_instances(self, tmp_data_dir):
        repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
        repo.create(_make_job())
        result = repo.find_all()
        assert isinstance(result[0], ProductionJob)


# ---------------------------------------------------------------------------
# find_all 정렬 보장 (FIFO — enqueued_at 오름차순)
# ---------------------------------------------------------------------------

class TestProductionJobRepositoryFindAllOrdering:

    def test_find_all_is_sorted_by_enqueued_at_ascending(self, tmp_data_dir):
        """find_all 결과는 enqueued_at 오름차순이어야 한다."""
        now = datetime(2026, 5, 8, 12, 0, 0)
        repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
        # 나중 시각 먼저 삽입
        repo.create(_make_job(order_id="ORD-20260508-0002", enqueued_at=now + timedelta(hours=2)))
        repo.create(_make_job(order_id="ORD-20260508-0001", enqueued_at=now))
        repo.create(_make_job(order_id="ORD-20260508-0003", enqueued_at=now + timedelta(hours=1)))

        result = repo.find_all()
        enqueued_times = [job.enqueued_at for job in result]
        assert enqueued_times == sorted(enqueued_times)

    def test_find_all_first_item_is_oldest_enqueued(self, tmp_data_dir):
        """find_all 의 첫 번째 항목은 가장 이른 enqueued_at 을 가져야 한다."""
        now = datetime(2026, 5, 8, 9, 0, 0)
        repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
        repo.create(_make_job(order_id="ORD-20260508-0002", enqueued_at=now + timedelta(minutes=30)))
        repo.create(_make_job(order_id="ORD-20260508-0001", enqueued_at=now))

        result = repo.find_all()
        assert result[0].order_id == "ORD-20260508-0001"


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

class TestProductionJobRepositoryUpdate:

    def test_update_returns_true_when_job_exists(self, tmp_data_dir):
        repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
        repo.create(_make_job(order_id="ORD-20260508-0001"))
        updated = _make_job(order_id="ORD-20260508-0001", shortage=99)
        assert repo.update(updated) is True

    def test_update_changes_field_value(self, tmp_data_dir):
        repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
        repo.create(_make_job(order_id="ORD-20260508-0001", shortage=20))
        repo.update(_make_job(order_id="ORD-20260508-0001", shortage=99))
        found = repo.find_by_id("ORD-20260508-0001")
        assert found.shortage == 99

    def test_update_returns_false_when_job_not_exists(self, tmp_data_dir):
        repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
        result = repo.update(_make_job(order_id="ORD-99991231-9999"))
        assert result is False


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

class TestProductionJobRepositoryDelete:

    def test_delete_returns_true_when_job_exists(self, tmp_data_dir):
        repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
        repo.create(_make_job(order_id="ORD-20260508-0001"))
        assert repo.delete("ORD-20260508-0001") is True

    def test_delete_removes_job_from_find_all(self, tmp_data_dir):
        repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
        repo.create(_make_job(order_id="ORD-20260508-0001"))
        repo.delete("ORD-20260508-0001")
        assert repo.find_by_id("ORD-20260508-0001") is None

    def test_delete_returns_false_when_job_not_exists(self, tmp_data_dir):
        repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
        assert repo.delete("ORD-99991231-9999") is False


# ---------------------------------------------------------------------------
# find_first
# ---------------------------------------------------------------------------

class TestProductionJobRepositoryFindFirst:

    def test_find_first_returns_none_when_no_jobs(self, tmp_data_dir):
        repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
        assert repo.find_first() is None

    def test_find_first_returns_job_when_one_exists(self, tmp_data_dir):
        repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
        repo.create(_make_job(order_id="ORD-20260508-0001"))
        result = repo.find_first()
        assert result is not None
        assert isinstance(result, ProductionJob)

    def test_find_first_returns_oldest_enqueued_job(self, tmp_data_dir):
        """find_first 는 enqueued_at 이 가장 이른 job (FIFO 선두) 을 반환해야 한다."""
        now = datetime(2026, 5, 8, 10, 0, 0)
        repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
        repo.create(_make_job(order_id="ORD-20260508-0002", enqueued_at=now + timedelta(hours=1)))
        repo.create(_make_job(order_id="ORD-20260508-0001", enqueued_at=now))

        result = repo.find_first()
        assert result.order_id == "ORD-20260508-0001"

    def test_find_first_after_delete_returns_next_job(self, tmp_data_dir):
        """선두 job 삭제 후 find_first 는 다음 job 을 반환해야 한다."""
        now = datetime(2026, 5, 8, 10, 0, 0)
        repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
        repo.create(_make_job(order_id="ORD-20260508-0001", enqueued_at=now))
        repo.create(_make_job(order_id="ORD-20260508-0002", enqueued_at=now + timedelta(hours=1)))

        repo.delete("ORD-20260508-0001")
        result = repo.find_first()
        assert result.order_id == "ORD-20260508-0002"


# ---------------------------------------------------------------------------
# count
# ---------------------------------------------------------------------------

class TestProductionJobRepositoryCount:

    def test_count_returns_zero_when_no_jobs(self, tmp_data_dir):
        repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
        assert repo.count() == 0

    def test_count_returns_correct_count_after_creates(self, tmp_data_dir):
        repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
        repo.create(_make_job(order_id="ORD-20260508-0001"))
        repo.create(_make_job(order_id="ORD-20260508-0002"))
        assert repo.count() == 2

    def test_count_decrements_after_delete(self, tmp_data_dir):
        repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
        repo.create(_make_job(order_id="ORD-20260508-0001"))
        repo.create(_make_job(order_id="ORD-20260508-0002"))
        repo.delete("ORD-20260508-0001")
        assert repo.count() == 1

    def test_count_returns_int(self, tmp_data_dir):
        repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
        assert isinstance(repo.count(), int)


# ---------------------------------------------------------------------------
# write-through 영속성
# ---------------------------------------------------------------------------

class TestProductionJobRepositoryPersistence:

    def test_create_writes_to_json_file(self, tmp_data_dir):
        """create 후 JSON 파일을 직접 읽었을 때 데이터가 저장되어야 한다."""
        filepath = tmp_data_dir / "production_jobs.json"
        repo = ProductionJobRepository(filepath)
        repo.create(_make_job(order_id="ORD-20260508-0001"))
        raw = json.loads(filepath.read_text(encoding="utf-8"))
        assert len(raw) == 1

    def test_delete_writes_to_json_file(self, tmp_data_dir):
        """delete 후 JSON 파일을 직접 읽었을 때 항목이 제거되어야 한다."""
        filepath = tmp_data_dir / "production_jobs.json"
        repo = ProductionJobRepository(filepath)
        repo.create(_make_job(order_id="ORD-20260508-0001"))
        repo.delete("ORD-20260508-0001")
        raw = json.loads(filepath.read_text(encoding="utf-8"))
        assert raw == []

    def test_new_instance_loads_existing_json(self, tmp_data_dir):
        """같은 JSON 파일로 새 인스턴스를 만들면 기존 데이터를 불러와야 한다."""
        filepath = tmp_data_dir / "production_jobs.json"
        repo1 = ProductionJobRepository(filepath)
        repo1.create(_make_job(order_id="ORD-20260508-0001"))

        repo2 = ProductionJobRepository(filepath)
        assert repo2.find_by_id("ORD-20260508-0001") is not None

    def test_new_instance_preserves_fifo_order(self, tmp_data_dir):
        """새 인스턴스로 불러왔을 때도 enqueued_at 오름차순 정렬이 유지되어야 한다."""
        now = datetime(2026, 5, 8, 8, 0, 0)
        filepath = tmp_data_dir / "production_jobs.json"
        repo1 = ProductionJobRepository(filepath)
        repo1.create(_make_job(order_id="ORD-20260508-0002", enqueued_at=now + timedelta(hours=1)))
        repo1.create(_make_job(order_id="ORD-20260508-0001", enqueued_at=now))

        repo2 = ProductionJobRepository(filepath)
        result = repo2.find_all()
        assert result[0].order_id == "ORD-20260508-0001"
