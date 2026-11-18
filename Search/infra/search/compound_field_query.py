from google.cloud.firestore_v1.base_query import FieldFilter, Or, And 

from core.search.compound_field_query import CompoundFieldQuery

class CompoundFieldQueryAdapter(CompoundFieldQuery):

    def query_generator(self):
        if len(self.query_elments) == 1:
            return FieldFilter(self.query_elments[0].key.value,
                               self.query_elments[0].op.get_op,
                               self.query_elments[0].value)
        
        filters = []
        for field_query in self.query_elments:
            filters.append(FieldFilter(field_query.key.value, 
                                       field_query.op.get_op,
                                       field_query.value))
        
        if self.op.get_op == 'and':
            return And(filters = filters)
        else:
            return Or(filters = filters)