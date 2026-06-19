"""
GUARDIAN - Centinela Plugin
"""
from .operators import RunCentinela

def register(p):
    p.register(RunCentinela)
