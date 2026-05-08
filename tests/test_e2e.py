import pytest
from math import ceil

from repository.sample_repository import SampleRepository
from repository.order_repository import OrderRepository
from repository.production_job_repository import ProductionJobRepository
from controller.sample_controller import SampleController
from controller.order_controller import OrderController
from controller.production_controller import ProductionController
from controller.monitor_controller import MonitorController
from model.order import OrderStatus


@pytest.fixture
def system(tmp_data_dir):
    """4개 Controller를 조립한 완전한 시스템 fixture."""
    sample_repo = SampleRepository(tmp_data_dir / "samples.json")
    order_repo = OrderRepository(tmp_data_dir / "orders.json")
    job_repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")

    return {
        "sample": SampleController(sample_repo, order_repo),
        "order": OrderController(sample_repo, order_repo, job_repo),
        "prod": ProductionController(sample_repo, order_repo, job_repo),
        "mon": MonitorController(sample_repo, order_repo, job_repo),
        # repo 직접 접근이 필요한 검증용
        "sample_repo": sample_repo,
        "order_repo": order_repo,
        "job_repo": job_repo,
    }



def test_scenario_1_full_release_flow_when_stock_sufficient(system):
    sc = system["sample"]
    oc = system["order"]
    mon = system["mon"]
    sample_repo = system["sample_repo"]

    # 시료 등록
    sample = sc.register("S001", "테스트시료A", avg_production_time=1.0, yield_rate=0.9, stock=100)
    assert sample.stock == 100

    # 주문 접수
    order = oc.reserve("S001", "고객A", quantity=30)
    assert order.status == OrderStatus.RESERVED

    # 승인 — 재고 충분이므로 CONFIRMED
    approved = oc.approve(order.order_id)
    assert approved.status == OrderStatus.CONFIRMED

    # 중간 상태: stock은 아직 차감 전
    mid_sample = sample_repo.find_by_id("S001")
    assert mid_sample.stock == 100

    # 출고 처리
    released = oc.release(order.order_id)
    assert released.status == OrderStatus.RELEASE

    # stock이 70으로 감소했는지 확인
    after_sample = sample_repo.find_by_id("S001")
    assert after_sample.stock == 70

    # monitor 요약 검증
    summary = mon.get_summary()
    assert summary["sample_count"] == 1
    assert summary["order_count"] == 1
    assert summary["total_stock"] == 70



def test_scenario_2_production_then_release_when_stock_insufficient(system):
    sc = system["sample"]
    oc = system["order"]
    pc = system["prod"]
    sample_repo = system["sample_repo"]
    job_repo = system["job_repo"]

    # 시료 등록 (stock=5, yield_rate=0.8, avg_time=2.0)
    sc.register("S002", "테스트시료B", avg_production_time=2.0, yield_rate=0.8, stock=5)

    # 주문 접수 (qty=10, 부족분=5)
    order = oc.reserve("S002", "고객B", quantity=10)
    assert order.status == OrderStatus.RESERVED

    # 승인 — 재고 부족이므로 PRODUCING
    approved = oc.approve(order.order_id)
    assert approved.status == OrderStatus.PRODUCING

    # ProductionJob 생성 확인
    job = job_repo.find_first()
    assert job is not None
    assert job.order_id == order.order_id
    assert job.sample_id == "S002"

    # shortage=5 확인
    assert job.shortage == 5

    # actual_production = ceil(5 / (0.8 * 0.9)) = ceil(6.944...) = 7
    expected_actual_production = ceil(5 / (0.8 * 0.9))
    assert expected_actual_production == 7
    assert job.actual_production == 7

    # total_time = 2.0 * 7 = 14.0
    assert job.total_time == pytest.approx(14.0)

    # 생산 완료: stock += actual_production(7) → 5+7=12, 상태=CONFIRMED
    completed = pc.complete_current()
    assert completed.status == OrderStatus.CONFIRMED

    after_production_sample = sample_repo.find_by_id("S002")
    assert after_production_sample.stock == 12  # 5 + 7

    # ProductionJob이 삭제됐는지 확인
    assert job_repo.find_first() is None

    # 출고 처리 → RELEASE, stock=12-10=2
    released = oc.release(order.order_id)
    assert released.status == OrderStatus.RELEASE

    after_release_sample = sample_repo.find_by_id("S002")
    assert after_release_sample.stock == 2  # 12 - 10



def test_scenario_3_reject_order_and_monitor_exclusion(system):
    sc = system["sample"]
    oc = system["order"]
    mon = system["mon"]

    # 시료 등록
    sc.register("S003", "테스트시료C", avg_production_time=1.0, yield_rate=0.9, stock=50)

    # 주문 접수
    order = oc.reserve("S003", "고객C", quantity=20)
    assert order.status == OrderStatus.RESERVED

    # 거절
    rejected = oc.reject(order.order_id)
    assert rejected.status == OrderStatus.REJECTED

    # get_order_stats()에서 REJECTED는 집계되지 않는지 확인
    stats = mon.get_order_stats()
    assert OrderStatus.REJECTED not in stats
    assert stats[OrderStatus.RESERVED] == 0
    assert stats[OrderStatus.CONFIRMED] == 0
    assert stats[OrderStatus.PRODUCING] == 0
    assert stats[OrderStatus.RELEASE] == 0

    # get_stock_status_all()에서 REJECTED 주문은 미처리 집계에서 제외되는지 확인
    # REJECTED 주문의 qty=20이 제외되므로 stock=50 >= 0 → 여유
    stock_statuses = mon.get_stock_status_all()
    assert len(stock_statuses) == 1
    assert stock_statuses[0]["status"] == "여유"

    # get_summary()에서 REJECTED는 order_count에서 제외
    summary = mon.get_summary()
    assert summary["order_count"] == 0



def test_scenario_4_fifo_production_queue(system):
    sc = system["sample"]
    oc = system["order"]
    pc = system["prod"]

    # 시료 등록 (stock=0 → 모든 주문이 PRODUCING)
    sc.register("S004", "테스트시료D", avg_production_time=1.0, yield_rate=0.9, stock=0)

    # 주문 A 접수 및 승인 → PRODUCING (job_A 생성)
    order_a = oc.reserve("S004", "고객A", quantity=5)
    approved_a = oc.approve(order_a.order_id)
    assert approved_a.status == OrderStatus.PRODUCING

    # 주문 B 접수 및 승인 → PRODUCING (job_B 생성)
    order_b = oc.reserve("S004", "고객B", quantity=3)
    approved_b = oc.approve(order_b.order_id)
    assert approved_b.status == OrderStatus.PRODUCING

    # get_current()가 job_A(먼저 들어온 것) 반환 확인
    current = pc.get_current()
    assert current is not None
    assert current.order_id == order_a.order_id

    # get_queue()가 [job_B] 반환 확인
    queue = pc.get_queue()
    assert len(queue) == 1
    assert queue[0].order_id == order_b.order_id

    # complete_current() → 주문A=CONFIRMED
    completed_a = pc.complete_current()
    assert completed_a.order_id == order_a.order_id
    assert completed_a.status == OrderStatus.CONFIRMED

    # 이제 get_current()가 job_B를 반환하는지 확인
    new_current = pc.get_current()
    assert new_current is not None
    assert new_current.order_id == order_b.order_id

    # get_queue()는 비어 있어야 함
    assert pc.get_queue() == []



def test_scenario_5_stock_status_transitions(system):
    sc = system["sample"]
    oc = system["order"]
    sample_repo = system["sample_repo"]

    # 시료 등록 (stock=10)
    sc.register("S005", "테스트시료E", avg_production_time=1.0, yield_rate=0.9, stock=10)

    # 초기 상태: 여유
    assert sc.get_stock_status("S005") == "여유"

    # 주문 접수 (qty=15, RESERVED 상태) → stock=10 < 15 → 부족
    order = oc.reserve("S005", "고객E", quantity=15)
    assert order.status == OrderStatus.RESERVED
    assert sc.get_stock_status("S005") == "부족"

    # 주문 거절 → REJECTED는 미처리 집계 제외 → 여유 복원
    oc.reject(order.order_id)
    assert sc.get_stock_status("S005") == "여유"

    # stock을 0으로 업데이트 → 고갈
    sample = sample_repo.find_by_id("S005")
    sample.stock = 0
    sample_repo.update(sample)
    assert sc.get_stock_status("S005") == "고갈"



def test_scenario_6_reserve_with_unregistered_sample_id_raises_error(system):
    oc = system["order"]
    order_repo = system["order_repo"]

    # 미등록 sample_id로 주문 시도 → ValueError 발생
    with pytest.raises(ValueError):
        oc.reserve("NONEXISTENT", "고객F", quantity=10)

    # 주문이 저장되지 않았는지 확인
    assert order_repo.find_all() == []



def test_scenario_7_invalid_state_transitions_are_blocked(system):
    sc = system["sample"]
    oc = system["order"]

    # 시료 등록 및 주문 접수
    sc.register("S007", "테스트시료G", avg_production_time=1.0, yield_rate=0.9, stock=100)
    order = oc.reserve("S007", "고객G", quantity=10)
    assert order.status == OrderStatus.RESERVED

    # RESERVED 상태에서 release() 시도 → ValueError
    with pytest.raises(ValueError):
        oc.release(order.order_id)

    # RESERVED 상태에서 approve() → CONFIRMED (재고 충분)
    approved = oc.approve(order.order_id)
    assert approved.status == OrderStatus.CONFIRMED

    # CONFIRMED 상태에서 approve() 재시도 → ValueError
    with pytest.raises(ValueError):
        oc.approve(order.order_id)

    # CONFIRMED 상태에서 reject() 시도 → ValueError
    with pytest.raises(ValueError):
        oc.reject(order.order_id)



def test_scenario_8_monitor_stats_consistency(system):
    sc = system["sample"]
    oc = system["order"]
    mon = system["mon"]

    # 시료 2종 등록
    # 시료1: 재고 충분 (CONFIRMED 전환용)
    sc.register("S101", "시료1", avg_production_time=1.0, yield_rate=0.9, stock=1000)
    # 시료2: 재고 없음 (PRODUCING 전환용)
    sc.register("S102", "시료2", avg_production_time=1.0, yield_rate=0.9, stock=0)

    # RESERVED 2건: 주문만 접수하고 승인하지 않음
    r1 = oc.reserve("S101", "고객1", quantity=1)
    r2 = oc.reserve("S101", "고객2", quantity=1)
    assert r1.status == OrderStatus.RESERVED
    assert r2.status == OrderStatus.RESERVED

    # PRODUCING 1건: 재고 없는 시료에 주문 접수 후 승인
    p1 = oc.reserve("S102", "고객3", quantity=5)
    approved_p1 = oc.approve(p1.order_id)
    assert approved_p1.status == OrderStatus.PRODUCING

    # CONFIRMED 2건: 재고 충분한 시료에 주문 접수 후 승인
    c1 = oc.reserve("S101", "고객4", quantity=1)
    c2 = oc.reserve("S101", "고객5", quantity=1)
    approved_c1 = oc.approve(c1.order_id)
    approved_c2 = oc.approve(c2.order_id)
    assert approved_c1.status == OrderStatus.CONFIRMED
    assert approved_c2.status == OrderStatus.CONFIRMED

    # REJECTED 1건: 주문 접수 후 거절
    rej1 = oc.reserve("S101", "고객6", quantity=1)
    rejected = oc.reject(rej1.order_id)
    assert rejected.status == OrderStatus.REJECTED

    # get_order_stats() 검증: REJECTED 제외
    stats = mon.get_order_stats()
    assert stats[OrderStatus.RESERVED] == 2
    assert stats[OrderStatus.PRODUCING] == 1
    assert stats[OrderStatus.CONFIRMED] == 2
    assert stats[OrderStatus.RELEASE] == 0
    assert OrderStatus.REJECTED not in stats

    # get_summary() 검증: order_count=5 (REJECTED 제외), sample_count=2
    summary = mon.get_summary()
    assert summary["order_count"] == 5
    assert summary["sample_count"] == 2
