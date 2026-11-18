import functions_framework
from flask import Request

from di import user_handler, query_handler, logger
from utils.http import handle_excpetion

@functions_framework.http
def http_query(request: Request):
    user_handler.set_next(query_handler)
    
    try:
        return user_handler.handle(request)
    except Exception as e:
        logger.error(f'Internal error: {e}')
        handle_excpetion(e)
    