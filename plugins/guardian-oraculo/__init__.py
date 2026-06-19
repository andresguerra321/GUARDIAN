"""
GUARDIAN - Oráculo Plugin
"""
# pyrefly: ignore [missing-import]
from .operators import EvaluateRisk


def register(p):
    p.register(EvaluateRisk)
