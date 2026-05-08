from datetime import datetime

from model.order import Order, OrderStatus
from model.production_job import ProductionJob
from model.sample import Sample


def make_sample(repo, sample_id="S-001", name="테스트 웨이퍼",
                avg_production_time=5.0, yield_rate=0.9, stock=10) -> Sample:
    sample = Sample(
        sample_id=sample_id, name=name,
        avg_production_time=avg_production_time,
        yield_rate=yield_rate, stock=stock,
    )
    repo.create(sample)
    return sample


def make_order(repo, order_id, sample_id="S-001", customer_name="고객A",
               quantity=3, status=OrderStatus.RESERVED) -> Order:
    order = Order(
        order_id=order_id, sample_id=sample_id,
        customer_name=customer_name, quantity=quantity, status=status,
    )
    repo.create(order)
    return order


def make_job(repo, order_id, sample_id="S-001",
             shortage=5, actual_production=7, total_time=35.0) -> ProductionJob:
    job = ProductionJob(
        order_id=order_id, sample_id=sample_id,
        shortage=shortage, actual_production=actual_production,
        total_time=total_time,
    )
    repo.create(job)
    return job
