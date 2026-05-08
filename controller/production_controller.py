from model.order import OrderStatus


class ProductionController:
    def __init__(self, sample_repo, order_repo, job_repo):
        self._sample_repo = sample_repo
        self._order_repo = order_repo
        self._job_repo = job_repo

    def complete_current(self):
        job = self._job_repo.find_first()
        if job is None:
            raise ValueError("생산 중인 작업이 없습니다")
        order = self._order_repo.find_by_id(job.order_id)
        sample = self._sample_repo.find_by_id(job.sample_id)
        sample.stock += job.actual_production
        self._sample_repo.update(sample)
        order.status = OrderStatus.CONFIRMED
        self._order_repo.update(order)
        self._job_repo.delete(job.order_id)
        return order

    def get_current(self):
        return self._job_repo.find_first()

    def get_queue(self) -> list:
        jobs = self._job_repo.find_all()
        return jobs[1:]

    def get_queue_size(self) -> int:
        return self._job_repo.count()

    def find_job(self, order_id: str):
        return self._job_repo.find_by_id(order_id)
