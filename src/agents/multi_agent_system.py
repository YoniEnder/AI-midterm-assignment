"""
Multi-Agent System
Orchestrates all agents and manages the routing flow
Includes DateParserTool MCP for date parsing
"""

from dotenv import load_dotenv
from llama_index.core import Settings, SummaryIndex, VectorStoreIndex

from src.agents.constants import DATE_PARSING_KEYWORDS
from src.agents.manager_router import ManagerRouterAgent
from src.agents.needle_haystack import NeedleInHaystackAgent
from src.agents.summarization_expert import SummarizationExpertAgent
from src.evaluation.token_usage import token_usage_context

try:
    from src.mcp_tools.date_parser_tool import DateParserTool
except ImportError:
    try:
        from src.date_parser_tool import DateParserTool
    except ImportError:
        from date_parser_tool import DateParserTool

load_dotenv()


class MultiAgentSystem:
    """
    Orchestrates all agents and manages the routing flow
    Includes DateParserTool MCP for date parsing
    """

    def __init__(
        self, summary_index: VectorStoreIndex, hierarchical_index: VectorStoreIndex
    ):
        self.manager = ManagerRouterAgent(summary_index, hierarchical_index)

        # Initialize date parser tool (MCP)
        self.date_parser_tool = DateParserTool()

        # Initialize agents with date parser tool
        self.summarization_agent = SummarizationExpertAgent(
            summary_index, date_parser_tool=self.date_parser_tool
        )
        self.needle_agent = NeedleInHaystackAgent(
            hierarchical_index, date_parser_tool=self.date_parser_tool
        )

    def query(self, user_query: str, return_chunks: bool = False) -> dict:
        """
        Main entry point for queries
        Returns a dictionary with routing decision and answer
        """
        # Reset tool usage tracking for this query (if supported)
        if self.date_parser_tool and hasattr(self.date_parser_tool, "reset_usage"):
            try:
                self.date_parser_tool.reset_usage()
            except Exception:
                pass

        with token_usage_context() as get_usage:
            cb = getattr(get_usage, "callback_manager", None)

            def _set_cb_manager(obj):
                if obj is None or cb is None:
                    return None
                if hasattr(obj, "callback_manager"):
                    old = getattr(obj, "callback_manager", None)
                    try:
                        setattr(obj, "callback_manager", cb)
                    except Exception:
                        return None
                    return old
                return None

            # Attach callback manager to the concrete LLM/embed instances used at query-time.
            old_manager_cb = _set_cb_manager(getattr(self.manager, "llm", None))
            old_needle_cb = _set_cb_manager(getattr(self.needle_agent, "llm", None))
            old_sum_cb = _set_cb_manager(getattr(self.summarization_agent, "llm", None))
            old_embed_cb = _set_cb_manager(getattr(Settings, "embed_model", None))

            # Step 1: Route the query
            route = self.manager.route_query(user_query)

            # Step 2: Get appropriate index (for logging/demonstration)
            index_type = (
                "Summary Index" if route == "HIGH_LEVEL" else "Hierarchical Index"
            )

            # Step 3: Route to appropriate agent
            chunks = []
            if route == "HIGH_LEVEL":
                result = self.summarization_agent.answer(
                    user_query, return_chunks=return_chunks
                )
                agent_used = "Summarization Expert Agent"
            else:
                result = self.needle_agent.answer(
                    user_query, return_chunks=return_chunks
                )
                agent_used = "Needle-in-a-Haystack Agent"

            # Extract answer and chunks from result
            if return_chunks and isinstance(result, dict):
                answer = result["answer"]
                chunks = result.get("chunks", [])
            else:
                answer = result if isinstance(result, str) else result.get("answer", "")

            usage = get_usage()

            # Restore callback managers (best-effort) to avoid cross-test interference.
            try:
                if hasattr(getattr(self.manager, "llm", None), "callback_manager"):
                    setattr(self.manager.llm, "callback_manager", old_manager_cb)
                if hasattr(getattr(self.needle_agent, "llm", None), "callback_manager"):
                    setattr(self.needle_agent.llm, "callback_manager", old_needle_cb)
                if hasattr(
                    getattr(self.summarization_agent, "llm", None), "callback_manager"
                ):
                    setattr(
                        self.summarization_agent.llm, "callback_manager", old_sum_cb
                    )
                if hasattr(getattr(Settings, "embed_model", None), "callback_manager"):
                    setattr(Settings.embed_model, "callback_manager", old_embed_cb)
            except Exception:
                pass

        # Tool usage signals:
        # - `date_parser_tool_triggered`: whether the query *looks like* it needs date parsing (keyword heuristic)
        # - `date_parser_tool_used`: whether the tool actually ran (tracked by DateParserTool)
        query_lower = user_query.lower()
        date_parser_tool_triggered = any(
            keyword in query_lower for keyword in DATE_PARSING_KEYWORDS
        )
        date_parser_tool_used = bool(getattr(self.date_parser_tool, "used", False))

        return {
            "query": user_query,
            "route": route,
            "index_used": index_type,
            "agent_used": agent_used,
            "date_parser_tool_used": date_parser_tool_used,
            "date_parser_tool_triggered": date_parser_tool_triggered,
            "usage": usage,
            "answer": answer,
            "chunks": chunks if return_chunks else [],
        }
