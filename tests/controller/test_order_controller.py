import math
import re
import pytest
from datetime import date

from model.order import OrderStatus
from controller.order_controller import OrderController
from tests.helpers import make_sample


class TestOrderControllerReserve:

    def test_reserve_returns_order_with_reserved_status(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo)

        result = ctrl.reserve("S-001", "고객A", 3)

        assert result.status == OrderStatus.RESERVED

    def test_reserve_returns_order_with_correct_sample_and_customer(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo)

        result = ctrl.reserve("S-001", "고객A", 3)

        assert result.sample_id == "S-001"
        assert result.customer_name == "고객A"
        assert result.quantity == 3

    def test_reserve_order_id_format_matches_ORD_YYYYMMDD_NNNN(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo)

        result = ctrl.reserve("S-001", "고객A", 3)

        today_str = date.today().strftime("%Y%m%d")
        pattern = rf"^ORD-{today_str}-\d{{4}}$"
        assert re.match(pattern, result.order_id), (
            f"주문번호 형식 불일치: {result.order_id}"
        )

    def test_reserve_order_id_sequence_increments_within_same_day(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo)

        order1 = ctrl.reserve("S-001", "고객A", 1)
        order2 = ctrl.reserve("S-001", "고객B", 2)

        seq1 = int(order1.order_id.split("-")[-1])
        seq2 = int(order2.order_id.split("-")[-1])
        assert seq2 == seq1 + 1

    def test_reserve_raises_when_sample_id_not_registered(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)

        with pytest.raises(ValueError, match="등록되지 않은 시료 ID입니다"):
            ctrl.reserve("S-999", "고객A", 3)

    def test_reserve_persists_order_to_repository(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo)

        result = ctrl.reserve("S-001", "고객A", 3)

        assert order_repo.find_by_id(result.order_id) is not None


class TestOrderControllerApprove:

    def test_approve_confirms_order_when_stock_sufficient(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=10)
        order = ctrl.reserve("S-001", "고객A", 5)

        result = ctrl.approve(order.order_id)

        assert result.status == OrderStatus.CONFIRMED

    def test_approve_sets_producing_when_stock_insufficient(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=2)
        order = ctrl.reserve("S-001", "고객A", 5)

        result = ctrl.approve(order.order_id)

        assert result.status == OrderStatus.PRODUCING

    def test_approve_creates_production_job_when_stock_insufficient(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=2)
        order = ctrl.reserve("S-001", "고객A", 5)

        ctrl.approve(order.order_id)

        job = job_repo.find_by_id(order.order_id)
        assert job is not None

    def test_approve_production_job_shortage_is_correct(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=2)
        order = ctrl.reserve("S-001", "고객A", 5)

        ctrl.approve(order.order_id)

        job = job_repo.find_by_id(order.order_id)
        # shortage = 주문수량 - 재고 = 5 - 2 = 3
        assert job.shortage == 3

    def test_approve_production_job_actual_production_uses_yield_formula(self, repos):
        # shortage=5, yield_rate=0.8 → ceil(5 / (0.8 * 0.9)) = ceil(5 / 0.72) = ceil(6.944) = 7
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, yield_rate=0.8, stock=0)
        order = ctrl.reserve("S-001", "고객A", 5)

        ctrl.approve(order.order_id)

        job = job_repo.find_by_id(order.order_id)
        expected = math.ceil(5 / (0.8 * 0.9))
        assert job.actual_production == expected

    def test_approve_production_job_actual_production_boundary_exact_division(
        self, repos
    ):
        # shortage=9, yield_rate=1.0 → ceil(9 / (1.0 * 0.9)) = ceil(10.0) = 10
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, yield_rate=1.0, stock=0)
        order = ctrl.reserve("S-001", "고객A", 9)

        ctrl.approve(order.order_id)

        job = job_repo.find_by_id(order.order_id)
        expected = math.ceil(9 / (1.0 * 0.9))
        assert job.actual_production == expected

    def test_approve_production_job_total_time_is_correct(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)
        sample = make_sample(sample_repo, yield_rate=0.8, stock=0)
        order = ctrl.reserve("S-001", "고객A", 5)

        ctrl.approve(order.order_id)

        job = job_repo.find_by_id(order.order_id)
        expected_actual = math.ceil(5 / (0.8 * 0.9))
        assert job.total_time == sample.avg_production_time * expected_actual

    def test_approve_raises_when_order_not_in_reserved_status(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=10)
        order = ctrl.reserve("S-001", "고객A", 5)
        ctrl.approve(order.order_id)  # CONFIRMED 상태가 됨

        with pytest.raises(ValueError):
            ctrl.approve(order.order_id)

    def test_approve_raises_when_order_is_rejected(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=10)
        order = ctrl.reserve("S-001", "고객A", 5)
        ctrl.reject(order.order_id)  # REJECTED 상태가 됨

        with pytest.raises(ValueError):
            ctrl.approve(order.order_id)


class TestOrderControllerReject:

    def test_reject_sets_order_status_to_rejected(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=10)
        order = ctrl.reserve("S-001", "고객A", 5)

        result = ctrl.reject(order.order_id)

        assert result.status == OrderStatus.REJECTED

    def test_reject_raises_when_order_not_in_reserved_status(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=10)
        order = ctrl.reserve("S-001", "고객A", 5)
        ctrl.approve(order.order_id)  # CONFIRMED 상태가 됨

        with pytest.raises(ValueError):
            ctrl.reject(order.order_id)

    def test_reject_raises_when_order_already_rejected(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=10)
        order = ctrl.reserve("S-001", "고객A", 5)
        ctrl.reject(order.order_id)

        with pytest.raises(ValueError):
            ctrl.reject(order.order_id)


class TestOrderControllerRelease:

    def test_release_sets_order_status_to_release(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=10)
        order = ctrl.reserve("S-001", "고객A", 5)
        ctrl.approve(order.order_id)

        result = ctrl.release(order.order_id)

        assert result.status == OrderStatus.RELEASE

    def test_release_decrements_stock_by_order_quantity(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=10)
        order = ctrl.reserve("S-001", "고객A", 5)
        ctrl.approve(order.order_id)

        ctrl.release(order.order_id)

        sample = sample_repo.find_by_id("S-001")
        assert sample.stock == 5

    def test_release_raises_when_order_not_confirmed(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=10)
        order = ctrl.reserve("S-001", "고객A", 5)
        # RESERVED 상태에서 출고 시도

        with pytest.raises(ValueError):
            ctrl.release(order.order_id)

    def test_release_raises_when_order_is_rejected(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=10)
        order = ctrl.reserve("S-001", "고객A", 5)
        ctrl.reject(order.order_id)

        with pytest.raises(ValueError):
            ctrl.release(order.order_id)

    def test_release_raises_when_order_is_producing(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=0)
        order = ctrl.reserve("S-001", "고객A", 5)
        ctrl.approve(order.order_id)  # PRODUCING 상태

        with pytest.raises(ValueError):
            ctrl.release(order.order_id)


class TestOrderControllerList:

    def test_list_reserved_returns_only_reserved_orders(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=10)
        ctrl.reserve("S-001", "고객A", 1)
        ctrl.reserve("S-001", "고객B", 2)
        order_to_confirm = ctrl.reserve("S-001", "고객C", 3)
        ctrl.approve(order_to_confirm.order_id)  # CONFIRMED 상태

        result = ctrl.list_reserved()

        assert all(o.status == OrderStatus.RESERVED for o in result)
        assert len(result) == 2

    def test_list_confirmed_returns_only_confirmed_orders(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = OrderController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=10)
        ctrl.reserve("S-001", "고객A", 1)  # RESERVED 상태로 남김
        order1 = ctrl.reserve("S-001", "고객B", 2)
        order2 = ctrl.reserve("S-001", "고객C", 3)
        ctrl.approve(order1.order_id)
        ctrl.approve(order2.order_id)

        result = ctrl.list_confirmed()

        assert all(o.status == OrderStatus.CONFIRMED for o in result)
        assert len(result) == 2
