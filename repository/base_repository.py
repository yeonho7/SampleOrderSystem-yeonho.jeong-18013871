import json
from abc import ABC, abstractmethod
from pathlib import Path


class BaseRepository(ABC):
    # 서브클래스가 엔티티의 PK 필드명으로 재정의 (JSON 키 = 엔티티 속성명)
    _id_key: str = ""

    def __init__(self, filepath: Path):
        self._filepath = filepath

    def _read(self) -> list[dict]:
        return json.loads(self._filepath.read_text(encoding="utf-8"))

    def _write(self, data: list[dict]) -> None:
        self._filepath.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @abstractmethod
    def _to_dict(self, entity) -> dict: ...

    @abstractmethod
    def _from_dict(self, item: dict): ...

    def create(self, entity):
        data = self._read()
        data.append(self._to_dict(entity))
        self._write(data)
        return entity

    def find_by_id(self, entity_id: str):
        for item in self._read():
            if item[self._id_key] == entity_id:
                return self._from_dict(item)
        return None

    def find_all(self) -> list:
        return [self._from_dict(item) for item in self._read()]

    def update(self, entity) -> bool:
        data = self._read()
        entity_id = getattr(entity, self._id_key)
        for i, item in enumerate(data):
            if item[self._id_key] == entity_id:
                data[i] = self._to_dict(entity)
                self._write(data)
                return True
        return False

    def delete(self, entity_id: str) -> bool:
        data = self._read()
        new_data = [item for item in data if item[self._id_key] != entity_id]
        if len(new_data) == len(data):
            return False
        self._write(new_data)
        return True
