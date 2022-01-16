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
    "Kg": 1000000,
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
    unit_and_amt(q1)

    if type(q1) == str:
        amt, unit = q1.split(" ")
        amt = float(amt)
    pass

def unit_and_amt(q):
    amt, unit = q1.split(" ")
    return (amt, unit)

def add_quantities_vol(q1, u1, q2, u2):
    return conv_vol_unit_to_ml(q1, u1) + conv_vol_unit_to_ml(q2, u2)

def add_quantities_mass(q1, q2):
    return conv_mass_unit_to_mg(q1) + conv_mass_unit_to_mg(q2)

def conv_vol_unit_to_ml(vol, unit):
    return VOL_UNITS[unit]

def conv_mass_unit_to_mg(vol, unit):
    return MASS_UNITS[unit]

def pick_smallest_unit_for_volume(vol):
    return pick_smallest_unit(vol, VOL_UNITS)

def pick_smallest_unit_for_mas(mass, unit):
    return pick_smallest_unit(mass, MASS_UNITS)

def pick_smallest_unit(amt, l_table):
    for (unit, min_amt) in l_table.items():
        if min_amt > amt:
            continue

        return unit

    # Gross... Get the largest unit if it's too big.
    (_, unit) = VOL_UNITS[-1]
    return unit