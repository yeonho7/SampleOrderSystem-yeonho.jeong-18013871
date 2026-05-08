from datetime import datetime
from pathlib import Path

from model.production_job import ProductionJob
from repository.base_repository import BaseRepository


class ProductionJobRepository(BaseRepository):
    _id_key = "order_id"

    def _to_dict(self, job: ProductionJob) -> dict:
        return {
            "order_id": job.order_id,
            "sample_id": job.sample_id,
            "shortage": job.shortage,
            "actual_production": job.actual_production,
            "total_time": job.total_time,
            "enqueued_at": job.enqueued_at.isoformat(),
        }

    def _from_dict(self, item: dict) -> ProductionJob:
        job = ProductionJob(
            order_id=item["order_id"],
            sample_id=item["sample_id"],
            shortage=item["shortage"],
            actual_production=item["actual_production"],
            total_time=item["total_time"],
        )
        job.enqueued_at = datetime.fromisoformat(item["enqueued_at"])
        return job

    def find_all(self) -> list[ProductionJob]:
        jobs = [self._from_dict(item) for item in self._read()]
        jobs.sort(key=lambda j: j.enqueued_at)
        return jobs

    def find_first(self) -> ProductionJob | None:
        jobs = self.find_all()
        return jobs[0] if jobs else None

    def count(self) -> int:
        return len(self._read())
