from flask import request, session
from sqlalchemy import select, exists
from functools import wraps

MASS_TYPE = 0
VOL_TYPE = 1
UNKNOWN_TYPE = 2

# For reference
UNITS = ['oz', 'cup', 'large', 'cups', 'tablespoon', 'servings', 'ounces', '', 
'teaspoon', 'tablespoons', 'c', 'pound', 'null', 'fillet', 'serving', 'bunch', 
'loaf', 'grams', 'package', 'tsp', 'pounds', 'g', 'teaspoons', 'pinch', 'slices']

# Atomic units are mL
VOL_UNITS = {
    "ml": 1.0,
    "tsp": 5.0,
    "tbsp": 15.0,
    "cup": 250.0,
    "litre": 1000.0,
}

MASS_UNITS = {
    "mg": 1.0,
    "g": 1000.0,
    "oz": 28000.34952,
    "kg": 1000000.0,
    "lb": 453592.0,
}

UNITS_CONV = {
    "milliliter": "ml",
    "c": "cup",
    "cups": "cup",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "milligram": "mg",
    "gram": "g",
    "grams": "g",
    "ounce": "oz",
    "killigram": "kg",
    "pound": "lb"
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

def ingred_unit_is_known(ingred):
    return get_unit_type(ingred["unit"]) != UNKNOWN_TYPE

# Assumes that the units are mergeable
def merge_ingreds(q1, q2):
    u1, q1 = unit_and_amt(q1)
    u2, q2 = unit_and_amt(q2)
    
    return add_quantities(q1, u1, q2, u2)

def unit_and_amt(q):
    # if type(q) == str:
    #     split = q.split(" ")
    #     if len(split) == 2:
    #         amt, unit = float(split[0]), split[1]
    #     elif len(split) == 1:
    #         amt, unit = float(0), None
    #     else:
    #         raise TypeError("Don't know how to split up amt and unit")

    # elif type(q) == float:
    #     amt, unit = q, None 

    # else:
    #     raise TypeError("Don't know how to split up amt and unit")

    return (q["unit"], q["amount"])

def unit_understandable(unit):
    unit != UNKNOWN_TYPE

def attempt_to_conv_type_to_known_type(unit):
    if unit in UNITS_CONV:
        return UNITS_CONV[unit]
    
    return unit

def get_unit_type(unit):
    if unit in MASS_UNITS:
        return MASS_TYPE
    elif unit in VOL_UNITS:
        return VOL_TYPE
    else:
        return UNKNOWN_TYPE

def add_quantities(q1, u1, q2, u2):
    print(u2)
    if get_unit_type(u1) == MASS_TYPE:
        return conv_mass_unit_to_mg(q1, u1, q2, u2)
    elif get_unit_type(u2) == VOL_TYPE:
        return conv_mass_unit_to_mg(q1, u1, q2, u2)
    else:
        print("error")

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



