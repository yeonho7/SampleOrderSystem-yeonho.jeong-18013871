import pytest
from repository.sample_repository import SampleRepository
from repository.order_repository import OrderRepository
from repository.production_job_repository import ProductionJobRepository
from model.sample import Sample
from model.order import Order, OrderStatus
from controller.monitor_controller import MonitorController


@pytest.fixture
def repos(tmp_data_dir):
    sample_repo = SampleRepository(tmp_data_dir / "samples.json")
    order_repo = OrderRepository(tmp_data_dir / "orders.json")
    job_repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
    return sample_repo, order_repo, job_repo


@pytest.fixture
def controller(repos):
    sample_repo, order_repo, _ = repos
    return MonitorController(sample_repo, order_repo)


def _make_sample(sample_repo, sample_id="S-001", name="웨이퍼 A", stock=10):
    sample = Sample(
        sample_id=sample_id,
        name=name,
        avg_production_time=5.0,
        yield_rate=0.9,
        stock=stock,
    )
    sample_repo.create(sample)
    return sample


def _make_order(order_repo, order_id, sample_id="S-001", quantity=3, status=OrderStatus.RESERVED):
    order = Order(
        order_id=order_id,
        sample_id=sample_id,
        customer_name="고객A",
        quantity=quantity,
        status=status,
    )
    order_repo.create(order)
    return order


# ── get_order_stats ───────────────────────────────────────────────────────────

def test_get_order_stats_excludes_rejected_orders(controller, repos):
    _, order_repo, _ = repos
    _make_order(order_repo, "ORD-20260508-0001", status=OrderStatus.RESERVED)
    _make_order(order_repo, "ORD-20260508-0002", status=OrderStatus.REJECTED)

    result = controller.get_order_stats()

    assert OrderStatus.REJECTED not in result


def test_get_order_stats_counts_reserved_correctly(controller, repos):
    _, order_repo, _ = repos
    _make_order(order_repo, "ORD-20260508-0001", status=OrderStatus.RESERVED)
    _make_order(order_repo, "ORD-20260508-0002", status=OrderStatus.RESERVED)

    result = controller.get_order_stats()

    assert result[OrderStatus.RESERVED] == 2


def test_get_order_stats_counts_producing_correctly(controller, repos):
    _, order_repo, _ = repos
    _make_order(order_repo, "ORD-20260508-0001", status=OrderStatus.PRODUCING)

    result = controller.get_order_stats()

    assert result[OrderStatus.PRODUCING] == 1


def test_get_order_stats_counts_confirmed_correctly(controller, repos):
    _, order_repo, _ = repos
    _make_order(order_repo, "ORD-20260508-0001", status=OrderStatus.CONFIRMED)
    _make_order(order_repo, "ORD-20260508-0002", status=OrderStatus.CONFIRMED)

    result = controller.get_order_stats()

    assert result[OrderStatus.CONFIRMED] == 2


def test_get_order_stats_counts_release_correctly(controller, repos):
    _, order_repo, _ = repos
    _make_order(order_repo, "ORD-20260508-0001", status=OrderStatus.RELEASE)

    result = controller.get_order_stats()

    assert result[OrderStatus.RELEASE] == 1


def test_get_order_stats_returns_zero_for_empty_statuses(controller):
    result = controller.get_order_stats()

    assert result[OrderStatus.RESERVED] == 0
    assert result[OrderStatus.PRODUCING] == 0
    assert result[OrderStatus.CONFIRMED] == 0
    assert result[OrderStatus.RELEASE] == 0


def test_get_order_stats_includes_all_four_non_rejected_statuses(controller):
    result = controller.get_order_stats()

    expected_statuses = {
        OrderStatus.RESERVED,
        OrderStatus.PRODUCING,
        OrderStatus.CONFIRMED,
        OrderStatus.RELEASE,
    }
    assert expected_statuses.issubset(result.keys())


# ── get_stock_status_all ──────────────────────────────────────────────────────

def test_get_stock_status_all_returns_entry_for_each_sample(controller, repos):
    sample_repo, _, _ = repos
    _make_sample(sample_repo, "S-001", "웨이퍼 A", stock=5)
    _make_sample(sample_repo, "S-002", "웨이퍼 B", stock=3)

    result = controller.get_stock_status_all()

    assert len(result) == 2


def test_get_stock_status_all_returns_고갈_when_stock_zero(controller, repos):
    sample_repo, _, _ = repos
    _make_sample(sample_repo, "S-001", stock=0)

    result = controller.get_stock_status_all()

    entry = next(e for e in result if e["sample"].sample_id == "S-001")
    assert entry["status"] == "고갈"


def test_get_stock_status_all_returns_부족_when_stock_less_than_pending(
    controller, repos
):
    sample_repo, order_repo, _ = repos
    _make_sample(sample_repo, "S-001", stock=3)
    _make_order(order_repo, "ORD-20260508-0001", quantity=5, status=OrderStatus.RESERVED)

    result = controller.get_stock_status_all()

    entry = next(e for e in result if e["sample"].sample_id == "S-001")
    assert entry["status"] == "부족"


def test_get_stock_status_all_returns_여유_when_stock_sufficient(controller, repos):
    sample_repo, order_repo, _ = repos
    _make_sample(sample_repo, "S-001", stock=10)
    _make_order(order_repo, "ORD-20260508-0001", quantity=5, status=OrderStatus.RESERVED)

    result = controller.get_stock_status_all()

    entry = next(e for e in result if e["sample"].sample_id == "S-001")
    assert entry["status"] == "여유"


def test_get_stock_status_all_includes_producing_in_pending_calculation(
    controller, repos
):
    sample_repo, order_repo, _ = repos
    # stock=2, PRODUCING 주문 5 → 2 < 5 → 부족
    _make_sample(sample_repo, "S-001", stock=2)
    _make_order(order_repo, "ORD-20260508-0001", quantity=5, status=OrderStatus.PRODUCING)

    result = controller.get_stock_status_all()

    entry = next(e for e in result if e["sample"].sample_id == "S-001")
    assert entry["status"] == "부족"


def test_get_stock_status_all_excludes_rejected_from_pending_calculation(
    controller, repos
):
    sample_repo, order_repo, _ = repos
    # stock=1, REJECTED 주문 10 → REJECTED 제외하면 미처리=0 → 여유
    _make_sample(sample_repo, "S-001", stock=1)
    _make_order(order_repo, "ORD-20260508-0001", quantity=10, status=OrderStatus.REJECTED)

    result = controller.get_stock_status_all()

    entry = next(e for e in result if e["sample"].sample_id == "S-001")
    assert entry["status"] == "여유"


def test_get_stock_status_all_entry_contains_sample_object(controller, repos):
    sample_repo, _, _ = repos
    _make_sample(sample_repo, "S-001", stock=5)

    result = controller.get_stock_status_all()

    assert isinstance(result[0]["sample"], Sample)


# ── get_summary ───────────────────────────────────────────────────────────────

def test_get_summary_returns_correct_sample_count(controller, repos):
    sample_repo, _, _ = repos
    _make_sample(sample_repo, "S-001", "웨이퍼 A")
    _make_sample(sample_repo, "S-002", "웨이퍼 B")

    result = controller.get_summary()

    assert result["sample_count"] == 2


def test_get_summary_returns_correct_total_stock(controller, repos):
    sample_repo, _, _ = repos
    _make_sample(sample_repo, "S-001", stock=7)
    _make_sample(sample_repo, "S-002", stock=3)

    result = controller.get_summary()

    assert result["total_stock"] == 10


def test_get_summary_excludes_rejected_from_order_count(controller, repos):
    sample_repo, order_repo, _ = repos
    _make_sample(sample_repo, "S-001")
    _make_order(order_repo, "ORD-20260508-0001", status=OrderStatus.RESERVED)
    _make_order(order_repo, "ORD-20260508-0002", status=OrderStatus.REJECTED)
    _make_order(order_repo, "ORD-20260508-0003", status=OrderStatus.CONFIRMED)

    result = controller.get_summary()

    assert result["order_count"] == 2


def test_get_summary_queue_size_counts_producing_orders(controller, repos):
    sample_repo, order_repo, _ = repos
    _make_sample(sample_repo, "S-001")
    _make_order(order_repo, "ORD-20260508-0001", status=OrderStatus.PRODUCING)
    _make_order(order_repo, "ORD-20260508-0002", status=OrderStatus.PRODUCING)
    _make_order(order_repo, "ORD-20260508-0003", status=OrderStatus.CONFIRMED)

    result = controller.get_summary()

    assert result["queue_size"] == 2


def test_get_summary_returns_zero_when_no_data(controller):
    result = controller.get_summary()

    assert result["sample_count"] == 0
    assert result["total_stock"] == 0
    assert result["order_count"] == 0
    assert result["queue_size"] == 0


def test_get_summary_contains_all_required_keys(controller):
    result = controller.get_summary()

    assert "sample_count" in result
    assert "total_stock" in result
    assert "order_count" in result
    assert "queue_size" in result
