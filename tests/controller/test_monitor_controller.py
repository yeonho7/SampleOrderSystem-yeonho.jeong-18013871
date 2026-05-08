import pytest
from model.sample import Sample
from model.order import OrderStatus
from controller.monitor_controller import MonitorController
from tests.helpers import make_sample, make_order, make_job


class TestMonitorControllerOrderStats:

    def test_get_order_stats_excludes_rejected_orders(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = MonitorController(sample_repo, order_repo, job_repo)
        make_order(order_repo, "ORD-20260508-0001", status=OrderStatus.RESERVED)
        make_order(order_repo, "ORD-20260508-0002", status=OrderStatus.REJECTED)

        result = ctrl.get_order_stats()

        assert OrderStatus.REJECTED not in result

    def test_get_order_stats_counts_reserved_correctly(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = MonitorController(sample_repo, order_repo, job_repo)
        make_order(order_repo, "ORD-20260508-0001", status=OrderStatus.RESERVED)
        make_order(order_repo, "ORD-20260508-0002", status=OrderStatus.RESERVED)

        result = ctrl.get_order_stats()

        assert result[OrderStatus.RESERVED] == 2

    def test_get_order_stats_counts_producing_correctly(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = MonitorController(sample_repo, order_repo, job_repo)
        make_order(order_repo, "ORD-20260508-0001", status=OrderStatus.PRODUCING)

        result = ctrl.get_order_stats()

        assert result[OrderStatus.PRODUCING] == 1

    def test_get_order_stats_counts_confirmed_correctly(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = MonitorController(sample_repo, order_repo, job_repo)
        make_order(order_repo, "ORD-20260508-0001", status=OrderStatus.CONFIRMED)
        make_order(order_repo, "ORD-20260508-0002", status=OrderStatus.CONFIRMED)

        result = ctrl.get_order_stats()

        assert result[OrderStatus.CONFIRMED] == 2

    def test_get_order_stats_counts_release_correctly(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = MonitorController(sample_repo, order_repo, job_repo)
        make_order(order_repo, "ORD-20260508-0001", status=OrderStatus.RELEASE)

        result = ctrl.get_order_stats()

        assert result[OrderStatus.RELEASE] == 1

    def test_get_order_stats_returns_zero_for_empty_statuses(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = MonitorController(sample_repo, order_repo, job_repo)

        result = ctrl.get_order_stats()

        assert result[OrderStatus.RESERVED] == 0
        assert result[OrderStatus.PRODUCING] == 0
        assert result[OrderStatus.CONFIRMED] == 0
        assert result[OrderStatus.RELEASE] == 0

    def test_get_order_stats_includes_all_four_non_rejected_statuses(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = MonitorController(sample_repo, order_repo, job_repo)

        result = ctrl.get_order_stats()

        expected_statuses = {
            OrderStatus.RESERVED,
            OrderStatus.PRODUCING,
            OrderStatus.CONFIRMED,
            OrderStatus.RELEASE,
        }
        assert expected_statuses.issubset(result.keys())


class TestMonitorControllerStockStatus:

    def test_get_stock_status_all_returns_entry_for_each_sample(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = MonitorController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, "S-001", "웨이퍼 A", stock=5)
        make_sample(sample_repo, "S-002", "웨이퍼 B", stock=3)

        result = ctrl.get_stock_status_all()

        assert len(result) == 2

    def test_get_stock_status_all_returns_고갈_when_stock_zero(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = MonitorController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, "S-001", stock=0)

        result = ctrl.get_stock_status_all()

        entry = next(e for e in result if e["sample"].sample_id == "S-001")
        assert entry["status"] == "고갈"

    def test_get_stock_status_all_returns_부족_when_stock_less_than_pending(
        self, repos
    ):
        sample_repo, order_repo, job_repo = repos
        ctrl = MonitorController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, "S-001", stock=3)
        make_order(order_repo, "ORD-20260508-0001", quantity=5, status=OrderStatus.RESERVED)

        result = ctrl.get_stock_status_all()

        entry = next(e for e in result if e["sample"].sample_id == "S-001")
        assert entry["status"] == "부족"

    def test_get_stock_status_all_returns_여유_when_stock_sufficient(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = MonitorController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, "S-001", stock=10)
        make_order(order_repo, "ORD-20260508-0001", quantity=5, status=OrderStatus.RESERVED)

        result = ctrl.get_stock_status_all()

        entry = next(e for e in result if e["sample"].sample_id == "S-001")
        assert entry["status"] == "여유"

    def test_get_stock_status_all_includes_producing_in_pending_calculation(
        self, repos
    ):
        sample_repo, order_repo, job_repo = repos
        ctrl = MonitorController(sample_repo, order_repo, job_repo)
        # stock=2, PRODUCING 주문 5 → 2 < 5 → 부족
        make_sample(sample_repo, "S-001", stock=2)
        make_order(order_repo, "ORD-20260508-0001", quantity=5, status=OrderStatus.PRODUCING)

        result = ctrl.get_stock_status_all()

        entry = next(e for e in result if e["sample"].sample_id == "S-001")
        assert entry["status"] == "부족"

    def test_get_stock_status_all_excludes_rejected_from_pending_calculation(
        self, repos
    ):
        sample_repo, order_repo, job_repo = repos
        ctrl = MonitorController(sample_repo, order_repo, job_repo)
        # stock=1, REJECTED 주문 10 → REJECTED 제외하면 미처리=0 → 여유
        make_sample(sample_repo, "S-001", stock=1)
        make_order(order_repo, "ORD-20260508-0001", quantity=10, status=OrderStatus.REJECTED)

        result = ctrl.get_stock_status_all()

        entry = next(e for e in result if e["sample"].sample_id == "S-001")
        assert entry["status"] == "여유"

    def test_get_stock_status_all_entry_contains_sample_object(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = MonitorController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, "S-001", stock=5)

        result = ctrl.get_stock_status_all()

        assert isinstance(result[0]["sample"], Sample)


class TestMonitorControllerSummary:

    def test_get_summary_returns_correct_sample_count(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = MonitorController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, "S-001", "웨이퍼 A")
        make_sample(sample_repo, "S-002", "웨이퍼 B")

        result = ctrl.get_summary()

        assert result["sample_count"] == 2

    def test_get_summary_returns_correct_total_stock(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = MonitorController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, "S-001", stock=7)
        make_sample(sample_repo, "S-002", stock=3)

        result = ctrl.get_summary()

        assert result["total_stock"] == 10

    def test_get_summary_excludes_rejected_from_order_count(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = MonitorController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, "S-001")
        make_order(order_repo, "ORD-20260508-0001", status=OrderStatus.RESERVED)
        make_order(order_repo, "ORD-20260508-0002", status=OrderStatus.REJECTED)
        make_order(order_repo, "ORD-20260508-0003", status=OrderStatus.CONFIRMED)

        result = ctrl.get_summary()

        assert result["order_count"] == 2

    def test_get_summary_queue_size_counts_producing_orders(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = MonitorController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, "S-001")
        make_order(order_repo, "ORD-20260508-0001", status=OrderStatus.PRODUCING)
        make_order(order_repo, "ORD-20260508-0002", status=OrderStatus.PRODUCING)
        make_order(order_repo, "ORD-20260508-0003", status=OrderStatus.CONFIRMED)
        make_job(job_repo, "ORD-20260508-0001")
        make_job(job_repo, "ORD-20260508-0002")

        result = ctrl.get_summary()

        assert result["queue_size"] == 2

    def test_get_summary_returns_zero_when_no_data(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = MonitorController(sample_repo, order_repo, job_repo)

        result = ctrl.get_summary()

        assert result["sample_count"] == 0
        assert result["total_stock"] == 0
        assert result["order_count"] == 0
        assert result["queue_size"] == 0

    def test_get_summary_contains_all_required_keys(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = MonitorController(sample_repo, order_repo, job_repo)

        result = ctrl.get_summary()

        assert "sample_count" in result
        assert "total_stock" in result
        assert "order_count" in result
        assert "queue_size" in result

    def test_get_summary_queue_size_uses_job_repo_count(self, repos):
        # PRODUCING 주문은 있지만 job이 없으면 queue_size = 0 이어야 함
        sample_repo, order_repo, job_repo = repos
        ctrl = MonitorController(sample_repo, order_repo, job_repo)
        make_order(order_repo, "ORD-20260508-0001", status=OrderStatus.PRODUCING)

        result = ctrl.get_summary()

        assert result["queue_size"] == 0
