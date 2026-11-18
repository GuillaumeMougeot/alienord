from typing import List, Optional
from abc import ABC, abstractmethod

from core.entities import DatabaseInfo, User

class Database(ABC):
    
    @abstractmethod
    def exist(collection: str, id: str) -> bool:
        raise NotImplementedError
    
    @abstractmethod
    def get_document(collection: str, id: str) -> DatabaseInfo:
        raise NotImplementedError

    @abstractmethod
    def set(self, id: str, data: DatabaseInfo) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def update(self, id: str, data: DatabaseInfo) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def delete(self, id: str, data: DatabaseInfo) -> None:
        raise NotImplementedError

    @abstractmethod
    def query(self, q) -> List[dict]:
        raise NotImplementedError
    
    @abstractmethod
    def get_user_info(self, token: str) -> Optional[User]:
        raise NotImplementedError