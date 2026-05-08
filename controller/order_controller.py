from math import ceil
from datetime import date, datetime
from model.order import Order, OrderStatus
from model.production_job import ProductionJob


class OrderController:
    def __init__(self, sample_repo, order_repo, job_repo):
        self._sample_repo = sample_repo
        self._order_repo = order_repo
        self._job_repo = job_repo

    def _generate_order_id(self) -> str:
        today_str = date.today().strftime("%Y%m%d")
        prefix = f"ORD-{today_str}-"
        count = sum(
            1 for o in self._order_repo.find_all()
            if o.order_id.startswith(prefix)
        )
        return f"{prefix}{count + 1:04d}"

    def reserve(self, sample_id, customer_name, quantity) -> Order:
        if self._sample_repo.find_by_id(sample_id) is None:
            raise ValueError("등록되지 않은 시료 ID입니다")
        if quantity <= 0:
            raise ValueError("주문 수량은 1 이상이어야 합니다")
        order = Order(
            order_id=self._generate_order_id(),
            sample_id=sample_id,
            customer_name=customer_name,
            quantity=quantity,
            status=OrderStatus.RESERVED,
        )
        self._order_repo.create(order)
        return order

    def approve(self, order_id: str) -> Order:
        order = self._order_repo.find_by_id(order_id)
        if order is None:
            raise ValueError("존재하지 않는 주문번호입니다")
        if not order.is_reserved():
            raise ValueError("RESERVED 상태의 주문만 승인할 수 있습니다")
        sample = self._sample_repo.find_by_id(order.sample_id)
        # 이미 CONFIRMED된 주문이 선점한 재고를 제외한 가용 재고로 판단
        committed = sum(
            o.quantity
            for o in self._order_repo.find_by_status(OrderStatus.CONFIRMED)
            if o.sample_id == order.sample_id
        )
        available = sample.stock - committed
        if available >= order.quantity:
            order.status = OrderStatus.CONFIRMED
        else:
            shortage = order.quantity - max(available, 0)
            actual_production = ceil(shortage / (sample.yield_rate * 0.9))
            total_time = sample.avg_production_time * actual_production
            job = ProductionJob(
                order_id=order.order_id,
                sample_id=order.sample_id,
                shortage=shortage,
                actual_production=actual_production,
                total_time=total_time,
            )
            self._job_repo.create(job)
            order.status = OrderStatus.PRODUCING
        order.updated_at = datetime.now()
        self._order_repo.update(order)
        return order

    def reject(self, order_id: str) -> Order:
        order = self._order_repo.find_by_id(order_id)
        if order is None:
            raise ValueError("존재하지 않는 주문번호입니다")
        if not order.is_reserved():
            raise ValueError("RESERVED 상태의 주문만 거절할 수 있습니다")
        order.status = OrderStatus.REJECTED
        order.updated_at = datetime.now()
        self._order_repo.update(order)
        return order

    def release(self, order_id: str) -> Order:
        order = self._order_repo.find_by_id(order_id)
        if order is None:
            raise ValueError("존재하지 않는 주문번호입니다")
        if not order.is_confirmed():
            raise ValueError("CONFIRMED 상태의 주문만 출고할 수 있습니다")
        sample = self._sample_repo.find_by_id(order.sample_id)
        if sample.stock < order.quantity:
            raise ValueError("재고가 부족합니다")
        sample.stock -= order.quantity
        self._sample_repo.update(sample)
        order.status = OrderStatus.RELEASE
        order.updated_at = datetime.now()
        self._order_repo.update(order)
        return order

    def list_reserved(self) -> list:
        return self._order_repo.find_by_status(OrderStatus.RESERVED)

    def list_confirmed(self) -> list:
        return self._order_repo.find_by_status(OrderStatus.CONFIRMED)
