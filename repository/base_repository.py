from abc import ABC, abstractmethod

class BaseRepository(ABC):
    @abstractmethod
    def create(self, entity): pass
    @abstractmethod
    def find_by_id(self, entity_id: str): pass
    @abstractmethod
    def find_all(self) -> list: pass
    @abstractmethod
    def update(self, entity) -> bool: pass
    @abstractmethod
    def delete(self, entity_id: str) -> bool: pass
