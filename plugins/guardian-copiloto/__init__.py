"""
GUARDIAN - Copiloto Plugin
"""

from .operators import AskCopiloto, GenerateBriefing

def register(p):
    p.register(AskCopiloto)
    p.register(GenerateBriefing)
