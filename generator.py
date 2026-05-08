import random
import sys
from math import ceil
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from model.sample import Sample
from model.order import Order, OrderStatus
from model.production_job import ProductionJob
from repository.sample_repository import SampleRepository
from repository.order_repository import OrderRepository
from repository.production_job_repository import ProductionJobRepository

SEED = 42
DATA_DIR = Path(__file__).parent / "data"

SAMPLES_DATA = [
    Sample("S-001", "실리콘 웨이퍼-8인치", 2.5, 0.92, 150),
    Sample("S-002", "GaAs 기판-2인치",     3.2, 0.88,  80),
    Sample("S-003", "SiC 웨이퍼-4인치",    4.1, 0.85,  30),
    Sample("S-004", "InP 기판-3인치",      5.0, 0.90,   0),
    Sample("S-005", "Ge 웨이퍼-6인치",     1.8, 0.95, 200),
]

STATUS_DISTRIBUTION = (
    [OrderStatus.RESERVED]  * 5 +
    [OrderStatus.REJECTED]  * 3 +
    [OrderStatus.PRODUCING] * 4 +
    [OrderStatus.CONFIRMED] * 8 +
    [OrderStatus.RELEASE]   * 5
)

BASE_DATE = datetime(2026, 1, 1)
ORDER_DATE_STR = "20260101"


def main():
    DATA_DIR.mkdir(exist_ok=True)
    for fname in ("samples.json", "orders.json", "production_jobs.json"):
        (DATA_DIR / fname).write_text("[]", encoding="utf-8")

    sample_repo = SampleRepository(DATA_DIR / "samples.json")
    order_repo = OrderRepository(DATA_DIR / "orders.json")
    job_repo = ProductionJobRepository(DATA_DIR / "production_jobs.json")

    for sample in SAMPLES_DATA:
        sample_repo.create(sample)

    sample_map = {s.sample_id: s for s in SAMPLES_DATA}

    rng = random.Random(SEED)
    statuses = STATUS_DISTRIBUTION[:]

    producing_orders = []
    for i in range(25):
        order_id = f"ORD-{ORDER_DATE_STR}-{i + 1:04d}"
        customer_name = f"고객-{i + 1:02d}"
        quantity = rng.randint(5, 50)
        sample_id = rng.choice(["S-001", "S-002", "S-003", "S-004", "S-005"])
        days_offset = rng.randint(0, 30)
        created_at = BASE_DATE + timedelta(days=days_offset)
        status = statuses[i]

        order = Order(
            order_id=order_id,
            sample_id=sample_id,
            customer_name=customer_name,
            quantity=quantity,
            status=status,
            created_at=created_at,
            updated_at=created_at,
        )
        order_repo.create(order)

        if status == OrderStatus.PRODUCING:
            producing_orders.append(order)

    job_count = 0
    for order in producing_orders:
        sample = sample_map[order.sample_id]
        shortage = max(0, order.quantity - sample.stock)
        actual_production = ceil(shortage / (sample.yield_rate * 0.9))
        total_time = sample.avg_production_time * actual_production
        enqueued_at = order.created_at + timedelta(hours=1)

        job = ProductionJob(
            order_id=order.order_id,
            sample_id=order.sample_id,
            shortage=shortage,
            actual_production=actual_production,
            total_time=total_time,
            enqueued_at=enqueued_at,
        )
        job_repo.create(job)
        job_count += 1

    print(f"더미 데이터 생성 완료: 시료 5종, 주문 25건, 생산작업 {job_count}건")


if __name__ == "__main__":
    main()
