import json
from pathlib import Path

from model.order import Order, OrderStatus
from repository.base_repository import BaseRepository


def _order_to_dict(order: Order) -> dict:
    return {
        "order_id": order.order_id,
        "sample_id": order.sample_id,
        "customer_name": order.customer_name,
        "quantity": order.quantity,
        "status": order.status.value,
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
    }


def _dict_to_order(item: dict) -> Order:
    from datetime import datetime
    return Order(
        order_id=item["order_id"],
        sample_id=item["sample_id"],
        customer_name=item["customer_name"],
        quantity=item["quantity"],
        status=OrderStatus(item["status"]),
        created_at=datetime.fromisoformat(item["created_at"]),
        updated_at=datetime.fromisoformat(item["updated_at"]),
    )


class OrderRepository(BaseRepository):

    def __init__(self, filepath: Path):
        self._filepath = filepath

    def _read(self) -> list[dict]:
        return json.loads(self._filepath.read_text(encoding="utf-8"))

    def _write(self, data: list[dict]):
        self._filepath.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def create(self, order: Order) -> Order:
        data = self._read()
        data.append(_order_to_dict(order))
        self._write(data)
        return order

    def find_by_id(self, order_id: str) -> Order | None:
        for item in self._read():
            if item["order_id"] == order_id:
                return _dict_to_order(item)
        return None

    def find_all(self) -> list[Order]:
        return [_dict_to_order(item) for item in self._read()]

    def update(self, order: Order) -> bool:
        data = self._read()
        for i, item in enumerate(data):
            if item["order_id"] == order.order_id:
                data[i] = _order_to_dict(order)
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

    def find_by_status(self, status: OrderStatus) -> list[Order]:
        return [
            _dict_to_order(item)
            for item in self._read()
            if item["status"] == status.value
        ]

    def count_by_status(self, status: OrderStatus) -> int:
        return sum(1 for item in self._read() if item["status"] == status.value)
