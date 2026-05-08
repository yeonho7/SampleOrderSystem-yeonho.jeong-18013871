import pytest
from repository.sample_repository import SampleRepository
from repository.order_repository import OrderRepository
from repository.production_job_repository import ProductionJobRepository
from model.sample import Sample
from model.order import Order, OrderStatus
from model.production_job import ProductionJob
from controller.production_controller import ProductionController


@pytest.fixture
def repos(tmp_data_dir):
    sample_repo = SampleRepository(tmp_data_dir / "samples.json")
    order_repo = OrderRepository(tmp_data_dir / "orders.json")
    job_repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
    return sample_repo, order_repo, job_repo


@pytest.fixture
def controller(repos):
    sample_repo, order_repo, job_repo = repos
    return ProductionController(sample_repo, order_repo, job_repo)


def _make_sample(sample_repo, sample_id="S-001", stock=0):
    sample = Sample(
        sample_id=sample_id,
        name="테스트 웨이퍼",
        avg_production_time=5.0,
        yield_rate=0.9,
        stock=stock,
    )
    sample_repo.create(sample)
    return sample


def _make_producing_order(order_repo, order_id, sample_id="S-001", quantity=5):
    order = Order(
        order_id=order_id,
        sample_id=sample_id,
        customer_name="고객A",
        quantity=quantity,
        status=OrderStatus.PRODUCING,
    )
    order_repo.create(order)
    return order


def _make_job(job_repo, order_id, sample_id="S-001", shortage=5, actual_production=7):
    job = ProductionJob(
        order_id=order_id,
        sample_id=sample_id,
        shortage=shortage,
        actual_production=actual_production,
        total_time=35.0,
    )
    job_repo.create(job)
    return job


# ── complete_current ──────────────────────────────────────────────────────────

def test_complete_current_sets_order_status_to_confirmed(controller, repos):
    sample_repo, order_repo, job_repo = repos
    _make_sample(sample_repo, stock=0)
    _make_producing_order(order_repo, "ORD-20260508-0001")
    _make_job(job_repo, "ORD-20260508-0001", actual_production=7)

    result = controller.complete_current()

    assert result.status == OrderStatus.CONFIRMED


def test_complete_current_increments_stock_by_actual_production(controller, repos):
    sample_repo, order_repo, job_repo = repos
    _make_sample(sample_repo, stock=0)
    _make_producing_order(order_repo, "ORD-20260508-0001")
    _make_job(job_repo, "ORD-20260508-0001", actual_production=7)

    controller.complete_current()

    sample = sample_repo.find_by_id("S-001")
    assert sample.stock == 7


def test_complete_current_deletes_job_from_repository(controller, repos):
    sample_repo, order_repo, job_repo = repos
    _make_sample(sample_repo, stock=0)
    _make_producing_order(order_repo, "ORD-20260508-0001")
    _make_job(job_repo, "ORD-20260508-0001", actual_production=7)

    controller.complete_current()

    assert job_repo.find_by_id("ORD-20260508-0001") is None


def test_complete_current_processes_fifo_order(controller, repos):
    sample_repo, order_repo, job_repo = repos
    _make_sample(sample_repo, stock=0)
    _make_producing_order(order_repo, "ORD-20260508-0001")
    _make_producing_order(order_repo, "ORD-20260508-0002")
    # FIFO: 먼저 등록된 job이 먼저 처리됨
    job1 = _make_job(job_repo, "ORD-20260508-0001", actual_production=5)
    _make_job(job_repo, "ORD-20260508-0002", actual_production=8)

    result = controller.complete_current()

    assert result.order_id == "ORD-20260508-0001"


def test_complete_current_raises_when_queue_is_empty(controller):
    with pytest.raises(ValueError, match="생산 중인 작업이 없습니다"):
        controller.complete_current()


# ── get_current ───────────────────────────────────────────────────────────────

def test_get_current_returns_first_job_in_queue(controller, repos):
    sample_repo, order_repo, job_repo = repos
    _make_sample(sample_repo, stock=0)
    _make_producing_order(order_repo, "ORD-20260508-0001")
    _make_producing_order(order_repo, "ORD-20260508-0002")
    _make_job(job_repo, "ORD-20260508-0001")
    _make_job(job_repo, "ORD-20260508-0002")

    result = controller.get_current()

    assert result is not None
    assert result.order_id == "ORD-20260508-0001"


def test_get_current_returns_none_when_queue_is_empty(controller):
    result = controller.get_current()

    assert result is None


# ── get_queue ─────────────────────────────────────────────────────────────────

def test_get_queue_returns_jobs_after_first(controller, repos):
    sample_repo, order_repo, job_repo = repos
    _make_sample(sample_repo, stock=0)
    for i in range(1, 4):
        _make_producing_order(order_repo, f"ORD-20260508-000{i}")
        _make_job(job_repo, f"ORD-20260508-000{i}")

    result = controller.get_queue()

    # 첫 번째를 제외한 2개가 반환되어야 함
    assert len(result) == 2
    assert result[0].order_id == "ORD-20260508-0002"
    assert result[1].order_id == "ORD-20260508-0003"


def test_get_queue_returns_empty_when_only_one_job(controller, repos):
    sample_repo, order_repo, job_repo = repos
    _make_sample(sample_repo, stock=0)
    _make_producing_order(order_repo, "ORD-20260508-0001")
    _make_job(job_repo, "ORD-20260508-0001")

    result = controller.get_queue()

    assert result == []


def test_get_queue_returns_empty_when_no_jobs(controller):
    result = controller.get_queue()

    assert result == []


# ── get_queue_size ────────────────────────────────────────────────────────────

def test_get_queue_size_returns_correct_count(controller, repos):
    sample_repo, order_repo, job_repo = repos
    _make_sample(sample_repo, stock=0)
    for i in range(1, 4):
        _make_producing_order(order_repo, f"ORD-20260508-000{i}")
        _make_job(job_repo, f"ORD-20260508-000{i}")

    result = controller.get_queue_size()

    assert result == 3


def test_get_queue_size_returns_zero_when_no_jobs(controller):
    result = controller.get_queue_size()

    assert result == 0


# ── find_job ──────────────────────────────────────────────────────────────────

def test_find_job_returns_job_when_exists(controller, repos):
    sample_repo, order_repo, job_repo = repos
    _make_sample(sample_repo, stock=0)
    _make_producing_order(order_repo, "ORD-20260508-0001")
    _make_job(job_repo, "ORD-20260508-0001", actual_production=5)

    result = controller.find_job("ORD-20260508-0001")

    assert result is not None
    assert result.order_id == "ORD-20260508-0001"


def test_find_job_returns_none_when_not_exists(controller):
    result = controller.find_job("ORD-99999999-0001")

    assert result is None
