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

# Always favour largest unit
def merge_ingreds(q1, q2):
    if type(q1) == str:
        amt, unit = q1.split(" ")
    pass


def convert_vol_unit_to_ml(vol):
    pass


# Atomic units are mL
vol_units = [
    (5.0, "tbs"),
    (15.0, "tbsp"),
    (250, "cup")
    (1000, "litre")
]

def pick_smallest_unit_for_volume(vol):
    for (min_vol, unit) in vol_units:
        if min_vol > vol:
            continue;

        return unit

    # Gross... Get the largest unit if it's too big.
    (_, unit) = vol_units[-1]
    return unit
