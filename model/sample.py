from dataclasses import dataclass

@dataclass
class Sample:
    sample_id: str
    name: str
    avg_production_time: float  # min/ea
    yield_rate: float           # 0.0~1.0
    stock: int

    def __repr__(self) -> str:
        return f"Sample(id={self.sample_id!r}, name={self.name!r}, stock={self.stock})"
