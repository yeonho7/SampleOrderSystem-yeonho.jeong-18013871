import pytest
from datetime import datetime

from model.sample import Sample
from model.order import Order, OrderStatus
from model.production_job import ProductionJob

class TestSampleFields:

    def test_sample_stores_sample_id(self):
        sample = Sample(
            sample_id="S-001",
            name="실리콘 웨이퍼-8인치",
            avg_production_time=30.0,
            yield_rate=0.92,
            stock=100,
        )
        assert sample.sample_id == "S-001"

    def test_sample_stores_name(self):
        sample = Sample(
            sample_id="S-002",
            name="GaAs 기판",
            avg_production_time=45.0,
            yield_rate=0.85,
            stock=50,
        )
        assert sample.name == "GaAs 기판"

    def test_sample_stores_avg_production_time(self):
        sample = Sample(
            sample_id="S-003",
            name="SiC 웨이퍼",
            avg_production_time=60.5,
            yield_rate=0.90,
            stock=200,
        )
        assert sample.avg_production_time == 60.5

    def test_sample_stores_yield_rate(self):
        sample = Sample(
            sample_id="S-004",
            name="InP 기판",
            avg_production_time=20.0,
            yield_rate=0.78,
            stock=30,
        )
        assert sample.yield_rate == 0.78

    def test_sample_stores_stock(self):
        sample = Sample(
            sample_id="S-005",
            name="Ge 기판",
            avg_production_time=15.0,
            yield_rate=0.95,
            stock=0,
        )
        assert sample.stock == 0


class TestOrderStatusEnum:

    @pytest.mark.parametrize("status, expected", [
        (OrderStatus.RESERVED,  "RESERVED"),
        (OrderStatus.REJECTED,  "REJECTED"),
        (OrderStatus.PRODUCING, "PRODUCING"),
        (OrderStatus.CONFIRMED, "CONFIRMED"),
        (OrderStatus.RELEASE,   "RELEASE"),
    ])
    def test_order_status_values(self, status, expected):
        assert status.value == expected

    def test_order_status_count_is_five(self):
        assert len(OrderStatus) == 5



class TestOrderFields:

    def _make_order(self, **overrides):
        defaults = dict(
            order_id="ORD-20260508-0001",
            sample_id="S-001",
            customer_name="홍길동",
            quantity=10,
        )
        defaults.update(overrides)
        return Order(**defaults)

    def test_order_stores_order_id(self):
        order = self._make_order(order_id="ORD-20260508-0001")
        assert order.order_id == "ORD-20260508-0001"

    def test_order_stores_sample_id(self):
        order = self._make_order(sample_id="S-007")
        assert order.sample_id == "S-007"

    def test_order_stores_customer_name(self):
        order = self._make_order(customer_name="김철수")
        assert order.customer_name == "김철수"

    def test_order_stores_quantity(self):
        order = self._make_order(quantity=42)
        assert order.quantity == 42

    def test_order_default_status_is_reserved(self):
        """주문 생성 시 기본 상태는 반드시 RESERVED 여야 한다."""
        order = self._make_order()
        assert order.status == OrderStatus.RESERVED

    def test_order_status_can_be_set_explicitly(self):
        order = self._make_order(status=OrderStatus.CONFIRMED)
        assert order.status == OrderStatus.CONFIRMED

    def test_order_default_created_at_is_datetime(self):
        order = self._make_order()
        assert isinstance(order.created_at, datetime)

    def test_order_default_updated_at_is_datetime(self):
        order = self._make_order()
        assert isinstance(order.updated_at, datetime)

    def test_order_id_format_pattern(self):
        """주문번호는 ORD-YYYYMMDD-NNNN 형식이어야 한다."""
        order = self._make_order(order_id="ORD-20260508-0042")
        parts = order.order_id.split("-")
        assert parts[0] == "ORD"
        assert len(parts[1]) == 8   # YYYYMMDD
        assert len(parts[2]) == 4   # NNNN



class TestProductionJobFields:

    def _make_job(self, **overrides):
        defaults = dict(
            order_id="ORD-20260508-0001",
            sample_id="S-001",
            shortage=20,
            actual_production=25,
            total_time=750.0,
        )
        defaults.update(overrides)
        return ProductionJob(**defaults)

    def test_production_job_stores_order_id(self):
        job = self._make_job(order_id="ORD-20260508-0099")
        assert job.order_id == "ORD-20260508-0099"

    def test_production_job_stores_sample_id(self):
        job = self._make_job(sample_id="S-009")
        assert job.sample_id == "S-009"

    def test_production_job_stores_shortage(self):
        job = self._make_job(shortage=15)
        assert job.shortage == 15

    def test_production_job_stores_actual_production(self):
        job = self._make_job(actual_production=18)
        assert job.actual_production == 18

    def test_production_job_stores_total_time(self):
        job = self._make_job(total_time=540.0)
        assert job.total_time == 540.0

    def test_production_job_default_enqueued_at_is_datetime(self):
        job = self._make_job()
        assert isinstance(job.enqueued_at, datetime)

    def test_production_job_shortage_zero_is_valid(self):
        """부족분이 0인 경우도 유효한 ProductionJob 이어야 한다."""
        job = self._make_job(shortage=0, actual_production=0, total_time=0.0)
        assert job.shortage == 0

    def test_production_job_actual_production_formula_boundary(self):
        """
        부족분이 수율 × 0.9 로 정확히 나누어 떨어지는 경계값을 저장할 수 있어야 한다.
        실 생산량 계산은 Controller 책임이므로 여기서는 필드 저장만 확인한다.
        shortage=9, yield_rate=1.0 → ceil(9 / (1.0 × 0.9)) = ceil(10.0) = 10
        """
        job = self._make_job(shortage=9, actual_production=10)
        assert job.shortage == 9
        assert job.actual_production == 10



class TestOrderStatusHelpers:
    def test_is_pending_returns_true_for_reserved(self):
        assert OrderStatus.RESERVED.is_pending() is True

    def test_is_pending_returns_true_for_producing(self):
        assert OrderStatus.PRODUCING.is_pending() is True

    def test_is_pending_returns_false_for_confirmed(self):
        assert OrderStatus.CONFIRMED.is_pending() is False

    def test_is_pending_returns_false_for_rejected(self):
        assert OrderStatus.REJECTED.is_pending() is False

    def test_is_pending_returns_false_for_release(self):
        assert OrderStatus.RELEASE.is_pending() is False

    def test_is_rejected_returns_true_for_rejected(self):
        assert OrderStatus.REJECTED.is_rejected() is True

    def test_is_rejected_returns_false_for_reserved(self):
        assert OrderStatus.RESERVED.is_rejected() is False

    def test_is_rejected_returns_false_for_confirmed(self):
        assert OrderStatus.CONFIRMED.is_rejected() is False



class TestOrderHelpers:
    def _make_order(self, **overrides):
        defaults = dict(
            order_id="ORD-20260508-0001",
            sample_id="S-001",
            customer_name="테스트고객",
            quantity=10,
        )
        defaults.update(overrides)
        return Order(**defaults)

    def test_is_reserved_returns_true_when_reserved(self):
        order = self._make_order(status=OrderStatus.RESERVED)
        assert order.is_reserved() is True

    def test_is_reserved_returns_false_when_confirmed(self):
        order = self._make_order(status=OrderStatus.CONFIRMED)
        assert order.is_reserved() is False

    def test_is_confirmed_returns_true_when_confirmed(self):
        order = self._make_order(status=OrderStatus.CONFIRMED)
        assert order.is_confirmed() is True

    def test_is_confirmed_returns_false_when_reserved(self):
        order = self._make_order(status=OrderStatus.RESERVED)
        assert order.is_confirmed() is False



class TestModelRepr:
    def test_sample_repr_contains_sample_id(self):
        s = Sample(sample_id="S-001", name="실리콘 웨이퍼", avg_production_time=2.5, yield_rate=0.92, stock=100)
        assert "S-001" in repr(s)

    def test_sample_repr_contains_stock(self):
        s = Sample(sample_id="S-001", name="실리콘 웨이퍼", avg_production_time=2.5, yield_rate=0.92, stock=42)
        assert "42" in repr(s)

    def test_order_repr_contains_order_id(self):
        o = Order(order_id="ORD-20260508-0001", sample_id="S-001", customer_name="홍길동", quantity=10)
        assert "ORD-20260508-0001" in repr(o)

    def test_order_repr_contains_status(self):
        o = Order(order_id="ORD-20260508-0001", sample_id="S-001", customer_name="홍길동", quantity=10,
                  status=OrderStatus.CONFIRMED)
        assert "CONFIRMED" in repr(o)

    def test_production_job_repr_contains_order_id(self):
        job = ProductionJob(order_id="ORD-20260508-0001", sample_id="S-001",
                            shortage=5, actual_production=7, total_time=14.0)
        assert "ORD-20260508-0001" in repr(job)

    def test_production_job_repr_contains_shortage(self):
        job = ProductionJob(order_id="ORD-20260508-0001", sample_id="S-001",
                            shortage=5, actual_production=7, total_time=14.0)
        assert "5" in repr(job)
