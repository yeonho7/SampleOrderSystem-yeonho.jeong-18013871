from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class OrderStatus(Enum):
    RESERVED = "RESERVED"
    REJECTED = "REJECTED"
    PRODUCING = "PRODUCING"
    CONFIRMED = "CONFIRMED"
    RELEASE = "RELEASE"

    def is_pending(self) -> bool:
        return self in (OrderStatus.RESERVED, OrderStatus.PRODUCING)

    def is_rejected(self) -> bool:
        return self == OrderStatus.REJECTED


@dataclass
class Order:
    order_id: str
    sample_id: str
    customer_name: str
    quantity: int
    status: OrderStatus = OrderStatus.RESERVED
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def is_reserved(self) -> bool:
        return self.status == OrderStatus.RESERVED

    def is_confirmed(self) -> bool:
        return self.status == OrderStatus.CONFIRMED

    def __repr__(self) -> str:
        return (
            f"Order(id={self.order_id!r}, sample={self.sample_id!r}, "
            f"qty={self.quantity}, status={self.status.value})"
        )
