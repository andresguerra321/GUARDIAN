"""
GUARDIAN - Centinela Plugin
"""
# pyrefly: ignore [missing-import]
from .operators import RunCentinela


def register(p):
    p.register(RunCentinela)
