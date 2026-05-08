import json
from pathlib import Path

from model.production_job import ProductionJob
from repository.base_repository import BaseRepository


def _job_to_dict(job: ProductionJob) -> dict:
    return {
        "order_id": job.order_id,
        "sample_id": job.sample_id,
        "shortage": job.shortage,
        "actual_production": job.actual_production,
        "total_time": job.total_time,
        "enqueued_at": job.enqueued_at.isoformat(),
    }


def _dict_to_job(item: dict) -> ProductionJob:
    from datetime import datetime
    job = ProductionJob(
        order_id=item["order_id"],
        sample_id=item["sample_id"],
        shortage=item["shortage"],
        actual_production=item["actual_production"],
        total_time=item["total_time"],
    )
    job.enqueued_at = datetime.fromisoformat(item["enqueued_at"])
    return job


class ProductionJobRepository(BaseRepository):

    def __init__(self, filepath: Path):
        self._filepath = filepath

    def _read(self) -> list[dict]:
        return json.loads(self._filepath.read_text(encoding="utf-8"))

    def _write(self, data: list[dict]):
        self._filepath.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def create(self, job: ProductionJob) -> ProductionJob:
        data = self._read()
        data.append(_job_to_dict(job))
        self._write(data)
        return job

    def find_by_id(self, order_id: str) -> ProductionJob | None:
        for item in self._read():
            if item["order_id"] == order_id:
                return _dict_to_job(item)
        return None

    def find_all(self) -> list[ProductionJob]:
        jobs = [_dict_to_job(item) for item in self._read()]
        jobs.sort(key=lambda j: j.enqueued_at)
        return jobs

    def update(self, job: ProductionJob) -> bool:
        data = self._read()
        for i, item in enumerate(data):
            if item["order_id"] == job.order_id:
                data[i] = _job_to_dict(job)
                self._write(data)
                return True
        return False

    def delete(self, order_id: str) -> bool:
        data = self._read()
        new_data = [item for item in data if item["order_id"] != order_id]
        if len(new_data) == len(data):
            return False
        self._write(new_data)
        return True

    def find_first(self) -> ProductionJob | None:
        jobs = self.find_all()
        return jobs[0] if jobs else None

    def count(self) -> int:
        return len(self._read())
