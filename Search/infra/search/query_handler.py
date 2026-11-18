from typing import List, Optional
from google.cloud.firestore_v1.base_query import And 
from flask import Request

from core.entities import Key, FieldQuery, HttpRequestData, AnnotationType
from core.search.handler import Handler
from core.database import Database
from infra.search.operator import OperatorAdapter as Operator
from infra.search.compound_field_query import CompoundFieldQueryAdapter as CompoundFieldQuery

from utils.utils import str_to_date
from utils.logging import SearchLogger

class QueryHandler(Handler):

    def __init__(self, db: Database, logger: SearchLogger):
        self.db = db
        self.logger = logger

    def timestamp_query(self, request: HttpRequestData) -> Optional[CompoundFieldQuery]:
        simple_query = []
        if request.min_tp:
            simple_query.append(FieldQuery(Key.TIMESTAMP, Operator('>='), str_to_date(request.min_tp)))
        if request.max_tp:
            simple_query.append(FieldQuery(Key.TIMESTAMP, Operator('<='), str_to_date(request.max_tp)))
        
        if simple_query:
            self.logger.info(f'Timestamp compound query: {simple_query}')
            return CompoundFieldQuery(simple_query, Operator('and'))
        
        return None
    
    def country_query(self, request: HttpRequestData) -> Optional[CompoundFieldQuery]:
        simple_query = []
        for country in request.country:
            simple_query.append(FieldQuery(Key.COUNTRY, Operator('=='), country))
        
        if simple_query:
            self.logger.info(f'Country compound query: {simple_query}')
            return CompoundFieldQuery(simple_query, Operator('or'))
        
        return None

    def device_query(self, request: HttpRequestData) -> Optional[CompoundFieldQuery]:
        simple_query = []
        for device in request.device:
            simple_query.append(FieldQuery(Key.DEVICE, Operator('=='), device))
        
        if simple_query:
            self.logger.info(f'Device compound query: {simple_query}')
            return CompoundFieldQuery(simple_query, Operator('or'))
        
        return None
    
    def plant_query(self, request: HttpRequestData) -> Optional[CompoundFieldQuery]:
        if request.plant_type:
            simple_query = [FieldQuery(Key.PLANT_TYPE, Operator('array_contains_any'), request.plant_type)]
            self.logger.info(f'Plant compound query: {simple_query}')
            return CompoundFieldQuery(simple_query)
        
        return None

    def get_query(self, request: HttpRequestData):

        compound_field_queries: List[CompoundFieldQuery] = [self.timestamp_query(request), 
                                                            self.country_query(request), 
                                                            self.device_query(request), 
                                                            self.plant_query(request)]
        
        compound_field_queries = [q for q in compound_field_queries if q is not None]

        filters = []
        for compound_query in compound_field_queries:
            filters.append(compound_query.query_generator())

        return And(filters = filters)
    
    def handle(self, request: Request):
        data = HttpRequestData.from_dict(request.get_json())
        self.logger.info(f'Http request recived: {data}') 
        filters = self.get_query(data)
        self.logger.info('Sending query to the database ...')
        return self.db.query(AnnotationType.DETECTION.value, filters)
        