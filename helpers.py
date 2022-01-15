from flask import request, session
from sqlalchemy import select, exists
from functools import wraps

def get_req_arg(key):
    request.args.get(key)

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "username" in session:
            return func(*args, **kwargs) 
        else:
            return "Need to login"
    return wrapper