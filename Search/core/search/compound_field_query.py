from abc import ABC, abstractmethod
from typing import List

from core.entities.query.field_query import FieldQuery
from core.search.operator import Operator
from core.search.exception import WrongCompoundOperator, WrongCompoundQuery

class CompoundFieldQuery(ABC):

    def __init__(self, query_elements: List[FieldQuery], op: Operator = None):
        self.query_elments = query_elements
        self.op = op
        self.check_query_validity()

    def check_query_validity(self):
        
        keys = set()
        for field_query in self.query_elments:
            keys.add(field_query.key)
        
        if len(keys) != 1:
            raise WrongCompoundQuery
        
        if self.op == None:
            return

        if not self.op.is_compound():
            raise WrongCompoundOperator
    
    @abstractmethod
    def query_generator(self):
        raise NotImplementedError