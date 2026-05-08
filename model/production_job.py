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
