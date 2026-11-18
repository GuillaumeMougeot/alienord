from abc import ABC, abstractmethod

class Operator(ABC):

    COMPOUND_OPERATORS = {'and', 'or'}

    def __init__(self, op: str):
        self.op = None
        self.is_valid(op)
    
    @abstractmethod
    def is_valid(self) -> bool:
        raise NotImplementedError
    
    @abstractmethod
    def is_simple(self) -> bool:
        raise NotImplementedError

    def is_compound(self) -> bool:
        if self.op in self.COMPOUND_OPERATORS:
            return True
        return False
    
    @property
    def get_op(self) -> str:
        return self.op