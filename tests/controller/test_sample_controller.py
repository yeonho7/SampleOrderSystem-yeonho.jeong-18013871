import pytest
from model.order import Order, OrderStatus
from controller.sample_controller import SampleController
from tests.helpers import make_sample


class TestSampleControllerRegister:

    def test_register_returns_sample_with_correct_fields(self, repos):
        sample_repo, order_repo, _ = repos
        ctrl = SampleController(sample_repo, order_repo)
        result = ctrl.register("S-001", "실리콘 웨이퍼", 5.0, 0.9, stock=10)

        assert result.sample_id == "S-001"
        assert result.name == "실리콘 웨이퍼"
        assert result.avg_production_time == 5.0
        assert result.yield_rate == 0.9
        assert result.stock == 10

    def test_register_persists_sample_to_repository(self, repos):
        sample_repo, order_repo, _ = repos
        ctrl = SampleController(sample_repo, order_repo)
        ctrl.register("S-001", "실리콘 웨이퍼", 5.0, 0.9, stock=10)

        assert sample_repo.find_by_id("S-001") is not None

    def test_register_raises_when_duplicate_sample_id(self, repos):
        sample_repo, order_repo, _ = repos
        ctrl = SampleController(sample_repo, order_repo)
        ctrl.register("S-001", "실리콘 웨이퍼", 5.0, 0.9)

        with pytest.raises(ValueError, match="이미 등록된 시료 ID입니다"):
            ctrl.register("S-001", "다른 이름", 3.0, 0.8)


class TestSampleControllerFind:

    def test_find_by_id_returns_sample_when_exists(self, repos):
        sample_repo, order_repo, _ = repos
        ctrl = SampleController(sample_repo, order_repo)
        make_sample(sample_repo, "S-001")

        result = ctrl.find_by_id("S-001")

        assert result is not None
        assert result.sample_id == "S-001"

    def test_find_by_id_returns_none_when_not_exists(self, repos):
        sample_repo, order_repo, _ = repos
        ctrl = SampleController(sample_repo, order_repo)

        result = ctrl.find_by_id("S-999")

        assert result is None

    def test_find_all_returns_all_registered_samples(self, repos):
        sample_repo, order_repo, _ = repos
        ctrl = SampleController(sample_repo, order_repo)
        make_sample(sample_repo, "S-001", "웨이퍼 A")
        make_sample(sample_repo, "S-002", "웨이퍼 B")
        make_sample(sample_repo, "S-003", "웨이퍼 C")

        result = ctrl.find_all()

        assert len(result) == 3

    def test_find_all_returns_empty_when_no_samples(self, repos):
        sample_repo, order_repo, _ = repos
        ctrl = SampleController(sample_repo, order_repo)

        result = ctrl.find_all()

        assert result == []


class TestSampleControllerSearch:

    def test_search_returns_samples_matching_keyword(self, repos):
        sample_repo, order_repo, _ = repos
        ctrl = SampleController(sample_repo, order_repo)
        make_sample(sample_repo, "S-001", "실리콘 웨이퍼")
        make_sample(sample_repo, "S-002", "갈륨비소 웨이퍼")
        make_sample(sample_repo, "S-003", "게르마늄 기판")

        result = ctrl.search("웨이퍼")

        assert len(result) == 2

    def test_search_returns_empty_when_no_keyword_match(self, repos):
        sample_repo, order_repo, _ = repos
        ctrl = SampleController(sample_repo, order_repo)
        make_sample(sample_repo, "S-001", "실리콘 웨이퍼")

        result = ctrl.search("존재하지않는키워드")

        assert result == []

    def test_search_is_case_insensitive(self, repos):
        sample_repo, order_repo, _ = repos
        ctrl = SampleController(sample_repo, order_repo)
        make_sample(sample_repo, "S-001", "Silicon Wafer")

        result = ctrl.search("silicon")

        assert len(result) == 1


class TestSampleControllerStockStatus:

    def test_get_stock_status_returns_고갈_when_stock_is_zero(self, repos):
        sample_repo, order_repo, _ = repos
        ctrl = SampleController(sample_repo, order_repo)
        make_sample(sample_repo, "S-001", stock=0)

        result = ctrl.get_stock_status("S-001")

        assert result == "고갈"

    def test_get_stock_status_returns_부족_when_stock_less_than_pending_quantity(
        self, repos
    ):
        sample_repo, order_repo, _ = repos
        ctrl = SampleController(sample_repo, order_repo)
        make_sample(sample_repo, "S-001", stock=3)
        order = Order(
            order_id="ORD-20260508-0001",
            sample_id="S-001",
            customer_name="고객A",
            quantity=5,
            status=OrderStatus.RESERVED,
        )
        order_repo.create(order)

        result = ctrl.get_stock_status("S-001")

        assert result == "부족"

    def test_get_stock_status_returns_여유_when_stock_equals_pending_quantity(
        self, repos
    ):
        sample_repo, order_repo, _ = repos
        ctrl = SampleController(sample_repo, order_repo)
        make_sample(sample_repo, "S-001", stock=5)
        order = Order(
            order_id="ORD-20260508-0001",
            sample_id="S-001",
            customer_name="고객A",
            quantity=5,
            status=OrderStatus.RESERVED,
        )
        order_repo.create(order)

        result = ctrl.get_stock_status("S-001")

        assert result == "여유"

    def test_get_stock_status_returns_여유_when_stock_greater_than_pending_quantity(
        self, repos
    ):
        sample_repo, order_repo, _ = repos
        ctrl = SampleController(sample_repo, order_repo)
        make_sample(sample_repo, "S-001", stock=10)
        order = Order(
            order_id="ORD-20260508-0001",
            sample_id="S-001",
            customer_name="고객A",
            quantity=5,
            status=OrderStatus.RESERVED,
        )
        order_repo.create(order)

        result = ctrl.get_stock_status("S-001")

        assert result == "여유"

    def test_get_stock_status_excludes_rejected_orders_from_pending(self, repos):
        sample_repo, order_repo, _ = repos
        ctrl = SampleController(sample_repo, order_repo)
        # stock=1, REJECTED 주문 수량=10 → REJECTED 제외하면 미처리=0 → 여유
        make_sample(sample_repo, "S-001", stock=1)
        order = Order(
            order_id="ORD-20260508-0001",
            sample_id="S-001",
            customer_name="고객A",
            quantity=10,
            status=OrderStatus.REJECTED,
        )
        order_repo.create(order)

        result = ctrl.get_stock_status("S-001")

        assert result == "여유"

    def test_get_stock_status_excludes_confirmed_orders_from_pending(self, repos):
        sample_repo, order_repo, _ = repos
        ctrl = SampleController(sample_repo, order_repo)
        # stock=1, CONFIRMED 주문 수량=10 → CONFIRMED 제외하면 미처리=0 → 여유
        make_sample(sample_repo, "S-001", stock=1)
        order = Order(
            order_id="ORD-20260508-0001",
            sample_id="S-001",
            customer_name="고객A",
            quantity=10,
            status=OrderStatus.CONFIRMED,
        )
        order_repo.create(order)

        result = ctrl.get_stock_status("S-001")

        assert result == "여유"

    def test_get_stock_status_includes_producing_orders_in_pending(self, repos):
        sample_repo, order_repo, _ = repos
        ctrl = SampleController(sample_repo, order_repo)
        # stock=2, PRODUCING 주문 수량=5 → 2 < 5 → 부족
        make_sample(sample_repo, "S-001", stock=2)
        order = Order(
            order_id="ORD-20260508-0001",
            sample_id="S-001",
            customer_name="고객A",
            quantity=5,
            status=OrderStatus.PRODUCING,
        )
        order_repo.create(order)

        result = ctrl.get_stock_status("S-001")

        assert result == "부족"
