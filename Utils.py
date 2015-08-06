from Enums import *

def clamp(value):
    return max(INT_MIN, min(value, INT_MAX))