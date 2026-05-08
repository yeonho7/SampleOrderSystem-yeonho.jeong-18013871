# 반도체 시료 생산주문관리 시스템 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Python 3 콘솔 CLI 앱으로 시료 등록·주문 접수·승인·생산·출고를 통합 관리한다.

**Architecture:** MVC + Repository 패턴. View → Controller → Repository → Model 단방향 의존. JSON 파일 write-through 영속성.

**Tech Stack:** Python 3.11+, dataclass, Enum, collections.deque, json, pytest

---

## 파일 구조

```
sample_order_system/
├── main.py                              진입점
├── app.py                               App 클래스 (메인 루프)
├── data/                                JSON 데이터 (자동 생성)
│   ├── samples.json
│   ├── orders.json
│   └── production_jobs.json
├── model/
│   ├── __init__.py
│   ├── sample.py                        Sample dataclass
│   ├── order.py                         OrderStatus Enum + Order dataclass
│   └── production_job.py               ProductionJob dataclass
├── repository/
│   ├── __init__.py
│   ├── base_repository.py              BaseRepository ABC
│   ├── sample_repository.py
│   ├── order_repository.py
│   └── production_job_repository.py
├── controller/
│   ├── __init__.py
│   ├── sample_controller.py
│   ├── order_controller.py
│   ├── production_controller.py
│   └── monitor_controller.py
├── view/
│   ├── __init__.py
│   ├── main_view.py
│   ├── sample_view.py
│   ├── order_view.py
│   ├── production_view.py
│   └── monitor_view.py
└── tests/
    ├── conftest.py
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

## Task 1: 프로젝트 골격 설정

**Files:**
- Create: `model/__init__.py`, `repository/__init__.py`, `controller/__init__.py`, `view/__init__.py`
- Create: `tests/__init__.py`, `tests/repository/__init__.py`, `tests/controller/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: pytest 설치 확인**

```bash
.venv\Scripts\python.exe -m pip install pytest
```
Expected: `Successfully installed pytest-...` 또는 `Requirement already satisfied`

- [ ] **Step 2: 디렉터리 및 `__init__.py` 생성**

```bash
mkdir -p model repository controller view data tests/repository tests/controller
touch model/__init__.py repository/__init__.py controller/__init__.py view/__init__.py
touch tests/__init__.py tests/repository/__init__.py tests/controller/__init__.py
```

- [ ] **Step 3: `tests/conftest.py` 작성**

```python
import pytest
import json
from pathlib import Path


@pytest.fixture
def tmp_data_dir(tmp_path):
    for name in ("samples.json", "orders.json", "production_jobs.json"):
        (tmp_path / name).write_text("[]", encoding="utf-8")
    return tmp_path
```

- [ ] **Step 4: 빈 테스트 실행**

```bash
.venv\Scripts\python.exe -m pytest tests/ -v
```
Expected: `no tests ran` 또는 `0 passed`

- [ ] **Step 5: 커밋**

```bash
git add model/ repository/ controller/ view/ tests/ data/
git commit -m "chore: 프로젝트 골격 및 디렉터리 구조 생성"
```

---

## Task 2: 모델 계층

**Files:**
- Create: `model/sample.py`
- Create: `model/order.py`
- Create: `model/production_job.py`
- Test: `tests/test_model_order.py`

- [ ] **Step 1: 테스트 작성**

`tests/test_model_order.py`:
```python
from model.order import OrderStatus, Order
from datetime import datetime


def test_order_status_enum_values():
    assert OrderStatus.RESERVED.value == "RESERVED"
    assert OrderStatus.REJECTED.value == "REJECTED"
    assert OrderStatus.PRODUCING.value == "PRODUCING"
    assert OrderStatus.CONFIRMED.value == "CONFIRMED"
    assert OrderStatus.RELEASE.value == "RELEASE"


def test_order_default_status_is_reserved():
    o = Order(order_id="ORD-20260508-0001", sample_id="S-001",
               customer_name="테스트고객", quantity=10)
    assert o.status == OrderStatus.RESERVED


def test_order_created_at_is_set_automatically():
    o = Order(order_id="ORD-20260508-0001", sample_id="S-001",
               customer_name="테스트고객", quantity=10)
    assert o.created_at != ""
    assert o.updated_at != ""
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
.venv\Scripts\python.exe -m pytest tests/test_model_order.py -v
```
Expected: `ModuleNotFoundError: No module named 'model.order'`

- [ ] **Step 3: `model/sample.py` 작성**

```python
from dataclasses import dataclass, field


@dataclass
class Sample:
    sample_id: str
    name: str
    avg_production_time: float
    yield_rate: float
    stock: int = field(default=0)
```

- [ ] **Step 4: `model/order.py` 작성**

```python
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone


class OrderStatus(Enum):
    RESERVED = "RESERVED"
    REJECTED = "REJECTED"
    PRODUCING = "PRODUCING"
    CONFIRMED = "CONFIRMED"
    RELEASE = "RELEASE"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Order:
    order_id: str
    sample_id: str
    customer_name: str
    quantity: int
    status: OrderStatus = field(default=OrderStatus.RESERVED)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
```

- [ ] **Step 5: `model/production_job.py` 작성**

```python
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ProductionJob:
    order_id: str
    sample_id: str
    shortage: int
    actual_production: int
    total_time: float
    enqueued_at: str = field(default_factory=_now_iso)
```

- [ ] **Step 6: 테스트 통과 확인**

```bash
.venv\Scripts\python.exe -m pytest tests/test_model_order.py -v
```
Expected: `3 passed`

- [ ] **Step 7: 커밋**

```bash
git add model/
git commit -m "feat: 모델 계층 구현 (Sample, Order, OrderStatus, ProductionJob)"
```

---

## Task 3: Repository 계층

**Files:**
- Create: `repository/base_repository.py`
- Create: `repository/sample_repository.py`
- Create: `repository/order_repository.py`
- Create: `repository/production_job_repository.py`
- Test: `tests/repository/test_sample_repository.py`
- Test: `tests/repository/test_order_repository.py`
- Test: `tests/repository/test_production_job_repository.py`

- [ ] **Step 1: 테스트 작성 — SampleRepository**

`tests/repository/test_sample_repository.py`:
```python
import pytest
from model.sample import Sample
from repository.sample_repository import SampleRepository


def test_create_and_find_by_id(tmp_data_dir):
    repo = SampleRepository(tmp_data_dir / "samples.json")
    s = Sample(sample_id="S-001", name="실리콘웨이퍼", avg_production_time=5.0, yield_rate=0.9, stock=100)
    repo.create(s)
    found = repo.find_by_id("S-001")
    assert found is not None
    assert found.name == "실리콘웨이퍼"
    assert found.stock == 100


def test_find_all_returns_all(tmp_data_dir):
    repo = SampleRepository(tmp_data_dir / "samples.json")
    repo.create(Sample("S-001", "A", 1.0, 0.9, 10))
    repo.create(Sample("S-002", "B", 2.0, 0.8, 20))
    assert len(repo.find_all()) == 2


def test_update_modifies_stock(tmp_data_dir):
    repo = SampleRepository(tmp_data_dir / "samples.json")
    s = Sample("S-001", "A", 1.0, 0.9, 10)
    repo.create(s)
    s.stock = 50
    repo.update(s)
    assert repo.find_by_id("S-001").stock == 50


def test_find_by_id_returns_none_if_missing(tmp_data_dir):
    repo = SampleRepository(tmp_data_dir / "samples.json")
    assert repo.find_by_id("S-999") is None
```

- [ ] **Step 2: 테스트 작성 — OrderRepository**

`tests/repository/test_order_repository.py`:
```python
import pytest
from model.order import Order, OrderStatus
from repository.order_repository import OrderRepository


def test_create_and_find_by_id(tmp_data_dir):
    repo = OrderRepository(tmp_data_dir / "orders.json")
    o = Order("ORD-20260508-0001", "S-001", "고객A", 10)
    repo.create(o)
    found = repo.find_by_id("ORD-20260508-0001")
    assert found is not None
    assert found.status == OrderStatus.RESERVED


def test_find_by_status(tmp_data_dir):
    repo = OrderRepository(tmp_data_dir / "orders.json")
    repo.create(Order("ORD-20260508-0001", "S-001", "고객A", 10, status=OrderStatus.RESERVED))
    repo.create(Order("ORD-20260508-0002", "S-001", "고객B", 20, status=OrderStatus.CONFIRMED))
    reserved = repo.find_by_status(OrderStatus.RESERVED)
    assert len(reserved) == 1
    assert reserved[0].order_id == "ORD-20260508-0001"


def test_update_status(tmp_data_dir):
    repo = OrderRepository(tmp_data_dir / "orders.json")
    o = Order("ORD-20260508-0001", "S-001", "고객A", 10)
    repo.create(o)
    o.status = OrderStatus.CONFIRMED
    repo.update(o)
    assert repo.find_by_id("ORD-20260508-0001").status == OrderStatus.CONFIRMED
```

- [ ] **Step 3: 테스트 작성 — ProductionJobRepository**

`tests/repository/test_production_job_repository.py`:
```python
import pytest
from model.production_job import ProductionJob
from repository.production_job_repository import ProductionJobRepository


def test_create_and_find_first(tmp_data_dir):
    repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
    j = ProductionJob("ORD-0001", "S-001", 50, 60, 300.0)
    repo.create(j)
    first = repo.find_first()
    assert first is not None
    assert first.order_id == "ORD-0001"


def test_fifo_order(tmp_data_dir):
    repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
    import time
    j1 = ProductionJob("ORD-0001", "S-001", 10, 12, 60.0)
    time.sleep(0.01)
    j2 = ProductionJob("ORD-0002", "S-001", 20, 24, 120.0)
    repo.create(j1)
    repo.create(j2)
    assert repo.find_first().order_id == "ORD-0001"


def test_delete_removes_job(tmp_data_dir):
    repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
    j = ProductionJob("ORD-0001", "S-001", 10, 12, 60.0)
    repo.create(j)
    repo.delete("ORD-0001")
    assert repo.find_first() is None


def test_count_returns_queue_length(tmp_data_dir):
    repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
    repo.create(ProductionJob("ORD-0001", "S-001", 10, 12, 60.0))
    repo.create(ProductionJob("ORD-0002", "S-001", 20, 24, 120.0))
    assert repo.count() == 2
```

- [ ] **Step 4: 테스트 실패 확인**

```bash
.venv\Scripts\python.exe -m pytest tests/repository/ -v
```
Expected: `ImportError` 또는 `ModuleNotFoundError`

- [ ] **Step 5: `repository/base_repository.py` 작성**

```python
from abc import ABC, abstractmethod


class BaseRepository(ABC):
    @abstractmethod
    def create(self, entity) -> None: ...

    @abstractmethod
    def find_by_id(self, entity_id: str): ...

    @abstractmethod
    def find_all(self) -> list: ...

    @abstractmethod
    def update(self, entity) -> bool: ...

    @abstractmethod
    def delete(self, entity_id: str) -> bool: ...
```

- [ ] **Step 6: `repository/sample_repository.py` 작성**

```python
import json
import os
from dataclasses import asdict
from model.sample import Sample
from repository.base_repository import BaseRepository


class SampleRepository(BaseRepository):
    def __init__(self, filepath: str = "data/samples.json"):
        self._filepath = str(filepath)
        os.makedirs(os.path.dirname(self._filepath), exist_ok=True)
        if not os.path.exists(self._filepath):
            self._write([])

    def _read(self) -> list[dict]:
        with open(self._filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: list[dict]) -> None:
        with open(self._filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def create(self, entity: Sample) -> None:
        data = self._read()
        data.append(asdict(entity))
        self._write(data)

    def find_by_id(self, entity_id: str) -> Sample | None:
        for item in self._read():
            if item["sample_id"] == entity_id:
                return Sample(**item)
        return None

    def find_all(self) -> list[Sample]:
        return [Sample(**item) for item in self._read()]

    def update(self, entity: Sample) -> bool:
        data = self._read()
        for i, item in enumerate(data):
            if item["sample_id"] == entity.sample_id:
                data[i] = asdict(entity)
                self._write(data)
                return True
        return False

    def delete(self, entity_id: str) -> bool:
        data = self._read()
        new_data = [item for item in data if item["sample_id"] != entity_id]
        if len(new_data) == len(data):
            return False
        self._write(new_data)
        return True

    def find_by_name(self, keyword: str) -> list[Sample]:
        lower = keyword.lower()
        return [Sample(**item) for item in self._read() if lower in item["name"].lower()]
```

- [ ] **Step 7: `repository/order_repository.py` 작성**

```python
import json
import os
from dataclasses import asdict
from model.order import Order, OrderStatus
from repository.base_repository import BaseRepository


def _serialize(order: Order) -> dict:
    d = asdict(order)
    d["status"] = order.status.value
    return d


def _deserialize(item: dict) -> Order:
    item = dict(item)
    item["status"] = OrderStatus(item["status"])
    return Order(**item)


class OrderRepository(BaseRepository):
    def __init__(self, filepath: str = "data/orders.json"):
        self._filepath = str(filepath)
        os.makedirs(os.path.dirname(self._filepath), exist_ok=True)
        if not os.path.exists(self._filepath):
            self._write([])

    def _read(self) -> list[dict]:
        with open(self._filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: list[dict]) -> None:
        with open(self._filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def create(self, entity: Order) -> None:
        data = self._read()
        data.append(_serialize(entity))
        self._write(data)

    def find_by_id(self, entity_id: str) -> Order | None:
        for item in self._read():
            if item["order_id"] == entity_id:
                return _deserialize(item)
        return None

    def find_all(self) -> list[Order]:
        return [_deserialize(item) for item in self._read()]

    def find_by_status(self, status: OrderStatus) -> list[Order]:
        return [o for o in self.find_all() if o.status == status]

    def update(self, entity: Order) -> bool:
        data = self._read()
        for i, item in enumerate(data):
            if item["order_id"] == entity.order_id:
                data[i] = _serialize(entity)
                self._write(data)
                return True
        return False

    def delete(self, entity_id: str) -> bool:
        data = self._read()
        new_data = [item for item in data if item["order_id"] != entity_id]
        if len(new_data) == len(data):
            return False
        self._write(new_data)
        return True

    def count_by_status(self) -> dict[str, int]:
        counts = {s.value: 0 for s in OrderStatus if s != OrderStatus.REJECTED}
        for order in self.find_all():
            if order.status != OrderStatus.REJECTED:
                counts[order.status.value] += 1
        return counts
```

- [ ] **Step 8: `repository/production_job_repository.py` 작성**

```python
import json
import os
from dataclasses import asdict
from model.production_job import ProductionJob
from repository.base_repository import BaseRepository


class ProductionJobRepository(BaseRepository):
    def __init__(self, filepath: str = "data/production_jobs.json"):
        self._filepath = str(filepath)
        os.makedirs(os.path.dirname(self._filepath), exist_ok=True)
        if not os.path.exists(self._filepath):
            self._write([])

    def _read(self) -> list[dict]:
        with open(self._filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: list[dict]) -> None:
        with open(self._filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def create(self, entity: ProductionJob) -> None:
        data = self._read()
        data.append(asdict(entity))
        self._write(data)

    def find_by_id(self, entity_id: str) -> ProductionJob | None:
        for item in self._read():
            if item["order_id"] == entity_id:
                return ProductionJob(**item)
        return None

    def find_all(self) -> list[ProductionJob]:
        items = sorted(self._read(), key=lambda x: x["enqueued_at"])
        return [ProductionJob(**item) for item in items]

    def find_first(self) -> ProductionJob | None:
        jobs = self.find_all()
        return jobs[0] if jobs else None

    def count(self) -> int:
        return len(self._read())

    def update(self, entity: ProductionJob) -> bool:
        data = self._read()
        for i, item in enumerate(data):
            if item["order_id"] == entity.order_id:
                data[i] = asdict(entity)
                self._write(data)
                return True
        return False

    def delete(self, entity_id: str) -> bool:
        data = self._read()
        new_data = [item for item in data if item["order_id"] != entity_id]
        if len(new_data) == len(data):
            return False
        self._write(new_data)
        return True
```

- [ ] **Step 9: 테스트 통과 확인**

```bash
.venv\Scripts\python.exe -m pytest tests/repository/ -v
```
Expected: `10 passed`

- [ ] **Step 10: 커밋**

```bash
git add repository/ tests/repository/
git commit -m "feat: Repository 계층 구현 (BaseRepository ABC + JSON CRUD 3종)"
```

---

## Task 4: SampleController

**Files:**
- Create: `controller/sample_controller.py`
- Test: `tests/controller/test_sample_controller.py`

- [ ] **Step 1: 테스트 작성**

`tests/controller/test_sample_controller.py`:
```python
import pytest
from repository.sample_repository import SampleRepository
from controller.sample_controller import SampleController


def make_ctrl(tmp_data_dir):
    repo = SampleRepository(tmp_data_dir / "samples.json")
    return SampleController(repo)


def test_register_creates_sample(tmp_data_dir):
    ctrl = make_ctrl(tmp_data_dir)
    s = ctrl.register("S-001", "실리콘웨이퍼", 5.0, 0.9)
    assert s.sample_id == "S-001"
    assert s.stock == 0


def test_register_duplicate_raises(tmp_data_dir):
    ctrl = make_ctrl(tmp_data_dir)
    ctrl.register("S-001", "실리콘웨이퍼", 5.0, 0.9)
    with pytest.raises(ValueError, match="이미 존재"):
        ctrl.register("S-001", "다른이름", 1.0, 0.8)


def test_search_by_name(tmp_data_dir):
    ctrl = make_ctrl(tmp_data_dir)
    ctrl.register("S-001", "실리콘웨이퍼", 5.0, 0.9)
    ctrl.register("S-002", "갈륨비소", 3.0, 0.85)
    result = ctrl.search("실리콘")
    assert len(result) == 1
    assert result[0].sample_id == "S-001"


def test_get_stock_status(tmp_data_dir):
    ctrl = make_ctrl(tmp_data_dir)
    ctrl.register("S-001", "A", 1.0, 0.9)
    repo = SampleRepository(tmp_data_dir / "samples.json")
    s = repo.find_by_id("S-001")
    s.stock = 0
    repo.update(s)
    assert ctrl.get_stock_status("S-001", 10) == "고갈"

    s.stock = 5
    repo.update(s)
    assert ctrl.get_stock_status("S-001", 10) == "부족"

    s.stock = 20
    repo.update(s)
    assert ctrl.get_stock_status("S-001", 10) == "여유"
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
.venv\Scripts\python.exe -m pytest tests/controller/test_sample_controller.py -v
```
Expected: `ImportError`

- [ ] **Step 3: `controller/sample_controller.py` 작성**

```python
from model.sample import Sample
from repository.sample_repository import SampleRepository


class SampleController:
    def __init__(self, repo: SampleRepository):
        self._repo = repo

    def register(self, sample_id: str, name: str, avg_production_time: float, yield_rate: float) -> Sample:
        if self._repo.find_by_id(sample_id) is not None:
            raise ValueError(f"이미 존재하는 시료 ID: {sample_id}")
        s = Sample(sample_id=sample_id, name=name,
                   avg_production_time=avg_production_time, yield_rate=yield_rate)
        self._repo.create(s)
        return s

    def find_by_id(self, sample_id: str) -> Sample | None:
        return self._repo.find_by_id(sample_id)

    def find_all(self) -> list[Sample]:
        return self._repo.find_all()

    def search(self, keyword: str) -> list[Sample]:
        return self._repo.find_by_name(keyword)

    def get_stock_status(self, sample_id: str, active_order_qty: int) -> str:
        s = self._repo.find_by_id(sample_id)
        if s is None:
            raise ValueError(f"존재하지 않는 시료 ID: {sample_id}")
        if s.stock == 0:
            return "고갈"
        if s.stock < active_order_qty:
            return "부족"
        return "여유"
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
.venv\Scripts\python.exe -m pytest tests/controller/test_sample_controller.py -v
```
Expected: `4 passed`

- [ ] **Step 5: 커밋**

```bash
git add controller/sample_controller.py tests/controller/test_sample_controller.py
git commit -m "feat: SampleController 구현 (등록/조회/검색/재고상태)"
```

---

## Task 5: OrderController

**Files:**
- Create: `controller/order_controller.py`
- Test: `tests/controller/test_order_controller.py`

PRD 비즈니스 로직:
- `reserve`: 시료 존재 여부 검사 → RESERVED 주문 생성, ID = `ORD-YYYYMMDD-NNNN`
- `approve`: 재고 ≥ 수량 → CONFIRMED / 재고 < 수량 → ProductionJob 생성 + PRODUCING
- `reject`: RESERVED → REJECTED
- `release`: CONFIRMED → RELEASE + stock -= quantity
- 생산량 공식: `ceil(부족분 / (수율 × 0.9))`

- [ ] **Step 1: 테스트 작성**

`tests/controller/test_order_controller.py`:
```python
import pytest
from model.order import OrderStatus
from model.sample import Sample
from repository.sample_repository import SampleRepository
from repository.order_repository import OrderRepository
from repository.production_job_repository import ProductionJobRepository
from controller.order_controller import OrderController
import math


def make_ctrl(tmp_data_dir, stock=100):
    sample_repo = SampleRepository(tmp_data_dir / "samples.json")
    order_repo = OrderRepository(tmp_data_dir / "orders.json")
    job_repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
    sample_repo.create(Sample("S-001", "실리콘웨이퍼", 5.0, 0.9, stock))
    return OrderController(sample_repo, order_repo, job_repo), order_repo, sample_repo, job_repo


def test_reserve_creates_reserved_order(tmp_data_dir):
    ctrl, order_repo, *_ = make_ctrl(tmp_data_dir)
    order = ctrl.reserve("S-001", "고객A", 10)
    assert order.status == OrderStatus.RESERVED
    assert order.order_id.startswith("ORD-")
    assert order.customer_name == "고객A"


def test_reserve_unknown_sample_raises(tmp_data_dir):
    ctrl, *_ = make_ctrl(tmp_data_dir)
    with pytest.raises(ValueError, match="존재하지 않는 시료"):
        ctrl.reserve("S-999", "고객A", 10)


def test_approve_with_sufficient_stock_sets_confirmed(tmp_data_dir):
    ctrl, order_repo, *_ = make_ctrl(tmp_data_dir, stock=100)
    order = ctrl.reserve("S-001", "고객A", 10)
    result = ctrl.approve(order.order_id)
    assert result["order"].status == OrderStatus.CONFIRMED
    assert result["path"] == "confirmed"


def test_approve_with_insufficient_stock_sets_producing(tmp_data_dir):
    ctrl, order_repo, sample_repo, job_repo = make_ctrl(tmp_data_dir, stock=5)
    order = ctrl.reserve("S-001", "고객A", 50)
    result = ctrl.approve(order.order_id)
    assert result["order"].status == OrderStatus.PRODUCING
    assert result["path"] == "producing"
    job = result["job"]
    assert job.shortage == 45  # 50 - 5
    expected_actual = math.ceil(45 / (0.9 * 0.9))
    assert job.actual_production == expected_actual


def test_reject_sets_rejected(tmp_data_dir):
    ctrl, order_repo, *_ = make_ctrl(tmp_data_dir)
    order = ctrl.reserve("S-001", "고객A", 10)
    result = ctrl.reject(order.order_id)
    assert result.status == OrderStatus.REJECTED


def test_release_sets_release_and_decrements_stock(tmp_data_dir):
    ctrl, order_repo, sample_repo, *_ = make_ctrl(tmp_data_dir, stock=100)
    order = ctrl.reserve("S-001", "고객A", 30)
    ctrl.approve(order.order_id)
    ctrl.release(order.order_id)
    released = order_repo.find_by_id(order.order_id)
    assert released.status == OrderStatus.RELEASE
    s = sample_repo.find_by_id("S-001")
    assert s.stock == 70  # 100 - 30


def test_release_non_confirmed_raises(tmp_data_dir):
    ctrl, *_ = make_ctrl(tmp_data_dir)
    order = ctrl.reserve("S-001", "고객A", 10)
    with pytest.raises(ValueError, match="CONFIRMED 상태"):
        ctrl.release(order.order_id)
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
.venv\Scripts\python.exe -m pytest tests/controller/test_order_controller.py -v
```
Expected: `ImportError`

- [ ] **Step 3: `controller/order_controller.py` 작성**

```python
import math
from datetime import datetime, timezone, date
from model.order import Order, OrderStatus
from model.production_job import ProductionJob
from repository.sample_repository import SampleRepository
from repository.order_repository import OrderRepository
from repository.production_job_repository import ProductionJobRepository


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class OrderController:
    def __init__(self, sample_repo: SampleRepository, order_repo: OrderRepository,
                 job_repo: ProductionJobRepository):
        self._sample_repo = sample_repo
        self._order_repo = order_repo
        self._job_repo = job_repo

    def _next_order_id(self) -> str:
        today = date.today().strftime("%Y%m%d")
        existing = [o for o in self._order_repo.find_all()
                    if o.order_id.startswith(f"ORD-{today}-")]
        seq = len(existing) + 1
        return f"ORD-{today}-{seq:04d}"

    def reserve(self, sample_id: str, customer_name: str, quantity: int) -> Order:
        if self._sample_repo.find_by_id(sample_id) is None:
            raise ValueError(f"존재하지 않는 시료 ID: {sample_id}")
        order = Order(order_id=self._next_order_id(), sample_id=sample_id,
                      customer_name=customer_name, quantity=quantity)
        self._order_repo.create(order)
        return order

    def approve(self, order_id: str) -> dict:
        order = self._order_repo.find_by_id(order_id)
        if order is None:
            raise ValueError(f"존재하지 않는 주문 ID: {order_id}")
        sample = self._sample_repo.find_by_id(order.sample_id)
        now = _now_iso()

        if sample.stock >= order.quantity:
            order.status = OrderStatus.CONFIRMED
            order.updated_at = now
            self._order_repo.update(order)
            return {"path": "confirmed", "order": order}
        else:
            shortage = order.quantity - sample.stock
            actual_production = math.ceil(shortage / (sample.yield_rate * 0.9))
            total_time = sample.avg_production_time * actual_production
            job = ProductionJob(order_id=order_id, sample_id=order.sample_id,
                                shortage=shortage, actual_production=actual_production,
                                total_time=total_time)
            self._job_repo.create(job)
            order.status = OrderStatus.PRODUCING
            order.updated_at = now
            self._order_repo.update(order)
            return {"path": "producing", "order": order, "job": job}

    def reject(self, order_id: str) -> Order:
        order = self._order_repo.find_by_id(order_id)
        if order is None:
            raise ValueError(f"존재하지 않는 주문 ID: {order_id}")
        order.status = OrderStatus.REJECTED
        order.updated_at = _now_iso()
        self._order_repo.update(order)
        return order

    def release(self, order_id: str) -> Order:
        order = self._order_repo.find_by_id(order_id)
        if order is None:
            raise ValueError(f"존재하지 않는 주문 ID: {order_id}")
        if order.status != OrderStatus.CONFIRMED:
            raise ValueError(f"출고는 CONFIRMED 상태에서만 가능합니다. 현재: {order.status.value}")
        sample = self._sample_repo.find_by_id(order.sample_id)
        sample.stock -= order.quantity
        self._sample_repo.update(sample)
        order.status = OrderStatus.RELEASE
        order.updated_at = _now_iso()
        self._order_repo.update(order)
        return order

    def list_reserved(self) -> list[Order]:
        return self._order_repo.find_by_status(OrderStatus.RESERVED)

    def list_confirmed(self) -> list[Order]:
        return self._order_repo.find_by_status(OrderStatus.CONFIRMED)
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
.venv\Scripts\python.exe -m pytest tests/controller/test_order_controller.py -v
```
Expected: `7 passed`

- [ ] **Step 5: 커밋**

```bash
git add controller/order_controller.py tests/controller/test_order_controller.py
git commit -m "feat: OrderController 구현 (접수/승인/거절/출고, 생산 로직 포함)"
```

---

## Task 6: ProductionController

**Files:**
- Create: `controller/production_controller.py`
- Test: `tests/controller/test_production_controller.py`

생산 완료 처리 시: 재고 += actual_production, 주문 PRODUCING→CONFIRMED, 작업 삭제

- [ ] **Step 1: 테스트 작성**

`tests/controller/test_production_controller.py`:
```python
import pytest
from model.order import OrderStatus
from model.sample import Sample
from model.production_job import ProductionJob
from repository.sample_repository import SampleRepository
from repository.order_repository import OrderRepository
from repository.production_job_repository import ProductionJobRepository
from controller.order_controller import OrderController
from controller.production_controller import ProductionController


def setup(tmp_data_dir, stock=5):
    sample_repo = SampleRepository(tmp_data_dir / "samples.json")
    order_repo = OrderRepository(tmp_data_dir / "orders.json")
    job_repo = ProductionJobRepository(tmp_data_dir / "production_jobs.json")
    sample_repo.create(Sample("S-001", "A", 5.0, 0.9, stock))
    order_ctrl = OrderController(sample_repo, order_repo, job_repo)
    prod_ctrl = ProductionController(sample_repo, order_repo, job_repo)
    return order_ctrl, prod_ctrl, sample_repo, order_repo, job_repo


def test_complete_current_updates_order_and_stock(tmp_data_dir):
    order_ctrl, prod_ctrl, sample_repo, order_repo, job_repo = setup(tmp_data_dir, stock=5)
    order = order_ctrl.reserve("S-001", "고객A", 50)
    result = order_ctrl.approve(order.order_id)
    job = result["job"]

    completed = prod_ctrl.complete_current()
    assert completed is not None
    assert completed.status == OrderStatus.CONFIRMED

    s = sample_repo.find_by_id("S-001")
    assert s.stock == 5 + job.actual_production

    assert job_repo.find_first() is None


def test_complete_current_returns_none_when_no_jobs(tmp_data_dir):
    _, prod_ctrl, *_ = setup(tmp_data_dir)
    assert prod_ctrl.complete_current() is None


def test_get_current_returns_first_job(tmp_data_dir):
    order_ctrl, prod_ctrl, *_ = setup(tmp_data_dir, stock=0)
    order = order_ctrl.reserve("S-001", "고객A", 50)
    order_ctrl.approve(order.order_id)
    current = prod_ctrl.get_current()
    assert current is not None
    assert current.order_id == order.order_id


def test_get_queue_excludes_first(tmp_data_dir):
    order_ctrl, prod_ctrl, *_ = setup(tmp_data_dir, stock=0)
    import time
    for i in range(3):
        o = order_ctrl.reserve("S-001", f"고객{i}", 50)
        order_ctrl.approve(o.order_id)
        time.sleep(0.01)
    queue = prod_ctrl.get_queue()
    assert len(queue) == 2
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
.venv\Scripts\python.exe -m pytest tests/controller/test_production_controller.py -v
```
Expected: `ImportError`

- [ ] **Step 3: `controller/production_controller.py` 작성**

```python
from datetime import datetime, timezone
from model.order import OrderStatus
from repository.sample_repository import SampleRepository
from repository.order_repository import OrderRepository
from repository.production_job_repository import ProductionJobRepository
from model.production_job import ProductionJob
from model.order import Order


class ProductionController:
    def __init__(self, sample_repo: SampleRepository, order_repo: OrderRepository,
                 job_repo: ProductionJobRepository):
        self._sample_repo = sample_repo
        self._order_repo = order_repo
        self._job_repo = job_repo

    def complete_current(self) -> Order | None:
        job = self._job_repo.find_first()
        if job is None:
            return None
        sample = self._sample_repo.find_by_id(job.sample_id)
        sample.stock += job.actual_production
        self._sample_repo.update(sample)

        order = self._order_repo.find_by_id(job.order_id)
        order.status = OrderStatus.CONFIRMED
        order.updated_at = datetime.now(timezone.utc).isoformat()
        self._order_repo.update(order)

        self._job_repo.delete(job.order_id)
        return order

    def get_current(self) -> ProductionJob | None:
        return self._job_repo.find_first()

    def get_queue(self) -> list[ProductionJob]:
        all_jobs = self._job_repo.find_all()
        return all_jobs[1:] if len(all_jobs) > 1 else []

    def get_queue_size(self) -> int:
        return self._job_repo.count()
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
.venv\Scripts\python.exe -m pytest tests/controller/test_production_controller.py -v
```
Expected: `4 passed`

- [ ] **Step 5: 커밋**

```bash
git add controller/production_controller.py tests/controller/test_production_controller.py
git commit -m "feat: ProductionController 구현 (FIFO 생산 완료/큐 조회)"
```

---

## Task 7: MonitorController

**Files:**
- Create: `controller/monitor_controller.py`
- Test: `tests/controller/test_monitor_controller.py`

재고 상태 기준 (CLAUDE.md): stock==0→고갈, stock<미처리주문합계→부족, 그 외→여유
미처리 주문: RESERVED + PRODUCING 상태 주문 수량 합계

- [ ] **Step 1: 테스트 작성**

`tests/controller/test_monitor_controller.py`:
```python
import pytest
from model.sample import Sample
from model.order import Order, OrderStatus
from repository.sample_repository import SampleRepository
from repository.order_repository import OrderRepository
from controller.monitor_controller import MonitorController


def make_ctrl(tmp_data_dir):
    sample_repo = SampleRepository(tmp_data_dir / "samples.json")
    order_repo = OrderRepository(tmp_data_dir / "orders.json")
    return MonitorController(sample_repo, order_repo), sample_repo, order_repo


def test_order_stats_excludes_rejected(tmp_data_dir):
    ctrl, sample_repo, order_repo = make_ctrl(tmp_data_dir)
    sample_repo.create(Sample("S-001", "A", 1.0, 0.9, 100))
    order_repo.create(Order("ORD-001", "S-001", "고객A", 10, status=OrderStatus.RESERVED))
    order_repo.create(Order("ORD-002", "S-001", "고객B", 10, status=OrderStatus.REJECTED))
    stats = ctrl.get_order_stats()
    assert stats["RESERVED"] == 1
    assert "REJECTED" not in stats


def test_stock_status_depleted(tmp_data_dir):
    ctrl, sample_repo, _ = make_ctrl(tmp_data_dir)
    sample_repo.create(Sample("S-001", "A", 1.0, 0.9, 0))
    result = ctrl.get_stock_status_all()
    assert result[0]["status"] == "고갈"


def test_stock_status_short(tmp_data_dir):
    ctrl, sample_repo, order_repo = make_ctrl(tmp_data_dir)
    sample_repo.create(Sample("S-001", "A", 1.0, 0.9, 5))
    order_repo.create(Order("ORD-001", "S-001", "고객A", 50, status=OrderStatus.RESERVED))
    result = ctrl.get_stock_status_all()
    assert result[0]["status"] == "부족"


def test_stock_status_surplus(tmp_data_dir):
    ctrl, sample_repo, order_repo = make_ctrl(tmp_data_dir)
    sample_repo.create(Sample("S-001", "A", 1.0, 0.9, 100))
    order_repo.create(Order("ORD-001", "S-001", "고객A", 10, status=OrderStatus.RESERVED))
    result = ctrl.get_stock_status_all()
    assert result[0]["status"] == "여유"
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
.venv\Scripts\python.exe -m pytest tests/controller/test_monitor_controller.py -v
```
Expected: `ImportError`

- [ ] **Step 3: `controller/monitor_controller.py` 작성**

```python
from model.order import OrderStatus
from repository.sample_repository import SampleRepository
from repository.order_repository import OrderRepository


_ACTIVE_STATUSES = {OrderStatus.RESERVED, OrderStatus.PRODUCING}
_MONITORED_STATUSES = {s for s in OrderStatus if s != OrderStatus.REJECTED}


class MonitorController:
    def __init__(self, sample_repo: SampleRepository, order_repo: OrderRepository):
        self._sample_repo = sample_repo
        self._order_repo = order_repo

    def get_order_stats(self) -> dict[str, int]:
        counts = {s.value: 0 for s in _MONITORED_STATUSES}
        for order in self._order_repo.find_all():
            if order.status in _MONITORED_STATUSES:
                counts[order.status.value] += 1
        return counts

    def get_stock_status_all(self) -> list[dict]:
        samples = self._sample_repo.find_all()
        active_orders = [o for o in self._order_repo.find_all()
                         if o.status in _ACTIVE_STATUSES]
        result = []
        for sample in samples:
            active_qty = sum(o.quantity for o in active_orders
                             if o.sample_id == sample.sample_id)
            if sample.stock == 0:
                status = "고갈"
            elif sample.stock < active_qty:
                status = "부족"
            else:
                status = "여유"
            result.append({
                "sample": sample,
                "active_order_qty": active_qty,
                "status": status,
            })
        return result

    def get_summary(self) -> dict:
        samples = self._sample_repo.find_all()
        orders = self._order_repo.find_all()
        monitored = [o for o in orders if o.status in _MONITORED_STATUSES]
        return {
            "sample_count": len(samples),
            "total_stock": sum(s.stock for s in samples),
            "total_orders": len(monitored),
        }
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
.venv\Scripts\python.exe -m pytest tests/controller/test_monitor_controller.py -v
```
Expected: `4 passed`

- [ ] **Step 5: 커밋**

```bash
git add controller/monitor_controller.py tests/controller/test_monitor_controller.py
git commit -m "feat: MonitorController 구현 (주문 통계/재고 상태 집계)"
```

---

## Task 8: View 계층 + App + main.py

**Files:**
- Create: `view/main_view.py`, `view/sample_view.py`, `view/order_view.py`
- Create: `view/production_view.py`, `view/monitor_view.py`
- Create: `app.py`, `main.py`

View는 출력 전용, 로직 없음. 모든 입력은 `input()`으로 받아 Controller로 전달.

- [ ] **Step 1: `view/main_view.py` 작성**

```python
from datetime import datetime


class MainView:
    def show_header(self, summary: dict) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{'='*50}")
        print(f"  S-Semi 시료 생산주문관리 시스템")
        print(f"  현재 시각: {now}")
        print(f"  등록 시료: {summary['sample_count']}종  |  총 재고: {summary['total_stock']}ea")
        print(f"  전체 주문: {summary['total_orders']}건  |  생산 대기: {summary['queue_count']}건")
        print(f"{'='*50}")

    def show_menu(self) -> None:
        print("\n[메뉴]")
        print("  1. 시료 관리")
        print("  2. 시료 주문")
        print("  3. 주문 승인/거절")
        print("  4. 모니터링")
        print("  5. 생산라인 조회")
        print("  6. 출고 처리")
        print("  0. 종료")

    def get_choice(self) -> str:
        return input("\n선택: ").strip()
```

- [ ] **Step 2: `view/sample_view.py` 작성**

```python
from model.sample import Sample


class SampleView:
    def show_menu(self) -> None:
        print("\n[시료 관리]")
        print("  1. 시료 등록")
        print("  2. 시료 목록 조회")
        print("  3. 시료 검색")
        print("  0. 뒤로")

    def get_choice(self) -> str:
        return input("선택: ").strip()

    def get_register_input(self) -> dict:
        print("\n[시료 등록]")
        return {
            "sample_id": input("시료 ID (예: S-001): ").strip(),
            "name": input("시료명: ").strip(),
            "avg_production_time": float(input("평균 생산시간 (min/ea): ").strip()),
            "yield_rate": float(input("수율 (0.0~1.0): ").strip()),
        }

    def show_register_result(self, sample: Sample) -> None:
        print(f"\n✔ 시료 등록 완료: {sample.sample_id} - {sample.name}")

    def show_sample_list(self, samples: list[Sample]) -> None:
        if not samples:
            print("\n등록된 시료가 없습니다.")
            return
        print(f"\n{'ID':<10} {'시료명':<20} {'생산시간':>8} {'수율':>6} {'재고':>6}")
        print("-" * 60)
        for s in samples:
            print(f"{s.sample_id:<10} {s.name:<20} {s.avg_production_time:>8.1f} {s.yield_rate:>6.2f} {s.stock:>6}")

    def get_search_keyword(self) -> str:
        return input("검색 키워드: ").strip()

    def show_error(self, msg: str) -> None:
        print(f"\n[오류] {msg}")
```

- [ ] **Step 3: `view/order_view.py` 작성**

```python
from model.order import Order, OrderStatus
from model.production_job import ProductionJob


class OrderView:
    def show_reserve_menu(self) -> dict:
        print("\n[시료 주문 접수]")
        return {
            "sample_id": input("시료 ID: ").strip(),
            "customer_name": input("고객명: ").strip(),
            "quantity": int(input("주문 수량 (ea): ").strip()),
        }

    def show_reserve_result(self, order: Order) -> None:
        print(f"\n✔ 주문 접수 완료")
        print(f"  주문번호: {order.order_id}")
        print(f"  상태: {order.status.value}")

    def show_reserved_list(self, orders: list[Order], sample_name_map: dict) -> None:
        if not orders:
            print("\n승인 대기 중인 주문이 없습니다.")
            return
        print(f"\n{'번호':<4} {'주문번호':<22} {'고객명':<12} {'시료명':<15} {'수량':>6} {'상태'}")
        print("-" * 75)
        for i, o in enumerate(orders, 1):
            name = sample_name_map.get(o.sample_id, o.sample_id)
            print(f"{i:<4} {o.order_id:<22} {o.customer_name:<12} {name:<15} {o.quantity:>6} {o.status.value}")

    def get_order_id_input(self, prompt: str = "주문번호: ") -> str:
        return input(prompt).strip()

    def show_approve_confirmed(self, order: Order) -> None:
        print(f"\n✔ 주문 승인 (재고 충분)")
        print(f"  주문번호: {order.order_id}  →  상태: {order.status.value}")

    def show_approve_producing(self, order: Order, job: ProductionJob) -> None:
        print(f"\n✔ 주문 승인 (재고 부족 → 생산 등록)")
        print(f"  주문번호:  {order.order_id}")
        print(f"  부족분:    {job.shortage}ea")
        print(f"  실 생산량: {job.actual_production}ea")
        print(f"  예상 시간: {job.total_time:.1f}분")

    def show_reject_result(self, order: Order) -> None:
        print(f"\n✔ 주문 거절: {order.order_id}  →  {order.status.value}")

    def show_confirmed_list(self, orders: list[Order], sample_name_map: dict) -> None:
        if not orders:
            print("\n출고 대기 주문이 없습니다.")
            return
        print(f"\n{'번호':<4} {'주문번호':<22} {'고객명':<12} {'시료명':<15} {'수량':>6}")
        print("-" * 65)
        for i, o in enumerate(orders, 1):
            name = sample_name_map.get(o.sample_id, o.sample_id)
            print(f"{i:<4} {o.order_id:<22} {o.customer_name:<12} {name:<15} {o.quantity:>6}")

    def show_release_result(self, order: Order) -> None:
        print(f"\n✔ 출고 처리 완료")
        print(f"  주문번호:  {order.order_id}")
        print(f"  출고 수량: {order.quantity}ea")
        print(f"  처리 일시: {order.updated_at}")
        print(f"  상태:      {order.status.value}")

    def show_error(self, msg: str) -> None:
        print(f"\n[오류] {msg}")
```

- [ ] **Step 4: `view/production_view.py` 작성**

```python
from model.production_job import ProductionJob
from model.order import Order


class ProductionView:
    def show_menu(self) -> None:
        print("\n[생산라인]")
        print("  1. 생산 현황 조회")
        print("  2. 생산 완료 처리")
        print("  0. 뒤로")

    def get_choice(self) -> str:
        return input("선택: ").strip()

    def show_current_job(self, job: ProductionJob | None, sample_name_map: dict) -> None:
        if job is None:
            print("\n현재 생산 중인 작업이 없습니다.")
            return
        name = sample_name_map.get(job.sample_id, job.sample_id)
        print(f"\n[현재 생산 중]")
        print(f"  주문번호:  {job.order_id}")
        print(f"  시료명:    {name}")
        print(f"  부족분:    {job.shortage}ea")
        print(f"  실 생산량: {job.actual_production}ea")
        print(f"  예상 시간: {job.total_time:.1f}분")
        print(f"  등록 시각: {job.enqueued_at}")

    def show_queue(self, jobs: list[ProductionJob], sample_name_map: dict) -> None:
        if not jobs:
            print("\n대기 중인 작업이 없습니다.")
            return
        print(f"\n[대기 큐]")
        print(f"{'순서':<4} {'주문번호':<22} {'시료명':<15} {'실생산량':>8} {'예상시간':>8}")
        print("-" * 65)
        for i, job in enumerate(jobs, 1):
            name = sample_name_map.get(job.sample_id, job.sample_id)
            print(f"{i:<4} {job.order_id:<22} {name:<15} {job.actual_production:>8} {job.total_time:>7.1f}분")

    def show_complete_result(self, order: Order) -> None:
        print(f"\n✔ 생산 완료: {order.order_id}  →  {order.status.value}")

    def show_error(self, msg: str) -> None:
        print(f"\n[오류] {msg}")
```

- [ ] **Step 5: `view/monitor_view.py` 작성**

```python
from model.sample import Sample


class MonitorView:
    def show_menu(self) -> None:
        print("\n[모니터링]")
        print("  1. 주문량 확인")
        print("  2. 재고량 확인")
        print("  0. 뒤로")

    def get_choice(self) -> str:
        return input("선택: ").strip()

    def show_order_stats(self, stats: dict[str, int]) -> None:
        print("\n[상태별 주문 현황] (REJECTED 제외)")
        print("-" * 30)
        for status, count in stats.items():
            print(f"  {status:<12}: {count}건")

    def show_stock_status(self, items: list[dict]) -> None:
        print(f"\n{'시료ID':<10} {'시료명':<20} {'재고':>6} {'미처리주문':>10} {'상태'}")
        print("-" * 60)
        for item in items:
            s: Sample = item["sample"]
            print(f"{s.sample_id:<10} {s.name:<20} {s.stock:>6} {item['active_order_qty']:>10} {item['status']}")
```

- [ ] **Step 6: `app.py` 작성**

```python
from repository.sample_repository import SampleRepository
from repository.order_repository import OrderRepository
from repository.production_job_repository import ProductionJobRepository
from controller.sample_controller import SampleController
from controller.order_controller import OrderController
from controller.production_controller import ProductionController
from controller.monitor_controller import MonitorController
from view.main_view import MainView
from view.sample_view import SampleView
from view.order_view import OrderView
from view.production_view import ProductionView
from view.monitor_view import MonitorView


class App:
    def __init__(self, data_dir: str = "data"):
        sample_repo = SampleRepository(f"{data_dir}/samples.json")
        order_repo = OrderRepository(f"{data_dir}/orders.json")
        job_repo = ProductionJobRepository(f"{data_dir}/production_jobs.json")

        self._sample_ctrl = SampleController(sample_repo)
        self._order_ctrl = OrderController(sample_repo, order_repo, job_repo)
        self._prod_ctrl = ProductionController(sample_repo, order_repo, job_repo)
        self._monitor_ctrl = MonitorController(sample_repo, order_repo)

        self._main_view = MainView()
        self._sample_view = SampleView()
        self._order_view = OrderView()
        self._prod_view = ProductionView()
        self._monitor_view = MonitorView()

    def _sample_name_map(self) -> dict:
        return {s.sample_id: s.name for s in self._sample_ctrl.find_all()}

    def _summary(self) -> dict:
        s = self._monitor_ctrl.get_summary()
        s["queue_count"] = self._prod_ctrl.get_queue_size()
        return s

    def run(self) -> None:
        while True:
            self._main_view.show_header(self._summary())
            self._main_view.show_menu()
            choice = self._main_view.get_choice()
            if choice == "0":
                print("\n프로그램을 종료합니다.")
                break
            elif choice == "1":
                self._handle_sample()
            elif choice == "2":
                self._handle_reserve()
            elif choice == "3":
                self._handle_approve_reject()
            elif choice == "4":
                self._handle_monitoring()
            elif choice == "5":
                self._handle_production()
            elif choice == "6":
                self._handle_release()

    def _handle_sample(self) -> None:
        while True:
            self._sample_view.show_menu()
            c = self._sample_view.get_choice()
            if c == "0":
                break
            elif c == "1":
                try:
                    data = self._sample_view.get_register_input()
                    s = self._sample_ctrl.register(**data)
                    self._sample_view.show_register_result(s)
                except ValueError as e:
                    self._sample_view.show_error(str(e))
            elif c == "2":
                self._sample_view.show_sample_list(self._sample_ctrl.find_all())
            elif c == "3":
                kw = self._sample_view.get_search_keyword()
                self._sample_view.show_sample_list(self._sample_ctrl.search(kw))

    def _handle_reserve(self) -> None:
        try:
            data = self._order_view.show_reserve_menu()
            order = self._order_ctrl.reserve(**data)
            self._order_view.show_reserve_result(order)
        except (ValueError, KeyError) as e:
            self._order_view.show_error(str(e))

    def _handle_approve_reject(self) -> None:
        orders = self._order_ctrl.list_reserved()
        name_map = self._sample_name_map()
        self._order_view.show_reserved_list(orders, name_map)
        if not orders:
            return
        order_id = self._order_view.get_order_id_input("주문번호 입력 (승인/거절할 주문): ")
        action = input("승인(a) / 거절(r): ").strip().lower()
        try:
            if action == "a":
                result = self._order_ctrl.approve(order_id)
                if result["path"] == "confirmed":
                    self._order_view.show_approve_confirmed(result["order"])
                else:
                    self._order_view.show_approve_producing(result["order"], result["job"])
            elif action == "r":
                order = self._order_ctrl.reject(order_id)
                self._order_view.show_reject_result(order)
        except ValueError as e:
            self._order_view.show_error(str(e))

    def _handle_monitoring(self) -> None:
        while True:
            self._monitor_view.show_menu()
            c = self._monitor_view.get_choice()
            if c == "0":
                break
            elif c == "1":
                self._monitor_view.show_order_stats(self._monitor_ctrl.get_order_stats())
            elif c == "2":
                self._monitor_view.show_stock_status(self._monitor_ctrl.get_stock_status_all())

    def _handle_production(self) -> None:
        while True:
            self._prod_view.show_menu()
            c = self._prod_view.get_choice()
            if c == "0":
                break
            name_map = self._sample_name_map()
            if c == "1":
                self._prod_view.show_current_job(self._prod_ctrl.get_current(), name_map)
                self._prod_view.show_queue(self._prod_ctrl.get_queue(), name_map)
            elif c == "2":
                try:
                    order = self._prod_ctrl.complete_current()
                    if order:
                        self._prod_view.show_complete_result(order)
                    else:
                        self._prod_view.show_error("완료할 생산 작업이 없습니다.")
                except Exception as e:
                    self._prod_view.show_error(str(e))

    def _handle_release(self) -> None:
        orders = self._order_ctrl.list_confirmed()
        name_map = self._sample_name_map()
        self._order_view.show_confirmed_list(orders, name_map)
        if not orders:
            return
        order_id = self._order_view.get_order_id_input("출고할 주문번호: ")
        try:
            order = self._order_ctrl.release(order_id)
            self._order_view.show_release_result(order)
        except ValueError as e:
            self._order_view.show_error(str(e))
```

- [ ] **Step 7: `main.py` 작성**

```python
from app import App

if __name__ == "__main__":
    App().run()
```

- [ ] **Step 8: 전체 테스트 통과 확인**

```bash
.venv\Scripts\python.exe -m pytest tests/ -v
```
Expected: `모든 테스트 passed`

- [ ] **Step 9: 수동 실행 확인**

```bash
.venv\Scripts\python.exe main.py
```
Expected: 메인 메뉴 출력, 0 입력 시 정상 종료

- [ ] **Step 10: 커밋**

```bash
git add view/ app.py main.py
git commit -m "feat: View 계층 및 App 메인 루프 구현 (전체 기능 완성)"
```

---

## Task 9: 더미 데이터 생성기

**Files:**
- Create: `generator.py`

수동 테스트를 위해 DummyDataGenerator POC 방식을 단순화한 스크립트.

- [ ] **Step 1: `generator.py` 작성**

```python
"""더미 데이터를 생성하여 data/*.json 에 저장합니다.
사용법: python generator.py
"""
import math
import random
from datetime import date, datetime, timezone

from model.sample import Sample
from model.order import Order, OrderStatus
from model.production_job import ProductionJob
from repository.sample_repository import SampleRepository
from repository.order_repository import OrderRepository
from repository.production_job_repository import ProductionJobRepository


SAMPLES = [
    ("S-001", "실리콘웨이퍼-8인치", 5.0, 0.92),
    ("S-002", "갈륨비소-A등급", 3.5, 0.88),
    ("S-003", "질화갈륨-파워", 8.0, 0.85),
    ("S-004", "탄화규소-SiC", 12.0, 0.80),
    ("S-005", "인화인듐-레이저", 6.5, 0.90),
]

CUSTOMERS = ["삼성전자", "SK하이닉스", "서울대 연구실", "KAIST", "고려대"]
RNG = random.Random(42)
TODAY = date.today().strftime("%Y%m%d")
TS = datetime.now(timezone.utc).isoformat()


def main():
    sample_repo = SampleRepository("data/samples.json")
    order_repo = OrderRepository("data/orders.json")
    job_repo = ProductionJobRepository("data/production_jobs.json")

    # 초기화
    for repo, path in [(sample_repo, "data/samples.json"),
                       (order_repo, "data/orders.json"),
                       (job_repo, "data/production_jobs.json")]:
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f)

    # 시료 생성
    stocks = [RNG.randint(0, 200) for _ in SAMPLES]
    for (sid, name, apt, yr), stock in zip(SAMPLES, stocks):
        sample_repo.create(Sample(sid, name, apt, yr, stock))

    # 주문 생성
    statuses = (
        [OrderStatus.RESERVED] * 5 +
        [OrderStatus.REJECTED] * 2 +
        [OrderStatus.PRODUCING] * 5 +
        [OrderStatus.CONFIRMED] * 8 +
        [OrderStatus.RELEASE] * 5
    )
    RNG.shuffle(statuses)
    all_samples = sample_repo.find_all()
    samples_map = {s.sample_id: s for s in all_samples}

    for i, status in enumerate(statuses, 1):
        sample = RNG.choice(all_samples)
        qty = RNG.randint(10, 300)
        order = Order(
            order_id=f"ORD-{TODAY}-{i:04d}",
            sample_id=sample.sample_id,
            customer_name=RNG.choice(CUSTOMERS),
            quantity=qty,
            status=status,
            created_at=TS,
            updated_at=TS,
        )
        order_repo.create(order)

        if status == OrderStatus.PRODUCING:
            s = samples_map[sample.sample_id]
            shortage = max(0, qty - s.stock)
            actual = math.ceil(shortage / (s.yield_rate * 0.9)) if shortage > 0 else 1
            job_repo.create(ProductionJob(
                order_id=order.order_id,
                sample_id=sample.sample_id,
                shortage=shortage,
                actual_production=actual,
                total_time=s.avg_production_time * actual,
            ))

    print("더미 데이터 생성 완료:")
    print(f"  시료: {len(SAMPLES)}종")
    print(f"  주문: {len(statuses)}건")
    print(f"  생산작업: {job_repo.count()}건")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 실행 확인**

```bash
.venv\Scripts\python.exe generator.py
```
Expected:
```
더미 데이터 생성 완료:
  시료: 5종
  주문: 25건
  생산작업: N건
```

- [ ] **Step 3: 더미 데이터로 앱 실행 확인**

```bash
.venv\Scripts\python.exe main.py
```
Expected: 헤더에 시료 5종, 주문 23건(REJECTED 제외) 등 데이터 반영

- [ ] **Step 4: 커밋**

```bash
git add generator.py
git commit -m "feat: 더미 데이터 생성기 추가 (수동 테스트용)"
```

---

## 자기 검토 (Spec Coverage)

| PRD 요구사항 | 구현 위치 |
|---|---|
| 4.1 메인 메뉴 + 요약 정보 | `app.py:_summary()`, `view/main_view.py` |
| 4.2.1 시료 등록 | `SampleController.register` + `SampleView` |
| 4.2.2 시료 목록 조회 | `SampleController.find_all` + `SampleView.show_sample_list` |
| 4.2.3 시료 검색 | `SampleController.search` + `SampleView` |
| 4.3 시료 주문 접수 (RESERVED) | `OrderController.reserve` + `OrderView` |
| 4.4.1 접수 주문 목록 | `OrderController.list_reserved` |
| 4.4.2 주문 승인 (재고 분기) | `OrderController.approve` |
| 4.4.3 주문 거절 | `OrderController.reject` |
| 4.5.1 주문량 확인 (REJECTED 제외) | `MonitorController.get_order_stats` |
| 4.5.2 재고량 확인 (여유/부족/고갈) | `MonitorController.get_stock_status_all` |
| 4.6.1 생산량 계산 공식 | `OrderController.approve` (ceil 공식) |
| 4.6.2 생산 완료 처리 | `ProductionController.complete_current` |
| 4.6.3 생산 현황 표시 | `ProductionController.get_current` + `ProductionView` |
| 4.6.4 대기 주문 확인 (FIFO) | `ProductionController.get_queue` + FIFO by `enqueued_at` |
| 4.7 출고 처리 (CONFIRMED→RELEASE) | `OrderController.release` |
| 주문번호 형식 ORD-YYYYMMDD-NNNN | `OrderController._next_order_id` |
| REJECTED 모니터링 제외 | `MonitorController._MONITORED_STATUSES` |
| JSON 영속성 (변경 시 즉시 저장) | 모든 Repository (write-through) |
