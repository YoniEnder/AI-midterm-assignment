"""
Multi-Agent System using LlamaIndex
Implements Manager Router, Summarization Expert, and Needle-in-a-Haystack agents
Includes ClaimTimelineAnalyticsTool MCP for timeline analytics
"""

from typing import Literal, Optional
import re
from llama_index.core import (
    VectorStoreIndex,
    SummaryIndex,
)
from llama_index.core.prompts import PromptTemplate
from llama_index.llms.openai import OpenAI
from dotenv import load_dotenv

try:
    from src.timeline_analytics_tool import ClaimTimelineAnalyticsTool
except ImportError:
    from timeline_analytics_tool import ClaimTimelineAnalyticsTool

load_dotenv()

# Keywords that indicate timeline analytics queries
TIMELINE_ANALYTICS_KEYWORDS = [
    "how long",
    "hours between",
    "minutes between",
    "time between",
    "delay",
    "sla",
    "within 48 hours",
    "violated",
    "breach",
    "duration",
    "total time",
    "how many hours",
    "how many minutes",
    "timeline stats",
    "timeline summary",
]


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
    Can use ClaimTimelineAnalyticsTool MCP for timeline analytics
    """

    def __init__(
        self,
        summary_index: SummaryIndex,
        timeline_tool: Optional[ClaimTimelineAnalyticsTool] = None,
    ):
        self.index = summary_index
        self.llm = OpenAI(temperature=0.3, model="gpt-4")
        self.timeline_tool = timeline_tool

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

    def _needs_timeline_analytics(self, query: str) -> bool:
        """Check if query requires timeline analytics tool"""
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in TIMELINE_ANALYTICS_KEYWORDS)

    def _extract_claim_id_from_query(self, query: str) -> Optional[str]:
        """Extract claim ID from query if mentioned"""
        # Try various patterns
        patterns = [
            r"claim\s+(?:id|#)?\s*:?\s*([A-Z0-9-]+)",
            r"claim\s+(\d+)",
            r"claim\s+document\s+(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def answer(self, query: str) -> str:
        """Answer high-level questions using the Summary Index with LlamaIndex's built-in summarization"""
        # Check if this needs timeline analytics
        if self.timeline_tool and self._needs_timeline_analytics(query):
            try:
                claim_id = (
                    self._extract_claim_id_from_query(query) or "01"
                )  # Default to claim 01

                # Try to extract event types and call appropriate tool function
                query_lower = query.lower()

                # Check for SLA queries
                if (
                    "sla" in query_lower
                    or "violated" in query_lower
                    or "breach" in query_lower
                ):
                    # Extract SLA hours if mentioned
                    sla_match = re.search(r"(\d+)\s*hours?", query_lower)
                    sla_hours = (
                        float(sla_match.group(1)) if sla_match else 48.0
                    )  # Default 48 hours

                    # Try to identify event types from query
                    if "fnol" in query_lower or "first notice" in query_lower:
                        result = self.timeline_tool.sla_check(
                            claim_id=claim_id,
                            sla_hours=sla_hours,
                            from_event_type="FNOL_REPORTED",
                            to_event_type="FIRST_ADJUSTER_CONTACT",
                        )
                        if "error" not in result:
                            return f"Based on timeline analytics:\n\nSLA Check Result:\n- Breach: {result['breach']}\n- Allowed Hours: {result['allowed_hours']}\n- Actual Hours: {result['actual_hours']}\n- Details: {result['details']}"

                # Check for time difference queries
                elif (
                    "how long" in query_lower
                    or "hours between" in query_lower
                    or "time between" in query_lower
                ):
                    # Try to identify event types
                    if "accident" in query_lower and "inspection" in query_lower:
                        result = self.timeline_tool.time_diff(
                            claim_id=claim_id,
                            from_event_type="FNOL_REPORTED",
                            to_event_type="INSPECTION_COMPLETED",
                        )
                        if "error" not in result:
                            return f"Based on timeline analytics:\n\nTime Difference:\n- From: {result['from_event_ts']}\n- To: {result['to_event_ts']}\n- Duration: {result['diff_human_readable']} ({result['diff_hours']} hours)"

                # Check for summary stats
                elif (
                    "summary" in query_lower
                    and "timeline" in query_lower
                    or "stats" in query_lower
                ):
                    result = self.timeline_tool.timeline_summary_stats(
                        claim_id=claim_id
                    )
                    if "error" not in result:
                        stats_text = (
                            f"Timeline Summary Statistics for Claim {claim_id}:\n"
                        )
                        stats_text += f"- Total Duration: {result.get('total_duration_hours', 'N/A')} hours\n"
                        stats_text += (
                            f"- Number of Events: {result.get('num_events', 0)}\n"
                        )
                        stats_text += f"- Average Gap: {result.get('average_gap_hours', 'N/A')} hours\n"
                        if result.get("longest_gap"):
                            lg = result["longest_gap"]
                            stats_text += f"- Longest Gap: {lg['gap_hours']} hours ({lg['from_event']} to {lg['to_event']})\n"
                        return stats_text

            except Exception as e:
                print(
                    f"Warning: Timeline analytics tool failed: {e}, falling back to standard query"
                )

        formatted_prompt = self.summarization_prompt.format(query=query)

        # Query the summary index - LlamaIndex handles summarization automatically via tree_summarize
        response = self.query_engine.query(formatted_prompt)
        return str(response)


class NeedleInHaystackAgent:
    """
    Needle-in-a-Haystack Agent
    Handles precise factual queries by searching deep inside the hierarchical index
    Uses multi-size chunks (small, medium, large) with metadata for precise retrieval
    Can use ClaimTimelineAnalyticsTool MCP for precise timeline calculations
    """

    def __init__(
        self,
        hierarchical_index: VectorStoreIndex,
        timeline_tool: Optional[ClaimTimelineAnalyticsTool] = None,
    ):
        self.index = hierarchical_index
        self.llm = OpenAI(temperature=0, model="gpt-4")
        self.timeline_tool = timeline_tool

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

    def _needs_timeline_analytics(self, query: str) -> bool:
        """Check if query requires timeline analytics tool"""
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in TIMELINE_ANALYTICS_KEYWORDS)

    def _extract_claim_id_from_query(self, query: str) -> Optional[str]:
        """Extract claim ID from query if mentioned"""
        import re

        patterns = [
            r"claim\s+(?:id|#)?\s*:?\s*([A-Z0-9-]+)",
            r"claim\s+(\d+)",
            r"claim\s+document\s+(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def answer(self, query: str) -> str:
        """Answer precise factual queries using the Hierarchical Index with multi-size chunks"""
        # Check if this needs timeline analytics
        if self.timeline_tool and self._needs_timeline_analytics(query):
            try:
                claim_id = self._extract_claim_id_from_query(query) or "01"
                query_lower = query.lower()

                # For precise queries, try to extract specific event types from the query
                # First, get context from the index to identify event types
                context_query = (
                    f"Extract event types and timestamps mentioned in: {query}"
                )
                context_response = self.query_engine.query(context_query)
                context_text = str(context_response)

                # Use LLM to identify event types from query and context
                event_extraction_prompt = f"""Given the user query and context, identify the two events mentioned for time calculation.

User Query: {query}
Context: {context_text}

Identify:
1. from_event_type: The starting event (e.g., FNOL_REPORTED, ACCIDENT_OCCURRED, PHOTO_UPLOAD)
2. to_event_type: The ending event (e.g., FIRST_ADJUSTER_CONTACT, INSPECTION_COMPLETED, POLICE_REPORT_RECEIVED)

Return ONLY a JSON object with "from_event_type" and "to_event_type" fields. If unclear, use standard event types."""

                extraction_response = self.llm.complete(event_extraction_prompt)
                extraction_text = extraction_response.text.strip()

                # Try to parse JSON
                json_match = re.search(r"\{[^}]+\}", extraction_text)
                if json_match:
                    import json

                    try:
                        events = json.loads(json_match.group(0))
                        from_event = events.get("from_event_type", "FNOL_REPORTED")
                        to_event = events.get("to_event_type", "FIRST_ADJUSTER_CONTACT")

                        # Check if it's an SLA query
                        if "sla" in query_lower or "violated" in query_lower:
                            sla_match = re.search(r"(\d+)\s*hours?", query_lower)
                            sla_hours = float(sla_match.group(1)) if sla_match else 48.0

                            result = self.timeline_tool.sla_check(
                                claim_id=claim_id,
                                sla_hours=sla_hours,
                                from_event_type=from_event,
                                to_event_type=to_event,
                            )
                            if "error" not in result:
                                return f"Precise SLA Analysis:\n\n- Breach: {result['breach']}\n- Allowed: {result['allowed_hours']} hours\n- Actual: {result['actual_hours']} hours\n- {result['details']}\n\nFrom: {result.get('from_event_ts', 'N/A')}\nTo: {result.get('to_event_ts', 'N/A')}"
                        else:
                            # Time difference query
                            result = self.timeline_tool.time_diff(
                                claim_id=claim_id,
                                from_event_type=from_event,
                                to_event_type=to_event,
                            )
                            if "error" not in result:
                                return f"Precise Time Calculation:\n\n- Duration: {result['diff_human_readable']}\n- Hours: {result['diff_hours']}\n- Seconds: {result['diff_seconds']}\n\nFrom: {result['from_event_ts']}\nTo: {result['to_event_ts']}"
                    except json.JSONDecodeError:
                        pass

            except Exception as e:
                print(
                    f"Warning: Timeline analytics tool failed: {e}, falling back to standard query"
                )

        formatted_prompt = self.precise_prompt.format(query=query)

        # Query the hierarchical index (contains multi-size chunks with metadata)
        response = self.query_engine.query(formatted_prompt)
        return str(response)


class MultiAgentSystem:
    """
    Orchestrates all agents and manages the routing flow
    Includes ClaimTimelineAnalyticsTool MCP for timeline analytics
    """

    def __init__(
        self, summary_index: SummaryIndex, hierarchical_index: VectorStoreIndex
    ):
        self.manager = ManagerRouterAgent(summary_index, hierarchical_index)

        # Initialize timeline analytics tool (MCP)
        self.timeline_tool = ClaimTimelineAnalyticsTool()

        # Populate timeline from documents (optional - can be done separately)
        try:
            from src.timeline_extractor import populate_timeline_from_documents

            populate_timeline_from_documents(hierarchical_index, self.timeline_tool)
        except Exception as e:
            print(f"Note: Could not auto-populate timeline: {e}")
            print("Timeline events can be added manually or extracted separately.")

        # Initialize agents with timeline tool
        self.summarization_agent = SummarizationExpertAgent(
            summary_index, timeline_tool=self.timeline_tool
        )
        self.needle_agent = NeedleInHaystackAgent(
            hierarchical_index, timeline_tool=self.timeline_tool
        )

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

        # Check if timeline tool was used
        timeline_tool_used = False
        if self.timeline_tool:
            query_lower = user_query.lower()
            timeline_tool_used = any(
                keyword in query_lower for keyword in TIMELINE_ANALYTICS_KEYWORDS
            )

        return {
            "query": user_query,
            "route": route,
            "index_used": index_type,
            "agent_used": agent_used,
            "timeline_tool_used": timeline_tool_used,
            "answer": answer,
        }
