from flask import request, session
from sqlalchemy import select, exists
from functools import wraps

# Atomic units are mL
VOL_UNITS = {
    "ml": 1.0,
    "tbs": 5.0,
    "tbsp": 15.0,
    "cup": 250.0,
    "litre": 1000.0,
}

MASS_UNITS = {
    "mg": 1.0,
    "g": 1000.0,
    "oz": 28000.34952,
    "Kg": 1,

}

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


def convert_vol_unit_to_ml(vol, unit):
    VOL_UNITS[unit]


def pick_smallest_unit_for_volume(vol):
    for (unit, min_vol) in VOL_UNITS.items():
        if min_vol > vol:
            continue;

        return unit

    # Gross... Get the largest unit if it's too big.
    (_, unit) = VOL_UNITS[-1]
    return unit
