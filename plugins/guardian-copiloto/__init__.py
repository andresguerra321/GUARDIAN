"""
GUARDIAN - Copiloto Plugin
"""
# pyrefly: ignore [missing-import]
from .operators import AskCopiloto, GenerateBriefing


def register(p):
    p.register(AskCopiloto)
    p.register(GenerateBriefing)
