import dataclasses
from pathlib import Path

from model.sample import Sample
from repository.base_repository import BaseRepository


class SampleRepository(BaseRepository):
    _id_key = "sample_id"

    def _to_dict(self, sample: Sample) -> dict:
        return dataclasses.asdict(sample)

    def _from_dict(self, item: dict) -> Sample:
        return Sample(**item)

    def find_by_name(self, keyword: str) -> list[Sample]:
        keyword_lower = keyword.lower()
        return [
            self._from_dict(item)
            for item in self._read()
            if keyword_lower in item["name"].lower()
        ]
