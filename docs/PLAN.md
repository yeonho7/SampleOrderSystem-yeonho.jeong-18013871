# 반도체 시료 생산주문관리 시스템 구현 계획

## 목표

Python 3 콘솔 CLI 앱으로 시료 등록·주문 접수·승인·생산·출고를 통합 관리한다.

## 아키텍처

MVC + Repository 패턴. `View → Controller → Repository → Model` 단방향 의존.  
JSON 파일 write-through 영속성 (`data/*.json`).

---

## 파일 구조

```
sample_order_system/
├── main.py
├── app.py                               메인 루프 + 메뉴 라우팅
├── generator.py                         더미 데이터 생성기 (수동 테스트용)
├── data/
│   ├── samples.json
│   ├── orders.json
│   └── production_jobs.json
├── model/
│   ├── sample.py                        Sample dataclass
│   ├── order.py                         OrderStatus Enum + Order dataclass
│   └── production_job.py               ProductionJob dataclass
├── repository/
│   ├── base_repository.py              BaseRepository ABC
│   ├── sample_repository.py
│   ├── order_repository.py
│   └── production_job_repository.py
├── controller/
│   ├── sample_controller.py
│   ├── order_controller.py
│   ├── production_controller.py
│   └── monitor_controller.py
├── view/
│   ├── main_view.py
│   ├── sample_view.py
│   ├── order_view.py
│   ├── production_view.py
│   └── monitor_view.py
└── tests/
    ├── conftest.py                      tmp_data_dir fixture (임시 JSON 파일)
    ├── test_model_order.py
    ├── repository/
    │   ├── test_sample_repository.py
    │   ├── test_order_repository.py
    │   └── test_production_job_repository.py
    └── controller/
        ├── test_sample_controller.py
        ├── test_order_controller.py
        ├── test_production_controller.py
        └── test_monitor_controller.py
```

---

## 도메인 규칙 (구현 전 숙지)

**주문 상태 전이**
```
RESERVED → approve (재고 충분) → CONFIRMED → RELEASE
RESERVED → approve (재고 부족) → PRODUCING → CONFIRMED → RELEASE
RESERVED → reject              → REJECTED
```

**생산량 계산**
```
부족분      = 주문 수량 - 현재 재고
실 생산량   = ceil(부족분 / (수율 × 0.9))
총 생산시간 = 평균 생산시간 × 실 생산량
```

**재고 상태 판단** (미처리 주문 = RESERVED + PRODUCING 수량 합계)
```
stock == 0            → 고갈
stock < 미처리 주문합계 → 부족
그 외                  → 여유
```

**핵심 제약**
- REJECTED는 모니터링 집계에서 항상 제외
- 출고는 CONFIRMED 상태에서만 가능
- 생산라인 큐는 FIFO (enqueued_at 오름차순)
- 등록되지 않은 시료 ID로 주문 시 즉시 에러

---

## POC 참조 요약

| POC | 참조할 핵심 패턴 |
|-----|----------------|
| DataPersistence | BaseRepository ABC, write-through JSON, asdict/dict 변환 |
| ConsoleMVC | OrderStatus Enum, App 메인 루프, FIFO 큐 |
| DataMonitor | 미처리 주문 기준 재고 상태 판단 로직 |
| DummyDataGenerator | Seed 기반 더미 데이터 생성 패턴 |

---

## Task 목록

### Task 1: 프로젝트 골격

디렉터리 생성, `__init__.py`, `tests/conftest.py` (tmp_data_dir fixture).

### Task 2: 모델 계층

- `model/sample.py` — Sample dataclass (sample_id, name, avg_production_time, yield_rate, stock)
- `model/order.py` — OrderStatus Enum (RESERVED/REJECTED/PRODUCING/CONFIRMED/RELEASE) + Order dataclass
- `model/production_job.py` — ProductionJob dataclass (order_id, sample_id, shortage, actual_production, total_time, enqueued_at)

주문 ID 형식: `ORD-YYYYMMDD-NNNN`

### Task 3: Repository 계층

- `repository/base_repository.py` — BaseRepository ABC (create/find_by_id/find_all/update/delete)
- `repository/sample_repository.py` — JSON write-through + find_by_name
- `repository/order_repository.py` — JSON write-through + find_by_status + count_by_status
- `repository/production_job_repository.py` — JSON write-through + find_first + count, find_all은 enqueued_at 오름차순 정렬

### Task 4: SampleController

register (중복 검사), find_by_id, find_all, search (이름 키워드), get_stock_status → "고갈"/"부족"/"여유"

### Task 5: OrderController

- `reserve` — 시료 존재 검사 → RESERVED 주문 생성
- `approve` — 재고 비교 → CONFIRMED 또는 (ProductionJob 생성 + PRODUCING)
- `reject` — REJECTED 전환
- `release` — CONFIRMED 검사 → RELEASE + stock 차감
- `list_reserved`, `list_confirmed`

### Task 6: ProductionController

- `complete_current` — 첫 번째 작업 완료: stock 증가 + PRODUCING→CONFIRMED + 작업 삭제
- `get_current` — 첫 번째 ProductionJob 반환
- `get_queue` — 두 번째 이후 작업 목록
- `get_queue_size`

### Task 7: MonitorController

- `get_order_stats` — 상태별 주문 수 (REJECTED 제외)
- `get_stock_status_all` — 시료별 재고 상태 (고갈/부족/여유)
- `get_summary` — 메인 헤더용 요약 (시료 수, 총 재고, 주문 수)

### Task 8: View 계층 + App + main.py

View는 출력/입력 전용, 로직 없음.

- `view/main_view.py` — 헤더(현재 시각, 요약) + 메뉴
- `view/sample_view.py` — 시료 관리 입출력
- `view/order_view.py` — 주문 접수/승인/거절/출고 입출력
- `view/production_view.py` — 생산현황 + 대기큐 출력
- `view/monitor_view.py` — 주문 통계 + 재고 현황 출력
- `app.py` — App 클래스: 각 Controller/View 조립, 메뉴 루프
- `main.py` — `App().run()` 호출

### Task 9: 더미 데이터 생성기

`generator.py` — 시료 5종, 주문 25건(상태 분포 포함), 생산작업 자동 생성.  
실행: `python generator.py`
