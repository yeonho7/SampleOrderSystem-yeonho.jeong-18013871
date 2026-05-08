import pytest
from model.order import Order, OrderStatus
from controller.production_controller import ProductionController
from tests.helpers import make_sample, make_job


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


class TestProductionControllerGetCurrent:

    def test_get_current_returns_first_job_in_queue(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = ProductionController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=0)
        _make_producing_order(order_repo, "ORD-20260508-0001")
        _make_producing_order(order_repo, "ORD-20260508-0002")
        make_job(job_repo, "ORD-20260508-0001")
        make_job(job_repo, "ORD-20260508-0002")

        result = ctrl.get_current()

        assert result is not None
        assert result.order_id == "ORD-20260508-0001"

    def test_get_current_returns_none_when_queue_is_empty(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = ProductionController(sample_repo, order_repo, job_repo)

        result = ctrl.get_current()

        assert result is None


class TestProductionControllerGetQueue:

    def test_get_queue_returns_jobs_after_first(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = ProductionController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=0)
        for i in range(1, 4):
            _make_producing_order(order_repo, f"ORD-20260508-000{i}")
            make_job(job_repo, f"ORD-20260508-000{i}")

        result = ctrl.get_queue()

        # 첫 번째를 제외한 2개가 반환되어야 함
        assert len(result) == 2
        assert result[0].order_id == "ORD-20260508-0002"
        assert result[1].order_id == "ORD-20260508-0003"

    def test_get_queue_returns_empty_when_only_one_job(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = ProductionController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=0)
        _make_producing_order(order_repo, "ORD-20260508-0001")
        make_job(job_repo, "ORD-20260508-0001")

        result = ctrl.get_queue()

        assert result == []

    def test_get_queue_returns_empty_when_no_jobs(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = ProductionController(sample_repo, order_repo, job_repo)

        result = ctrl.get_queue()

        assert result == []

    def test_get_queue_size_returns_correct_count(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = ProductionController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=0)
        for i in range(1, 4):
            _make_producing_order(order_repo, f"ORD-20260508-000{i}")
            make_job(job_repo, f"ORD-20260508-000{i}")

        result = ctrl.get_queue_size()

        assert result == 3

    def test_get_queue_size_returns_zero_when_no_jobs(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = ProductionController(sample_repo, order_repo, job_repo)

        result = ctrl.get_queue_size()

        assert result == 0


class TestProductionControllerCompleteCurrent:

    def test_complete_current_sets_order_status_to_confirmed(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = ProductionController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=0)
        _make_producing_order(order_repo, "ORD-20260508-0001")
        make_job(job_repo, "ORD-20260508-0001", actual_production=7)

        result = ctrl.complete_current()

        assert result.status == OrderStatus.CONFIRMED

    def test_complete_current_increments_stock_by_actual_production(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = ProductionController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=0)
        _make_producing_order(order_repo, "ORD-20260508-0001")
        make_job(job_repo, "ORD-20260508-0001", actual_production=7)

        ctrl.complete_current()

        sample = sample_repo.find_by_id("S-001")
        assert sample.stock == 7

    def test_complete_current_deletes_job_from_repository(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = ProductionController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=0)
        _make_producing_order(order_repo, "ORD-20260508-0001")
        make_job(job_repo, "ORD-20260508-0001", actual_production=7)

        ctrl.complete_current()

        assert job_repo.find_by_id("ORD-20260508-0001") is None

    def test_complete_current_processes_fifo_order(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = ProductionController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=0)
        _make_producing_order(order_repo, "ORD-20260508-0001")
        _make_producing_order(order_repo, "ORD-20260508-0002")
        # FIFO: 먼저 등록된 job이 먼저 처리됨
        make_job(job_repo, "ORD-20260508-0001", actual_production=5)
        make_job(job_repo, "ORD-20260508-0002", actual_production=8)

        result = ctrl.complete_current()

        assert result.order_id == "ORD-20260508-0001"

    def test_complete_current_raises_when_queue_is_empty(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = ProductionController(sample_repo, order_repo, job_repo)

        with pytest.raises(ValueError, match="생산 중인 작업이 없습니다"):
            ctrl.complete_current()


class TestProductionControllerFindJob:

    def test_find_job_returns_job_when_exists(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = ProductionController(sample_repo, order_repo, job_repo)
        make_sample(sample_repo, stock=0)
        _make_producing_order(order_repo, "ORD-20260508-0001")
        make_job(job_repo, "ORD-20260508-0001", actual_production=5)

        result = ctrl.find_job("ORD-20260508-0001")

        assert result is not None
        assert result.order_id == "ORD-20260508-0001"

    def test_find_job_returns_none_when_not_exists(self, repos):
        sample_repo, order_repo, job_repo = repos
        ctrl = ProductionController(sample_repo, order_repo, job_repo)

        result = ctrl.find_job("ORD-99999999-0001")

        assert result is None
