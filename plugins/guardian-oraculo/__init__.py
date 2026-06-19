"""
GUARDIAN - Oráculo Plugin
"""
from .operators import EvaluateRisk


def register(p):
    p.register(EvaluateRisk)
