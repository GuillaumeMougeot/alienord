from typing import List, Optional
from google.cloud.firestore import Client
from google.cloud.firestore_v1.base_query import FieldFilter

from core.database import Database
from core.entities import AnnotationType, DatabaseInfo, Recording, Detection,  User

class Firebase(Database):

    _instance = None
    _db = None

    def __new__(cls):

        if cls._instance is None:
            cls._instance = super(Firebase, cls).__new__(cls)
            try:
                cls._db = Client()
            except Exception as e:
                exit(1)
        return cls._instance

    def dict_to_database_info(self, d: dict) -> DatabaseInfo:
        annotation_type = d['annotation_type']
        if annotation_type == AnnotationType.DETECTION.value:
            return Detection.from_dict(d)
        elif annotation_type == AnnotationType.RECORDING.value:
            return Recording.from_dict(d)

    def exist(self, collection: str, id: str) -> bool:
        return self._db.collection(collection).document(id).get().exists
    
    def get_document(self, collection: str, id: str) -> DatabaseInfo:
        data = self._db.collection(collection).document(id).get()
        return self.dict_to_database_info(data.to_dict())

    def set(self, id: str, data: DatabaseInfo) -> None:
        self._db.collection(data.annotation_type.value).document(id).set(data.to_dict())
    
    def update(self, id: str, data: DatabaseInfo) -> None:
        self._db.collection(data.annotation_type.value).document(id).update(data.to_dict())
    
    def delete(self, collection: str, id: str) -> None:
        self._db.collection(collection).document(id).delete()

    def query(self, collection: str, flt) -> List[dict]:
        docs = self._db.collection(collection).where(filter=flt).stream()
        result = []
        for doc in docs:
            result.append(Detection.to_http_response(doc.to_dict()))
        
        return result
    
    def get_user_info(self, token: str) -> Optional[User]:
        docs = self._db.collection('users').where(filter = FieldFilter('token', '==', token)).stream()
        for doc in docs:
            return User.from_dict(doc.to_dict())
        return None