from core.search.operator import Operator

class OperatorAdapter(Operator):

    FIRESTORE_OPERATORS = {'==', '!=', '>', '>=', '<', '<=', 'in', 'not-in', 'array-contains', 'array_contains_any'}
    
    def is_valid(self, op: str) -> bool:
        if op in self.FIRESTORE_OPERATORS or op in self.COMPOUND_OPERATORS:
            self.op = op
            return True
        
        return False
    
    def is_simple(self) -> bool:
        if self.op in self.FIRESTORE_OPERATORS:
            return True
        
        return False