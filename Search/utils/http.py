from flask import abort

from core.search.exception import *

def handle_excpetion(error):
    try:
        raise error
    except Exception as e:
        if type(e) is RequestUnauthorized:
            abort(401, description = 'No token was provided')
        elif type(e) is InvalidToken:
            abort(401, description = 'Token not found')
        elif type(e) is TokenExpired:
            abort(401, description = 'Token expired')
        elif type(e) is WrongSimpleOperator:
            abort(400, description = 'Unvalid simple operator')
        elif type(e) is WrongCompoundOperator: 
            abort(400, description = 'Unvalid compound operator')
        elif type(e) is WrongCompoundQuery:
            abort(400, description = 'All compound filters should be the same')
        else:
            abort(500, description = str(e))