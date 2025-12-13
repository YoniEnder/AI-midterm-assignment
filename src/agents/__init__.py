"""
Multi-Agent System
Exports all agents and the MultiAgentSystem
"""

from src.agents.manager_router import ManagerRouterAgent
from src.agents.summarization_expert import SummarizationExpertAgent
from src.agents.needle_haystack import NeedleInHaystackAgent
from src.agents.multi_agent_system import MultiAgentSystem

__all__ = [
    "ManagerRouterAgent",
    "SummarizationExpertAgent",
    "NeedleInHaystackAgent",
    "MultiAgentSystem",
]
