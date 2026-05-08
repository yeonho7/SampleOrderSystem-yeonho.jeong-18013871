"""
TDD Red 단계 — SampleRepository 단위 테스트.

repository/sample_repository.py 가 아직 존재하지 않으므로
이 파일을 실행하면 ImportError 가 발생하며 전체 테스트가 FAIL 상태여야 한다.
구현 후 모든 테스트가 GREEN 으로 전환되는 것이 목표다.
"""

import json
import pytest

from model.sample import Sample
from repository.sample_repository import SampleRepository


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def _make_sample(sample_id="S-001", name="실리콘 웨이퍼-8인치",
                 avg_production_time=30.0, yield_rate=0.92, stock=100):
    return Sample(
        sample_id=sample_id,
        name=name,
        avg_production_time=avg_production_time,
        yield_rate=yield_rate,
        stock=stock,
    )


# ---------------------------------------------------------------------------
# create / find_by_id
# ---------------------------------------------------------------------------

class TestSampleRepositoryCreate:

    def test_create_returns_created_sample(self, tmp_data_dir):
        repo = SampleRepository(tmp_data_dir / "samples.json")
        sample = _make_sample()
        result = repo.create(sample)
        assert result.sample_id == "S-001"

    def test_find_by_id_returns_sample_after_create(self, tmp_data_dir):
        repo = SampleRepository(tmp_data_dir / "samples.json")
        repo.create(_make_sample(sample_id="S-001"))
        found = repo.find_by_id("S-001")
        assert found is not None
        assert found.sample_id == "S-001"

    def test_find_by_id_returns_none_when_not_exists(self, tmp_data_dir):
        repo = SampleRepository(tmp_data_dir / "samples.json")
        result = repo.find_by_id("S-999")
        assert result is None

    def test_find_by_id_restores_all_fields(self, tmp_data_dir):
        repo = SampleRepository(tmp_data_dir / "samples.json")
        repo.create(_make_sample(
            sample_id="S-002",
            name="GaAs 기판",
            avg_production_time=45.0,
            yield_rate=0.85,
            stock=50,
        ))
        found = repo.find_by_id("S-002")
        assert found.name == "GaAs 기판"
        assert found.avg_production_time == 45.0
        assert found.yield_rate == 0.85
        assert found.stock == 50


# ---------------------------------------------------------------------------
# find_all
# ---------------------------------------------------------------------------

class TestSampleRepositoryFindAll:

    def test_find_all_returns_empty_list_when_no_samples(self, tmp_data_dir):
        repo = SampleRepository(tmp_data_dir / "samples.json")
        assert repo.find_all() == []

    def test_find_all_returns_all_created_samples(self, tmp_data_dir):
        repo = SampleRepository(tmp_data_dir / "samples.json")
        repo.create(_make_sample(sample_id="S-001"))
        repo.create(_make_sample(sample_id="S-002", name="GaAs 기판"))
        result = repo.find_all()
        assert len(result) == 2

    def test_find_all_returns_sample_instances(self, tmp_data_dir):
        repo = SampleRepository(tmp_data_dir / "samples.json")
        repo.create(_make_sample(sample_id="S-001"))
        result = repo.find_all()
        assert isinstance(result[0], Sample)


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

class TestSampleRepositoryUpdate:

    def test_update_returns_true_when_sample_exists(self, tmp_data_dir):
        repo = SampleRepository(tmp_data_dir / "samples.json")
        repo.create(_make_sample(sample_id="S-001"))
        updated = _make_sample(sample_id="S-001", stock=200)
        assert repo.update(updated) is True

    def test_update_changes_field_value(self, tmp_data_dir):
        repo = SampleRepository(tmp_data_dir / "samples.json")
        repo.create(_make_sample(sample_id="S-001", stock=100))
        repo.update(_make_sample(sample_id="S-001", stock=999))
        found = repo.find_by_id("S-001")
        assert found.stock == 999

    def test_update_returns_false_when_sample_not_exists(self, tmp_data_dir):
        repo = SampleRepository(tmp_data_dir / "samples.json")
        result = repo.update(_make_sample(sample_id="S-999"))
        assert result is False


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

class TestSampleRepositoryDelete:

    def test_delete_returns_true_when_sample_exists(self, tmp_data_dir):
        repo = SampleRepository(tmp_data_dir / "samples.json")
        repo.create(_make_sample(sample_id="S-001"))
        assert repo.delete("S-001") is True

    def test_delete_removes_sample_from_find_all(self, tmp_data_dir):
        repo = SampleRepository(tmp_data_dir / "samples.json")
        repo.create(_make_sample(sample_id="S-001"))
        repo.delete("S-001")
        assert repo.find_by_id("S-001") is None

    def test_delete_returns_false_when_sample_not_exists(self, tmp_data_dir):
        repo = SampleRepository(tmp_data_dir / "samples.json")
        assert repo.delete("S-999") is False


# ---------------------------------------------------------------------------
# find_by_name
# ---------------------------------------------------------------------------

class TestSampleRepositoryFindByName:

    def test_find_by_name_returns_matching_samples(self, tmp_data_dir):
        repo = SampleRepository(tmp_data_dir / "samples.json")
        repo.create(_make_sample(sample_id="S-001", name="실리콘 웨이퍼-8인치"))
        repo.create(_make_sample(sample_id="S-002", name="GaAs 기판"))
        result = repo.find_by_name("웨이퍼")
        assert len(result) == 1
        assert result[0].sample_id == "S-001"

    def test_find_by_name_returns_empty_list_when_no_match(self, tmp_data_dir):
        repo = SampleRepository(tmp_data_dir / "samples.json")
        repo.create(_make_sample(sample_id="S-001", name="실리콘 웨이퍼-8인치"))
        result = repo.find_by_name("없는키워드")
        assert result == []

    def test_find_by_name_returns_multiple_matches(self, tmp_data_dir):
        repo = SampleRepository(tmp_data_dir / "samples.json")
        repo.create(_make_sample(sample_id="S-001", name="실리콘 웨이퍼-8인치"))
        repo.create(_make_sample(sample_id="S-002", name="실리콘 웨이퍼-12인치"))
        repo.create(_make_sample(sample_id="S-003", name="GaAs 기판"))
        result = repo.find_by_name("웨이퍼")
        assert len(result) == 2

    def test_find_by_name_is_case_insensitive_for_ascii(self, tmp_data_dir):
        repo = SampleRepository(tmp_data_dir / "samples.json")
        repo.create(_make_sample(sample_id="S-001", name="GaAs 기판"))
        result = repo.find_by_name("gaas")
        assert len(result) == 1


# ---------------------------------------------------------------------------
# write-through 영속성
# ---------------------------------------------------------------------------

class TestSampleRepositoryPersistence:

    def test_create_writes_to_json_file(self, tmp_data_dir):
        """create 후 JSON 파일을 직접 읽었을 때 데이터가 저장되어야 한다."""
        filepath = tmp_data_dir / "samples.json"
        repo = SampleRepository(filepath)
        repo.create(_make_sample(sample_id="S-001"))
        raw = json.loads(filepath.read_text(encoding="utf-8"))
        assert len(raw) == 1

    def test_update_writes_to_json_file(self, tmp_data_dir):
        """update 후 JSON 파일을 직접 읽었을 때 변경사항이 반영되어야 한다."""
        filepath = tmp_data_dir / "samples.json"
        repo = SampleRepository(filepath)
        repo.create(_make_sample(sample_id="S-001", stock=100))
        repo.update(_make_sample(sample_id="S-001", stock=777))
        raw = json.loads(filepath.read_text(encoding="utf-8"))
        assert raw[0]["stock"] == 777

    def test_delete_writes_to_json_file(self, tmp_data_dir):
        """delete 후 JSON 파일을 직접 읽었을 때 항목이 제거되어야 한다."""
        filepath = tmp_data_dir / "samples.json"
        repo = SampleRepository(filepath)
        repo.create(_make_sample(sample_id="S-001"))
        repo.delete("S-001")
        raw = json.loads(filepath.read_text(encoding="utf-8"))
        assert raw == []

    def test_new_instance_loads_existing_json(self, tmp_data_dir):
        """같은 JSON 파일로 새 인스턴스를 만들면 기존 데이터를 불러와야 한다."""
        filepath = tmp_data_dir / "samples.json"
        repo1 = SampleRepository(filepath)
        repo1.create(_make_sample(sample_id="S-001"))

        repo2 = SampleRepository(filepath)
        assert repo2.find_by_id("S-001") is not None

    def test_creates_empty_json_file_when_not_exists(self, tmp_path):
        """파일이 없을 때 Repository 생성 시 빈 JSON 배열로 초기화해야 한다."""
        filepath = tmp_path / "new_samples.json"
        assert not filepath.exists()
        SampleRepository(filepath)
        assert filepath.exists()
        assert json.loads(filepath.read_text(encoding="utf-8")) == []
