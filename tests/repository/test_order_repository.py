"""
TDD Red 단계 — OrderRepository 단위 테스트.

repository/order_repository.py 가 아직 존재하지 않으므로
이 파일을 실행하면 ImportError 가 발생하며 전체 테스트가 FAIL 상태여야 한다.
구현 후 모든 테스트가 GREEN 으로 전환되는 것이 목표다.
"""

import json
import pytest
from datetime import datetime

from model.order import Order, OrderStatus
from repository.order_repository import OrderRepository


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def _make_order(order_id="ORD-20260508-0001", sample_id="S-001",
                customer_name="홍길동", quantity=10,
                status=OrderStatus.RESERVED):
    return Order(
        order_id=order_id,
        sample_id=sample_id,
        customer_name=customer_name,
        quantity=quantity,
        status=status,
    )


# ---------------------------------------------------------------------------
# create / find_by_id
# ---------------------------------------------------------------------------

class TestOrderRepositoryCreate:

    def test_create_returns_created_order(self, tmp_data_dir):
        repo = OrderRepository(tmp_data_dir / "orders.json")
        order = _make_order()
        result = repo.create(order)
        assert result.order_id == "ORD-20260508-0001"

    def test_find_by_id_returns_order_after_create(self, tmp_data_dir):
        repo = OrderRepository(tmp_data_dir / "orders.json")
        repo.create(_make_order(order_id="ORD-20260508-0001"))
        found = repo.find_by_id("ORD-20260508-0001")
        assert found is not None
        assert found.order_id == "ORD-20260508-0001"

    def test_find_by_id_returns_none_when_not_exists(self, tmp_data_dir):
        repo = OrderRepository(tmp_data_dir / "orders.json")
        result = repo.find_by_id("ORD-99991231-9999")
        assert result is None

    def test_find_by_id_restores_all_fields(self, tmp_data_dir):
        repo = OrderRepository(tmp_data_dir / "orders.json")
        repo.create(_make_order(
            order_id="ORD-20260508-0002",
            sample_id="S-007",
            customer_name="김철수",
            quantity=42,
            status=OrderStatus.RESERVED,
        ))
        found = repo.find_by_id("ORD-20260508-0002")
        assert found.sample_id == "S-007"
        assert found.customer_name == "김철수"
        assert found.quantity == 42

    def test_find_by_id_restores_created_at_as_datetime(self, tmp_data_dir):
        repo = OrderRepository(tmp_data_dir / "orders.json")
        repo.create(_make_order())
        found = repo.find_by_id("ORD-20260508-0001")
        assert isinstance(found.created_at, datetime)

    def test_find_by_id_restores_updated_at_as_datetime(self, tmp_data_dir):
        repo = OrderRepository(tmp_data_dir / "orders.json")
        repo.create(_make_order())
        found = repo.find_by_id("ORD-20260508-0001")
        assert isinstance(found.updated_at, datetime)


# ---------------------------------------------------------------------------
# find_all
# ---------------------------------------------------------------------------

class TestOrderRepositoryFindAll:

    def test_find_all_returns_empty_list_when_no_orders(self, tmp_data_dir):
        repo = OrderRepository(tmp_data_dir / "orders.json")
        assert repo.find_all() == []

    def test_find_all_returns_all_created_orders(self, tmp_data_dir):
        repo = OrderRepository(tmp_data_dir / "orders.json")
        repo.create(_make_order(order_id="ORD-20260508-0001"))
        repo.create(_make_order(order_id="ORD-20260508-0002"))
        result = repo.find_all()
        assert len(result) == 2

    def test_find_all_returns_order_instances(self, tmp_data_dir):
        repo = OrderRepository(tmp_data_dir / "orders.json")
        repo.create(_make_order())
        result = repo.find_all()
        assert isinstance(result[0], Order)


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

class TestOrderRepositoryUpdate:

    def test_update_returns_true_when_order_exists(self, tmp_data_dir):
        repo = OrderRepository(tmp_data_dir / "orders.json")
        repo.create(_make_order(order_id="ORD-20260508-0001"))
        updated = _make_order(order_id="ORD-20260508-0001", status=OrderStatus.CONFIRMED)
        assert repo.update(updated) is True

    def test_update_changes_status_field(self, tmp_data_dir):
        repo = OrderRepository(tmp_data_dir / "orders.json")
        repo.create(_make_order(order_id="ORD-20260508-0001", status=OrderStatus.RESERVED))
        order = repo.find_by_id("ORD-20260508-0001")
        order.status = OrderStatus.CONFIRMED
        repo.update(order)
        found = repo.find_by_id("ORD-20260508-0001")
        assert found.status == OrderStatus.CONFIRMED

    def test_update_returns_false_when_order_not_exists(self, tmp_data_dir):
        repo = OrderRepository(tmp_data_dir / "orders.json")
        result = repo.update(_make_order(order_id="ORD-99991231-9999"))
        assert result is False


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

class TestOrderRepositoryDelete:

    def test_delete_returns_true_when_order_exists(self, tmp_data_dir):
        repo = OrderRepository(tmp_data_dir / "orders.json")
        repo.create(_make_order(order_id="ORD-20260508-0001"))
        assert repo.delete("ORD-20260508-0001") is True

    def test_delete_removes_order_from_find_all(self, tmp_data_dir):
        repo = OrderRepository(tmp_data_dir / "orders.json")
        repo.create(_make_order(order_id="ORD-20260508-0001"))
        repo.delete("ORD-20260508-0001")
        assert repo.find_by_id("ORD-20260508-0001") is None

    def test_delete_returns_false_when_order_not_exists(self, tmp_data_dir):
        repo = OrderRepository(tmp_data_dir / "orders.json")
        assert repo.delete("ORD-99991231-9999") is False


# ---------------------------------------------------------------------------
# find_by_status
# ---------------------------------------------------------------------------

class TestOrderRepositoryFindByStatus:

    def test_find_by_status_returns_only_matching_orders(self, tmp_data_dir):
        repo = OrderRepository(tmp_data_dir / "orders.json")
        repo.create(_make_order(order_id="ORD-20260508-0001", status=OrderStatus.RESERVED))
        repo.create(_make_order(order_id="ORD-20260508-0002", status=OrderStatus.CONFIRMED))
        result = repo.find_by_status(OrderStatus.RESERVED)
        assert len(result) == 1
        assert result[0].order_id == "ORD-20260508-0001"

    def test_find_by_status_returns_empty_list_when_no_match(self, tmp_data_dir):
        repo = OrderRepository(tmp_data_dir / "orders.json")
        repo.create(_make_order(order_id="ORD-20260508-0001", status=OrderStatus.RESERVED))
        result = repo.find_by_status(OrderStatus.PRODUCING)
        assert result == []

    def test_find_by_status_returns_multiple_matches(self, tmp_data_dir):
        repo = OrderRepository(tmp_data_dir / "orders.json")
        repo.create(_make_order(order_id="ORD-20260508-0001", status=OrderStatus.RESERVED))
        repo.create(_make_order(order_id="ORD-20260508-0002", status=OrderStatus.RESERVED))
        repo.create(_make_order(order_id="ORD-20260508-0003", status=OrderStatus.CONFIRMED))
        result = repo.find_by_status(OrderStatus.RESERVED)
        assert len(result) == 2

    def test_find_by_status_excludes_rejected_when_filtering_reserved(self, tmp_data_dir):
        repo = OrderRepository(tmp_data_dir / "orders.json")
        repo.create(_make_order(order_id="ORD-20260508-0001", status=OrderStatus.REJECTED))
        result = repo.find_by_status(OrderStatus.RESERVED)
        assert result == []


# ---------------------------------------------------------------------------
# count_by_status
# ---------------------------------------------------------------------------

class TestOrderRepositoryCountByStatus:

    def test_count_by_status_returns_zero_when_no_orders(self, tmp_data_dir):
        repo = OrderRepository(tmp_data_dir / "orders.json")
        assert repo.count_by_status(OrderStatus.RESERVED) == 0

    def test_count_by_status_returns_correct_count(self, tmp_data_dir):
        repo = OrderRepository(tmp_data_dir / "orders.json")
        repo.create(_make_order(order_id="ORD-20260508-0001", status=OrderStatus.RESERVED))
        repo.create(_make_order(order_id="ORD-20260508-0002", status=OrderStatus.RESERVED))
        repo.create(_make_order(order_id="ORD-20260508-0003", status=OrderStatus.CONFIRMED))
        assert repo.count_by_status(OrderStatus.RESERVED) == 2

    def test_count_by_status_returns_int(self, tmp_data_dir):
        repo = OrderRepository(tmp_data_dir / "orders.json")
        result = repo.count_by_status(OrderStatus.RESERVED)
        assert isinstance(result, int)


# ---------------------------------------------------------------------------
# OrderStatus enum 직렬화 / 역직렬화
# ---------------------------------------------------------------------------

class TestOrderRepositoryStatusSerialization:

    def test_status_is_stored_as_string_in_json(self, tmp_data_dir):
        """JSON 파일에 status 값이 문자열로 저장되어야 한다."""
        filepath = tmp_data_dir / "orders.json"
        repo = OrderRepository(filepath)
        repo.create(_make_order(status=OrderStatus.CONFIRMED))
        raw = json.loads(filepath.read_text(encoding="utf-8"))
        assert isinstance(raw[0]["status"], str)
        assert raw[0]["status"] == "CONFIRMED"

    def test_status_is_restored_as_enum_from_json(self, tmp_data_dir):
        """JSON 파일에서 읽을 때 status 가 OrderStatus enum 으로 복원되어야 한다."""
        filepath = tmp_data_dir / "orders.json"
        repo = OrderRepository(filepath)
        repo.create(_make_order(status=OrderStatus.PRODUCING))
        found = repo.find_by_id("ORD-20260508-0001")
        assert found.status == OrderStatus.PRODUCING
        assert isinstance(found.status, OrderStatus)

    def test_all_statuses_survive_round_trip(self, tmp_data_dir):
        """5가지 상태 모두 직렬화 → 역직렬화 후 동일한 enum 값이어야 한다."""
        filepath = tmp_data_dir / "orders.json"
        repo = OrderRepository(filepath)
        statuses = [
            OrderStatus.RESERVED,
            OrderStatus.REJECTED,
            OrderStatus.PRODUCING,
            OrderStatus.CONFIRMED,
            OrderStatus.RELEASE,
        ]
        for i, status in enumerate(statuses, start=1):
            order_id = f"ORD-20260508-{i:04d}"
            repo.create(_make_order(order_id=order_id, status=status))

        for i, expected_status in enumerate(statuses, start=1):
            order_id = f"ORD-20260508-{i:04d}"
            found = repo.find_by_id(order_id)
            assert found.status == expected_status

    def test_new_instance_loads_status_as_enum(self, tmp_data_dir):
        """새 Repository 인스턴스로 불러올 때도 status 가 enum 으로 복원되어야 한다."""
        filepath = tmp_data_dir / "orders.json"
        repo1 = OrderRepository(filepath)
        repo1.create(_make_order(status=OrderStatus.RELEASE))

        repo2 = OrderRepository(filepath)
        found = repo2.find_by_id("ORD-20260508-0001")
        assert found.status == OrderStatus.RELEASE
        assert isinstance(found.status, OrderStatus)
