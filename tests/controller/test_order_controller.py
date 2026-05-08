import math
import re
import pytest
from datetime import date

from repository.sample_repository import SampleRepository
from repository.order_repository import OrderRepository
from repository.production_job_repository import ProductionJobRepository
from model.sample import Sample
from model.order import Order, OrderStatus
from controller.order_controller import OrderController


@pytest.fixture
def repos(tmp_data_dir):
    sample_repo = SampleRepository(tmp_data_dir / "samples.json")
    order_repo = OrderRepository(tmp_data_dir / "orders.json")
    job_repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
    return sample_repo, order_repo, job_repo


@pytest.fixture
def controller(repos):
    sample_repo, order_repo, job_repo = repos
    return OrderController(sample_repo, order_repo, job_repo)


def _register_sample(sample_repo, sample_id="S-001", yield_rate=0.9, stock=10):
    sample = Sample(
        sample_id=sample_id,
        name="테스트 웨이퍼",
        avg_production_time=5.0,
        yield_rate=yield_rate,
        stock=stock,
    )
    sample_repo.create(sample)
    return sample


# ── reserve ───────────────────────────────────────────────────────────────────

def test_reserve_returns_order_with_reserved_status(controller, repos):
    _register_sample(repos[0])

    result = controller.reserve("S-001", "고객A", 3)

    assert result.status == OrderStatus.RESERVED


def test_reserve_returns_order_with_correct_sample_and_customer(controller, repos):
    _register_sample(repos[0])

    result = controller.reserve("S-001", "고객A", 3)

    assert result.sample_id == "S-001"
    assert result.customer_name == "고객A"
    assert result.quantity == 3


def test_reserve_order_id_format_matches_ORD_YYYYMMDD_NNNN(controller, repos):
    _register_sample(repos[0])

    result = controller.reserve("S-001", "고객A", 3)

    today_str = date.today().strftime("%Y%m%d")
    pattern = rf"^ORD-{today_str}-\d{{4}}$"
    assert re.match(pattern, result.order_id), (
        f"주문번호 형식 불일치: {result.order_id}"
    )


def test_reserve_order_id_sequence_increments_within_same_day(controller, repos):
    _register_sample(repos[0])

    order1 = controller.reserve("S-001", "고객A", 1)
    order2 = controller.reserve("S-001", "고객B", 2)

    seq1 = int(order1.order_id.split("-")[-1])
    seq2 = int(order2.order_id.split("-")[-1])
    assert seq2 == seq1 + 1


def test_reserve_raises_when_sample_id_not_registered(controller):
    with pytest.raises(ValueError, match="등록되지 않은 시료 ID입니다"):
        controller.reserve("S-999", "고객A", 3)


def test_reserve_persists_order_to_repository(controller, repos):
    sample_repo, order_repo, _ = repos
    _register_sample(sample_repo)

    result = controller.reserve("S-001", "고객A", 3)

    assert order_repo.find_by_id(result.order_id) is not None


# ── approve ───────────────────────────────────────────────────────────────────

def test_approve_confirms_order_when_stock_sufficient(controller, repos):
    _register_sample(repos[0], stock=10)
    order = controller.reserve("S-001", "고객A", 5)

    result = controller.approve(order.order_id)

    assert result.status == OrderStatus.CONFIRMED


def test_approve_sets_producing_when_stock_insufficient(controller, repos):
    _register_sample(repos[0], stock=2)
    order = controller.reserve("S-001", "고객A", 5)

    result = controller.approve(order.order_id)

    assert result.status == OrderStatus.PRODUCING


def test_approve_creates_production_job_when_stock_insufficient(controller, repos):
    sample_repo, order_repo, job_repo = repos
    _register_sample(sample_repo, stock=2)
    order = controller.reserve("S-001", "고객A", 5)

    controller.approve(order.order_id)

    job = job_repo.find_by_id(order.order_id)
    assert job is not None


def test_approve_production_job_shortage_is_correct(controller, repos):
    sample_repo, order_repo, job_repo = repos
    _register_sample(sample_repo, stock=2)
    order = controller.reserve("S-001", "고객A", 5)

    controller.approve(order.order_id)

    job = job_repo.find_by_id(order.order_id)
    # shortage = 주문수량 - 재고 = 5 - 2 = 3
    assert job.shortage == 3


def test_approve_production_job_actual_production_uses_yield_formula(controller, repos):
    # shortage=5, yield_rate=0.8 → ceil(5 / (0.8 * 0.9)) = ceil(5 / 0.72) = ceil(6.944) = 7
    sample_repo, order_repo, job_repo = repos
    _register_sample(sample_repo, yield_rate=0.8, stock=0)
    order = controller.reserve("S-001", "고객A", 5)

    controller.approve(order.order_id)

    job = job_repo.find_by_id(order.order_id)
    expected = math.ceil(5 / (0.8 * 0.9))
    assert job.actual_production == expected


def test_approve_production_job_actual_production_boundary_exact_division(
    controller, repos
):
    # shortage=9, yield_rate=1.0 → ceil(9 / (1.0 * 0.9)) = ceil(10.0) = 10
    sample_repo, order_repo, job_repo = repos
    _register_sample(sample_repo, yield_rate=1.0, stock=0)
    order = controller.reserve("S-001", "고객A", 9)

    controller.approve(order.order_id)

    job = job_repo.find_by_id(order.order_id)
    expected = math.ceil(9 / (1.0 * 0.9))
    assert job.actual_production == expected


def test_approve_production_job_total_time_is_correct(controller, repos):
    sample_repo, order_repo, job_repo = repos
    sample = _register_sample(sample_repo, yield_rate=0.8, stock=0)
    order = controller.reserve("S-001", "고객A", 5)

    controller.approve(order.order_id)

    job = job_repo.find_by_id(order.order_id)
    expected_actual = math.ceil(5 / (0.8 * 0.9))
    assert job.total_time == sample.avg_production_time * expected_actual


def test_approve_raises_when_order_not_in_reserved_status(controller, repos):
    _register_sample(repos[0], stock=10)
    order = controller.reserve("S-001", "고객A", 5)
    controller.approve(order.order_id)  # CONFIRMED 상태가 됨

    with pytest.raises(ValueError):
        controller.approve(order.order_id)


def test_approve_raises_when_order_is_rejected(controller, repos):
    _register_sample(repos[0], stock=10)
    order = controller.reserve("S-001", "고객A", 5)
    controller.reject(order.order_id)  # REJECTED 상태가 됨

    with pytest.raises(ValueError):
        controller.approve(order.order_id)


# ── reject ────────────────────────────────────────────────────────────────────

def test_reject_sets_order_status_to_rejected(controller, repos):
    _register_sample(repos[0], stock=10)
    order = controller.reserve("S-001", "고객A", 5)

    result = controller.reject(order.order_id)

    assert result.status == OrderStatus.REJECTED


def test_reject_raises_when_order_not_in_reserved_status(controller, repos):
    _register_sample(repos[0], stock=10)
    order = controller.reserve("S-001", "고객A", 5)
    controller.approve(order.order_id)  # CONFIRMED 상태가 됨

    with pytest.raises(ValueError):
        controller.reject(order.order_id)


def test_reject_raises_when_order_already_rejected(controller, repos):
    _register_sample(repos[0], stock=10)
    order = controller.reserve("S-001", "고객A", 5)
    controller.reject(order.order_id)

    with pytest.raises(ValueError):
        controller.reject(order.order_id)


# ── release ───────────────────────────────────────────────────────────────────

def test_release_sets_order_status_to_release(controller, repos):
    _register_sample(repos[0], stock=10)
    order = controller.reserve("S-001", "고객A", 5)
    controller.approve(order.order_id)

    result = controller.release(order.order_id)

    assert result.status == OrderStatus.RELEASE


def test_release_decrements_stock_by_order_quantity(controller, repos):
    sample_repo, order_repo, _ = repos
    _register_sample(sample_repo, stock=10)
    order = controller.reserve("S-001", "고객A", 5)
    controller.approve(order.order_id)

    controller.release(order.order_id)

    sample = sample_repo.find_by_id("S-001")
    assert sample.stock == 5


def test_release_raises_when_order_not_confirmed(controller, repos):
    _register_sample(repos[0], stock=10)
    order = controller.reserve("S-001", "고객A", 5)
    # RESERVED 상태에서 출고 시도

    with pytest.raises(ValueError):
        controller.release(order.order_id)


def test_release_raises_when_order_is_rejected(controller, repos):
    _register_sample(repos[0], stock=10)
    order = controller.reserve("S-001", "고객A", 5)
    controller.reject(order.order_id)

    with pytest.raises(ValueError):
        controller.release(order.order_id)


def test_release_raises_when_order_is_producing(controller, repos):
    _register_sample(repos[0], stock=0)
    order = controller.reserve("S-001", "고객A", 5)
    controller.approve(order.order_id)  # PRODUCING 상태

    with pytest.raises(ValueError):
        controller.release(order.order_id)


# ── list_reserved / list_confirmed ───────────────────────────────────────────

def test_list_reserved_returns_only_reserved_orders(controller, repos):
    _register_sample(repos[0], stock=10)
    controller.reserve("S-001", "고객A", 1)
    controller.reserve("S-001", "고객B", 2)
    order_to_confirm = controller.reserve("S-001", "고객C", 3)
    controller.approve(order_to_confirm.order_id)  # CONFIRMED 상태

    result = controller.list_reserved()

    assert all(o.status == OrderStatus.RESERVED for o in result)
    assert len(result) == 2


def test_list_confirmed_returns_only_confirmed_orders(controller, repos):
    _register_sample(repos[0], stock=10)
    controller.reserve("S-001", "고객A", 1)  # RESERVED 상태로 남김
    order1 = controller.reserve("S-001", "고객B", 2)
    order2 = controller.reserve("S-001", "고객C", 3)
    controller.approve(order1.order_id)
    controller.approve(order2.order_id)

    result = controller.list_confirmed()

    assert all(o.status == OrderStatus.CONFIRMED for o in result)
    assert len(result) == 2
