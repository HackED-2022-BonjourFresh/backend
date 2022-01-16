from flask import request, session
from sqlalchemy import select, exists
from functools import wraps

MASS_TYPE = 0
VOL_TYPE = 1
UNKNOWN_TYPE = 2

# For reference
UNITS = ['oz', 'cup', 'large', 'cups', 'tablespoon', 'servings', 'ounces',  
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
SORTED_VOL_UNITS = sorted(list(VOL_UNITS.items()))

# Atomic units are mg
MASS_UNITS = {
    "mg": 1.0,
    "g": 1000.0,
    "oz": 28000.34952,
    "kg": 1000000.0,
    "lb": 453592.0,
}
SORTED_MASS_UNITS = sorted(list(MASS_UNITS.items()))

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
    "ounces": "oz",
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
    if get_unit_type(u1) == MASS_TYPE:
        res = add_quantities_mass(q1, u1, q2, u2)
        smallest_unit = pick_smallest_unit_for_mass(res)
        return (res / MASS_UNITS[smallest_unit]), smallest_unit

    elif get_unit_type(u2) == VOL_TYPE:
        res = add_quantities_vol(q1, u1, q2, u2)
        smallest_unit = pick_smallest_unit_for_volume(res)
        return (res / VOL_UNITS[smallest_unit]), smallest_unit
    else:
        raise Exception("Quantity unit made it into add that is not recognized! ({})".format())

def add_quantities_vol(q1, u1, q2, u2):
    return conv_vol_unit_to_ml(q1, u1) + conv_vol_unit_to_ml(q2, u2)

def add_quantities_mass(q1, u1, q2, u2):
    return conv_mass_unit_to_mg(q1, u1) + conv_mass_unit_to_mg(q2, u2)

def conv_vol_unit_to_ml(vol, unit):
    return VOL_UNITS[unit] * vol

def conv_mass_unit_to_mg(mass, unit):
    return MASS_UNITS[unit] * mass

def pick_smallest_unit_for_volume(vol):
    return pick_smallest_unit(vol, SORTED_VOL_UNITS)

def pick_smallest_unit_for_mass(mass, unit):
    return pick_smallest_unit(mass, SORTED_MASS_UNITS)

def pick_smallest_unit(amt, l_table):
    prev_unit = l_table[0] # Gross...
    for (unit, unit_amt) in l_table:
        if unit_amt >= amt:
            return prev_unit

        prev_unit = unit

    # Gross... Get the largest unit if it's too big.
    (unit, _) = VOL_UNITS[-1]
    return unit

import random
def get_amount():
    idx = random.randint(0,len(UNITS)-1)
    if random.randint(1,100) > 80:
        half= ".5"
    else:
        half=""

    if random.randint(0,10) > 3:
        number= random.randint(1,10)
    else:
        number = random.randint(1, 100)
    return f"{str(number)}{half}",  UNITS[idx]
