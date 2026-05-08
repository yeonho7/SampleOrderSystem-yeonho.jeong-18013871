from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ProductionJob:
    order_id: str
    sample_id: str
    shortage: int
    actual_production: int
    total_time: float
    enqueued_at: datetime = field(default_factory=datetime.now)

    def __repr__(self) -> str:
        return (
            f"ProductionJob(order={self.order_id!r}, sample={self.sample_id!r}, "
            f"shortage={self.shortage}, actual={self.actual_production})"
        )
