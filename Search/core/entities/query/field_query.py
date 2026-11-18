from dataclasses import dataclass
from typing import Any

from core.entities.query.key import Key
from core.search.operator import Operator
from core.search.exception import WrongSimpleOperator

@dataclass
class FieldQuery:
    key: Key
    op: Operator
    value: Any
    
    def __post_init__(self):
        if not self.op.is_simple():
            raise WrongSimpleOperator
