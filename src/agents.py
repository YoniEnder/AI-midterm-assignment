"""
Multi-Agent System using LlamaIndex
Implements Manager Router, Summarization Expert, and Needle-in-a-Haystack agents
"""

from typing import Literal
from llama_index.core import (
    VectorStoreIndex,
    SummaryIndex,
)
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
        self.llm = OpenAI(temperature=0, model="gpt-4")

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


class SummarizationExpertAgent:
    """
    Summarization Expert Agent
    Answers high-level questions using the Summary Information Index
    Uses LlamaIndex's built-in summarization with hierarchical structure: Claim → Document → Section
    """

    def __init__(self, summary_index: SummaryIndex):
        self.index = summary_index
        self.llm = OpenAI(temperature=0.3, model="gpt-4")

        # Create query engine using LlamaIndex's built-in tree_summarize
        # This automatically handles summarization on-the-fly using the hierarchical structure
        self.query_engine = self.index.as_query_engine(
            llm=self.llm,
            response_mode="tree_summarize",  # LlamaIndex's built-in hierarchical summarization
            similarity_top_k=10,  # Retrieve multiple chunks for comprehensive summarization
        )

        # Define summarization prompt as a function
        self.summarization_prompt = self._create_summarization_prompt()

    def _create_summarization_prompt(self) -> PromptTemplate:
        """Create summarization prompt as a function"""
        return PromptTemplate(
            """You are a Summarization Expert Agent specializing in high-level analysis.

The Summary Index uses LlamaIndex's built-in tree_summarize with hierarchical structure:
- Large chunks organized by Claim → Document → Section hierarchy
- Metadata includes: claim_id, document_type, section, timestamp_range
- Summarization happens automatically using the hierarchical structure

Your role is to:
- Provide overviews and summaries using the hierarchical structure
- Explain timelines and sequences of events
- Identify key decisions and outcomes
- Highlight important entities and relationships
- Leverage the Claim → Document → Section hierarchy when relevant
- Reference metadata (claim_id, document_type, section, timestamp_range) when available

Use the Summary Index to answer the following query. 
Focus on high-level insights rather than specific details.
The tree_summarize response mode will automatically summarize relevant chunks hierarchically.

Query: {query}

Provide a comprehensive, well-structured response based on the hierarchical information available.
"""
        )

    def answer(self, query: str) -> str:
        """Answer high-level questions using the Summary Index with LlamaIndex's built-in summarization"""
        formatted_prompt = self.summarization_prompt.format(query=query)

        # Query the summary index - LlamaIndex handles summarization automatically via tree_summarize
        response = self.query_engine.query(formatted_prompt)
        return str(response)


class NeedleInHaystackAgent:
    """
    Needle-in-a-Haystack Agent
    Handles precise factual queries by searching deep inside the hierarchical index
    Uses multi-size chunks (small, medium, large) with metadata for precise retrieval
    """

    def __init__(self, hierarchical_index: VectorStoreIndex):
        self.index = hierarchical_index
        self.llm = OpenAI(temperature=0, model="gpt-4")

        # Create query engine optimized for precise retrieval
        # The hierarchical index contains multi-size chunks with metadata:
        # - Small chunks (150-250 tokens): High precision
        # - Medium chunks (400-600 tokens): Balanced reasoning
        # - Large chunks (800-1200 tokens): High-level context
        self.query_engine = self.index.as_query_engine(
            llm=self.llm,
            similarity_top_k=10,  # Retrieve multiple chunk sizes for comprehensive answers
            response_mode="compact",
        )

        # Define precise query prompt as a function
        self.precise_prompt = self._create_precise_prompt()

    def _create_precise_prompt(self) -> PromptTemplate:
        """Create precise query prompt as a function"""
        return PromptTemplate(
            """You are a Needle-in-a-Haystack Agent specializing in precise factual retrieval.

The Hierarchical Index uses multi-size chunking with metadata:
- Small chunks (150-250 tokens): High precision for specific facts
- Medium chunks (400-600 tokens): Balanced reasoning for related events
- Large chunks (800-1200 tokens): Context for broader understanding

Each chunk carries metadata:
- claim_id: The claim identifier
- document_type: Type of document (Auto Collision, Health, Property Damage, etc.)
- section: Section within the document
- chunk_size: Size category (small, medium, large)
- timestamp_range: Time period covered

Your role is to:
- Find exact details, dates, names, numbers, and specific facts
- Extract precise information from documents using metadata
- Provide accurate, citation-ready answers
- Search deeply through the hierarchical index structure (Claim → Document → Section → Chunk)
- Leverage chunk metadata (claim_id, document_type, section, timestamp_range) when relevant

Query: {query}

Search through the hierarchical index with multi-size chunks and provide the exact, precise answer. 
Include specific details like dates, claim IDs, document numbers, names, and reference the metadata when available.
"""
        )

    def answer(self, query: str) -> str:
        """Answer precise factual queries using the Hierarchical Index with multi-size chunks"""
        formatted_prompt = self.precise_prompt.format(query=query)

        # Query the hierarchical index (contains multi-size chunks with metadata)
        response = self.query_engine.query(formatted_prompt)
        return str(response)


class MultiAgentSystem:
    """
    Orchestrates all agents and manages the routing flow
    """

    def __init__(
        self, summary_index: SummaryIndex, hierarchical_index: VectorStoreIndex
    ):
        self.manager = ManagerRouterAgent(summary_index, hierarchical_index)
        self.summarization_agent = SummarizationExpertAgent(summary_index)
        self.needle_agent = NeedleInHaystackAgent(hierarchical_index)

    def query(self, user_query: str) -> dict:
        """
        Main entry point for queries
        Returns a dictionary with routing decision and answer
        """
        # Step 1: Route the query
        route = self.manager.route_query(user_query)

        # Step 2: Get appropriate index (for logging/demonstration)
        index_type = "Summary Index" if route == "HIGH_LEVEL" else "Hierarchical Index"

        # Step 3: Route to appropriate agent
        if route == "HIGH_LEVEL":
            answer = self.summarization_agent.answer(user_query)
            agent_used = "Summarization Expert Agent"
        else:
            answer = self.needle_agent.answer(user_query)
            agent_used = "Needle-in-a-Haystack Agent"

        return {
            "query": user_query,
            "route": route,
            "index_used": index_type,
            "agent_used": agent_used,
            "answer": answer,
        }
