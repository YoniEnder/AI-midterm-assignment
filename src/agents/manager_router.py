"""
Manager (Router) Agent
Receives user query, determines the correct agent to call,
and chooses which index to use (summary vs hierarchical)
"""

from typing import Literal
import os
from llama_index.core import VectorStoreIndex, SummaryIndex
from llama_index.core.prompts import PromptTemplate
from llama_index.llms.openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class ManagerRouterAgent:
    """
    Manager (Router) Agent
    Receives user query, determines the correct agent to call,
    and chooses which index to use (summary vs hierarchical)
    """

    def __init__(
        self, summary_index: SummaryIndex, hierarchical_index: VectorStoreIndex
    ):
        self.summary_index = summary_index
        self.hierarchical_index = hierarchical_index

        # Define routing prompt as a function
        self.routing_prompt = self._create_routing_prompt()

        # Initialize LLM for routing decisions
        manager_model = os.getenv("MANAGER_MODEL", "gpt-4o-mini")
        self.llm = OpenAI(temperature=0, model=manager_model)

    def _create_routing_prompt(self) -> PromptTemplate:
        """Create routing prompt as a function"""
        return PromptTemplate(
            """You are a routing agent that determines which specialist agent should handle a query.

Query types:
1. HIGH_LEVEL: Questions about summaries, timelines, overviews, general trends, or "what happened overall"
   - Examples: "What is the summary of this claim?", "Give me a timeline", "What are the key events?"
   - Use: Summarization Expert Agent with Summary Index

2. PRECISE: Questions about specific facts, exact details, dates, names, numbers, or "needle in haystack" queries
   - Examples: "What was the exact date of X?", "Who signed document Y?", "What is the claim ID for Z?"
   - Use: Needle-in-a-Haystack Agent with Hierarchical Index

User Query: {query}

Respond with ONLY one word: either "HIGH_LEVEL" or "PRECISE"
"""
        )

    def route_query(self, query: str) -> Literal["HIGH_LEVEL", "PRECISE"]:
        """
        Route the query to the appropriate agent
        Returns: "HIGH_LEVEL" or "PRECISE"
        """
        formatted_prompt = self.routing_prompt.format(query=query)
        response = self.llm.complete(formatted_prompt)
        decision = response.text.strip().upper()

        # Validate and default to PRECISE if unclear
        if decision not in ["HIGH_LEVEL", "PRECISE"]:
            # Fallback logic: if query contains specific keywords, route to PRECISE
            precise_keywords = [
                "exact",
                "specific",
                "what date",
                "who",
                "which",
                "claim id",
                "document number",
            ]
            if any(keyword in query.lower() for keyword in precise_keywords):
                return "PRECISE"
            return "HIGH_LEVEL"

        return decision

    def get_index(self, route: Literal["HIGH_LEVEL", "PRECISE"]):
        """Get the appropriate index based on routing decision"""
        if route == "HIGH_LEVEL":
            return self.summary_index
        else:
            return self.hierarchical_index
