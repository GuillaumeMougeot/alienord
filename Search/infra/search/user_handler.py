from flask import Request

from core.search.handler import Handler
from core.database import Database
from core.search.exception import RequestUnauthorized, TokenExpired, InvalidToken

from utils.logging import SearchLogger

class UserHandler(Handler):

    def __init__(self, db: Database, logger: SearchLogger):
        self.db = db
        self.logger = logger

    def get_token(self, auth: str):
        try:
            return auth.split()[1]
        except Exception:
            self.logger.error(f'No authorization provided')
            raise RequestUnauthorized
        
    
    def handle(self, request: Request):
        token = self.get_token(str(request.authorization))
        user_info = self.db.get_user_info(token)
        
        if not user_info:
            self.logger.error(f'Invalid token {token}')
            raise InvalidToken
        
        if not user_info.valid:
            self.logger.error(f'The token {token} has been disabled')
            raise TokenExpired
        
        self.logger.info(f'User authorized')

        return super().handle(request)

