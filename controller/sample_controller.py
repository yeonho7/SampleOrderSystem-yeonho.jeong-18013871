from model.sample import Sample
from model.order import OrderStatus
from repository.sample_repository import SampleRepository
from repository.order_repository import OrderRepository


class SampleController:
    def __init__(self, sample_repo: SampleRepository, order_repo: OrderRepository):
        self._sample_repo = sample_repo
        self._order_repo = order_repo

    def register(self, sample_id, name, avg_production_time, yield_rate, stock=0) -> Sample:
        if self._sample_repo.find_by_id(sample_id) is not None:
            raise ValueError("이미 등록된 시료 ID입니다")
        sample = Sample(
            sample_id=sample_id,
            name=name,
            avg_production_time=avg_production_time,
            yield_rate=yield_rate,
            stock=stock,
        )
        self._sample_repo.create(sample)
        return sample

    def find_by_id(self, sample_id: str):
        return self._sample_repo.find_by_id(sample_id)

    def find_all(self) -> list:
        return self._sample_repo.find_all()

    def search(self, keyword: str) -> list:
        return self._sample_repo.find_by_name(keyword)

    def get_stock_status(self, sample_id: str) -> str:
        sample = self._sample_repo.find_by_id(sample_id)
        if sample.stock == 0:
            return "고갈"
        pending_statuses = (OrderStatus.RESERVED, OrderStatus.PRODUCING)
        pending_quantity = sum(
            o.quantity
            for o in self._order_repo.find_all()
            if o.sample_id == sample_id and o.status in pending_statuses
        )
        if sample.stock < pending_quantity:
            return "부족"
        return "여유"
