import pytest

from app import App
from controller.order_controller import OrderController
from controller.production_controller import ProductionController
from controller.sample_controller import SampleController
from repository.order_repository import OrderRepository
from repository.production_job_repository import ProductionJobRepository
from repository.sample_repository import SampleRepository



def _run(app_obj, monkeypatch, inputs):
    it = iter(inputs)
    monkeypatch.setattr("builtins.input", lambda *args, **kwargs: next(it))
    app_obj.run()


def _make_app(tmp_path, monkeypatch):
    monkeypatch.setattr(App, "DATA_DIR", tmp_path)
    return App()


def _make_system(tmp_path):
    sample_repo = SampleRepository(tmp_path / "samples.json")
    order_repo = OrderRepository(tmp_path / "orders.json")
    job_repo = ProductionJobRepository(tmp_path / "production_jobs.json")
    return (
        SampleController(sample_repo, order_repo),
        OrderController(sample_repo, order_repo, job_repo),
        ProductionController(sample_repo, order_repo, job_repo),
    )


@pytest.fixture
def pre_reserved(tmp_path):
    """시료 1개(stock=100) + RESERVED 주문 1개를 사전 생성."""
    sc, oc, _ = _make_system(tmp_path)
    sc.register("S-001", "웨이퍼", 30.0, 0.9, 100)
    order = oc.reserve("S-001", "고객A", 10)
    return tmp_path, order.order_id


@pytest.fixture
def pre_producing(tmp_path):
    """시료(stock=0) + PRODUCING 주문 1개를 사전 생성."""
    sc, oc, _ = _make_system(tmp_path)
    sc.register("S-001", "웨이퍼", 30.0, 0.9, 0)
    order = oc.reserve("S-001", "고객A", 10)
    oc.approve(order.order_id)  # stock=0 → PRODUCING
    return tmp_path, order.order_id


@pytest.fixture
def pre_confirmed(tmp_path):
    """시료(stock=100) + CONFIRMED 주문 1개를 사전 생성."""
    sc, oc, _ = _make_system(tmp_path)
    sc.register("S-001", "웨이퍼", 30.0, 0.9, 100)
    order = oc.reserve("S-001", "고객A", 10)
    oc.approve(order.order_id)  # stock=100 → CONFIRMED
    return tmp_path, order.order_id



class TestMainView:

    def test_exit_shows_exit_message(self, tmp_path, monkeypatch, capsys):
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, ["0"])
        assert "시스템을 종료합니다" in capsys.readouterr().out

    def test_header_shows_summary(self, tmp_path, monkeypatch, capsys):
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, ["0"])
        out = capsys.readouterr().out
        assert "S-Semi 반도체 시료 생산주문관리 시스템" in out
        assert "등록 시료 종수" in out

    def test_invalid_menu_choice_shows_error(self, tmp_path, monkeypatch, capsys):
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, ["9", "0"])
        assert "올바른 메뉴 번호를 입력하세요" in capsys.readouterr().out



class TestSampleView:

    def test_register_success_shows_completion_message(self, tmp_path, monkeypatch, capsys):
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, [
            "1", "1", "S-001", "웨이퍼", "30.0", "0.9", "100",
            "0",
        ])
        out = capsys.readouterr().out
        assert "시료 등록 완료" in out
        assert "S-001" in out

    def test_register_duplicate_shows_error(self, tmp_path, monkeypatch, capsys):
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, [
            "1", "1", "S-001", "웨이퍼", "30.0", "0.9", "0",
            "1", "1", "S-001", "웨이퍼2", "30.0", "0.9", "0",
            "0",
        ])
        assert "오류" in capsys.readouterr().out

    def test_sample_list_shows_registered_samples(self, tmp_path, monkeypatch, capsys):
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, [
            "1", "1", "S-001", "웨이퍼", "30.0", "0.9", "50",
            "1", "2",
            "0",
        ])
        out = capsys.readouterr().out
        assert "시료 목록" in out
        assert "S-001" in out

    def test_sample_list_empty_shows_empty_message(self, tmp_path, monkeypatch, capsys):
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, ["1", "2", "0"])
        assert "해당 시료가 없습니다" in capsys.readouterr().out

    def test_sample_search_shows_results(self, tmp_path, monkeypatch, capsys):
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, [
            "1", "1", "S-001", "웨이퍼", "30.0", "0.9", "0",
            "1", "3", "웨이퍼",
            "0",
        ])
        out = capsys.readouterr().out
        assert "검색 결과" in out
        assert "S-001" in out

    def test_sample_search_no_match_shows_empty(self, tmp_path, monkeypatch, capsys):
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, [
            "1", "1", "S-001", "웨이퍼", "30.0", "0.9", "0",
            "1", "3", "없는키워드",
            "0",
        ])
        assert "해당 시료가 없습니다" in capsys.readouterr().out

    def test_sample_invalid_sub_shows_error(self, tmp_path, monkeypatch, capsys):
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, ["1", "9", "0"])
        assert "올바른 번호를 입력하세요" in capsys.readouterr().out



class TestOrderViewReserve:

    def test_reserve_success_shows_order_result(self, tmp_path, monkeypatch, capsys):
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, [
            "1", "1", "S-001", "웨이퍼", "30.0", "0.9", "100",
            "2", "S-001", "고객A", "10",
            "0",
        ])
        out = capsys.readouterr().out
        assert "주문 접수 완료" in out
        assert "RESERVED" in out

    def test_reserve_invalid_sample_shows_error(self, tmp_path, monkeypatch, capsys):
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, ["2", "NONE", "고객A", "10", "0"])
        assert "오류" in capsys.readouterr().out



class TestOrderViewApproveReject:

    def test_approve_confirmed_shows_confirmed_status(self, pre_reserved, monkeypatch, capsys):
        tmp_path, order_id = pre_reserved
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, ["3", "1", order_id, "0"])
        out = capsys.readouterr().out
        assert "주문 승인 완료" in out
        assert "CONFIRMED" in out

    def test_approve_producing_shows_production_info(self, tmp_path, monkeypatch, capsys):
        sc, oc, _ = _make_system(tmp_path)
        sc.register("S-001", "웨이퍼", 30.0, 0.9, 0)
        order = oc.reserve("S-001", "고객A", 10)
        # 아직 approve 전 — App을 통해 approve 수행
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, ["3", "1", order.order_id, "0"])
        out = capsys.readouterr().out
        assert "재고 부족 - 생산 등록" in out
        assert "PRODUCING" in out

    def test_reject_shows_rejected_status(self, pre_reserved, monkeypatch, capsys):
        tmp_path, order_id = pre_reserved
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, ["3", "2", order_id, "0"])
        out = capsys.readouterr().out
        assert "주문 거절 완료" in out
        assert "REJECTED" in out

    def test_approve_invalid_order_id_shows_error(self, pre_reserved, monkeypatch, capsys):
        tmp_path, _ = pre_reserved
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, ["3", "1", "ORD-INVALID", "0"])
        assert "오류" in capsys.readouterr().out

    def test_reject_invalid_order_id_shows_error(self, pre_reserved, monkeypatch, capsys):
        tmp_path, _ = pre_reserved
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, ["3", "2", "ORD-INVALID", "0"])
        assert "오류" in capsys.readouterr().out

    def test_approve_reject_no_reserved_shows_empty_list(self, tmp_path, monkeypatch, capsys):
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, ["3", "0"])
        out = capsys.readouterr().out
        assert "접수 대기 주문 목록" in out
        assert "해당 주문이 없습니다" in out

    def test_approve_reject_invalid_sub_shows_error(self, pre_reserved, monkeypatch, capsys):
        tmp_path, _ = pre_reserved
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, ["3", "9", "0"])
        assert "올바른 번호를 입력하세요" in capsys.readouterr().out



class TestMonitorView:

    def test_order_stats_shows_header(self, tmp_path, monkeypatch, capsys):
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, ["4", "1", "0"])
        assert "주문량 현황" in capsys.readouterr().out

    def test_stock_status_empty_shows_empty_message(self, tmp_path, monkeypatch, capsys):
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, ["4", "2", "0"])
        assert "등록된 시료가 없습니다" in capsys.readouterr().out

    def test_stock_status_with_samples_shows_table(self, tmp_path, monkeypatch, capsys):
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, [
            "1", "1", "S-001", "웨이퍼", "30.0", "0.9", "50",
            "4", "2",
            "0",
        ])
        out = capsys.readouterr().out
        assert "재고 현황" in out
        assert "S-001" in out

    def test_monitor_invalid_sub_shows_error(self, tmp_path, monkeypatch, capsys):
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, ["4", "9", "0"])
        assert "올바른 번호를 입력하세요" in capsys.readouterr().out



class TestProductionView:

    def test_no_current_job_shows_empty_message(self, tmp_path, monkeypatch, capsys):
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, ["5", "0"])
        out = capsys.readouterr().out
        assert "현재 생산 중인 작업이 없습니다" in out
        assert "생산 대기 큐" in out

    def test_current_job_shows_job_info(self, pre_producing, monkeypatch, capsys):
        tmp_path, _ = pre_producing
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, ["5", "n", "0"])
        out = capsys.readouterr().out
        assert "현재 생산 중인 작업" in out
        assert "웨이퍼" in out

    def test_complete_current_job_shows_result(self, pre_producing, monkeypatch, capsys):
        tmp_path, _ = pre_producing
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, ["5", "y", "0"])
        out = capsys.readouterr().out
        assert "생산 완료 처리" in out
        assert "CONFIRMED" in out

    def test_current_job_without_sample_shows_sample_id(self, tmp_path, monkeypatch, capsys):
        """시료가 삭제된 PRODUCING 주문 표시 시 sample_id 폴백 경로."""
        sc, oc, _ = _make_system(tmp_path)
        sc.register("S-001", "웨이퍼", 30.0, 0.9, 0)
        order = oc.reserve("S-001", "고객A", 10)
        oc.approve(order.order_id)  # → PRODUCING
        SampleRepository(tmp_path / "samples.json").delete("S-001")  # 시료 삭제
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, ["5", "n", "0"])
        out = capsys.readouterr().out
        assert "S-001" in out  # sample_id 폴백 표시

    def test_queue_shows_waiting_jobs(self, tmp_path, monkeypatch, capsys):
        """두 번째 PRODUCING 주문이 대기 큐에 표시되는지 확인."""
        sc, oc, _ = _make_system(tmp_path)
        sc.register("S-001", "웨이퍼", 30.0, 0.9, 0)
        o1 = oc.reserve("S-001", "고객A", 5)
        oc.approve(o1.order_id)  # 첫 번째 → 현재 작업
        o2 = oc.reserve("S-001", "고객B", 3)
        oc.approve(o2.order_id)  # 두 번째 → 대기 큐
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, ["5", "n", "0"])
        out = capsys.readouterr().out
        assert "생산 대기 큐" in out
        assert "웨이퍼" in out  # 큐 테이블에 시료명 표시



class TestOrderViewRelease:

    def test_release_shows_release_result(self, pre_confirmed, monkeypatch, capsys):
        tmp_path, order_id = pre_confirmed
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, ["6", order_id, "0"])
        out = capsys.readouterr().out
        assert "출고 처리 완료" in out
        assert "RELEASE" in out

    def test_release_no_confirmed_shows_empty_list(self, tmp_path, monkeypatch, capsys):
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, ["6", "0"])
        out = capsys.readouterr().out
        assert "출고 대기 주문 목록" in out
        assert "해당 주문이 없습니다" in out

    def test_release_invalid_order_id_shows_error(self, pre_confirmed, monkeypatch, capsys):
        tmp_path, _ = pre_confirmed
        app = _make_app(tmp_path, monkeypatch)
        _run(app, monkeypatch, ["6", "ORD-INVALID", "0"])
        assert "오류" in capsys.readouterr().out
