from dataclasses import dataclass

@dataclass
class Sample:
    sample_id: str
    name: str
    avg_production_time: float  # min/ea
    yield_rate: float           # 0.0~1.0
    stock: int
