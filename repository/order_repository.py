from datetime import datetime
from pathlib import Path

from model.order import Order, OrderStatus
from repository.base_repository import BaseRepository


class OrderRepository(BaseRepository):
    _id_key = "order_id"

    def _to_dict(self, order: Order) -> dict:
        return {
            "order_id": order.order_id,
            "sample_id": order.sample_id,
            "customer_name": order.customer_name,
            "quantity": order.quantity,
            "status": order.status.value,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat(),
        }

    def _from_dict(self, item: dict) -> Order:
        return Order(
            order_id=item["order_id"],
            sample_id=item["sample_id"],
            customer_name=item["customer_name"],
            quantity=item["quantity"],
            status=OrderStatus(item["status"]),
            created_at=datetime.fromisoformat(item["created_at"]),
            updated_at=datetime.fromisoformat(item["updated_at"]),
        )

    def find_by_status(self, status: OrderStatus) -> list[Order]:
        return [
            self._from_dict(item)
            for item in self._read()
            if item["status"] == status.value
        ]

    def count_by_status(self, status: OrderStatus) -> int:
        return sum(1 for item in self._read() if item["status"] == status.value)
