import json
import dataclasses
from pathlib import Path

from model.sample import Sample
from repository.base_repository import BaseRepository


class SampleRepository(BaseRepository):

    def __init__(self, filepath: Path):
        self._filepath = filepath

    def _read(self) -> list[dict]:
        return json.loads(self._filepath.read_text(encoding="utf-8"))

    def _write(self, data: list[dict]):
        self._filepath.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def create(self, sample: Sample) -> Sample:
        data = self._read()
        data.append(dataclasses.asdict(sample))
        self._write(data)
        return sample

    def find_by_id(self, sample_id: str) -> Sample | None:
        for item in self._read():
            if item["sample_id"] == sample_id:
                return Sample(**item)
        return None

    def find_all(self) -> list[Sample]:
        return [Sample(**item) for item in self._read()]

    def update(self, sample: Sample) -> bool:
        data = self._read()
        for i, item in enumerate(data):
            if item["sample_id"] == sample.sample_id:
                data[i] = dataclasses.asdict(sample)
                self._write(data)
                return True
        return False

    def delete(self, sample_id: str) -> bool:
        data = self._read()
        new_data = [item for item in data if item["sample_id"] != sample_id]
        if len(new_data) == len(data):
            return False
        self._write(new_data)
        return True

    def find_by_name(self, keyword: str) -> list[Sample]:
        keyword_lower = keyword.lower()
        return [
            Sample(**item)
            for item in self._read()
            if keyword_lower in item["name"].lower()
        ]
