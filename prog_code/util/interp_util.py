"""Logic for interpreting user provided values.

@author: Sam Pottinger
@license: GNU GPL v2
"""

def safe_int_interpret(target):
    try:
        return int(target)
    except ValueError:
        return None

def safe_float_interpret(target):
    try:
        return float(target)
    except ValueError:
        return None

def operator_to_str(operator):
    if operator == "eq":
        return "=="
    elif operator == "lt":
        return "<"
    elif operator == "gt":
        return ">"
    elif operator == "neq":
        return "!="
    elif operator == "lteq":
        return "<="
    elif operator == "gteq":
        return ">="
    else:
        return "?"

def filter_to_str(target):
    operator_str = operator_to_str(target.operator)
    return "%s %s %s" % (target.field, operator_str, target.operand)
