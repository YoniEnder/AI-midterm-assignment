"""
Summarization Expert Agent
Answers high-level questions using the Summary Information Index
Uses LlamaIndex's built-in summarization with hierarchical structure: Claim → Document → Section
Can use DateParserTool MCP for date parsing
"""

from typing import Optional
import re
import os
from llama_index.core import SummaryIndex, VectorStoreIndex
from llama_index.core.prompts import PromptTemplate
from llama_index.llms.openai import OpenAI
from dotenv import load_dotenv

try:
    from src.mcp_tools.date_parser_tool import DateParserTool
except ImportError:
    try:
        from src.date_parser_tool import DateParserTool
    except ImportError:
        from date_parser_tool import DateParserTool

from src.agents.constants import DATE_PARSING_KEYWORDS

load_dotenv()


class SummarizationExpertAgent:
    """
    Summarization Expert Agent
    Answers high-level questions using the Summary Information Index
    Uses LlamaIndex's built-in summarization with hierarchical structure: Claim → Document → Section
    Can use DateParserTool MCP for date parsing
    """

    def __init__(
        self,
        summary_index: VectorStoreIndex,
        date_parser_tool: Optional[DateParserTool] = None,
    ):
        self.index = summary_index
        summarization_model = os.getenv("SUMMARIZATION_MODEL", "gpt-4o-mini")
        self.llm = OpenAI(temperature=0.3, model=summarization_model)
        self.date_parser_tool = date_parser_tool

        # Create query engine using LlamaIndex's built-in tree_summarize
        # This automatically handles summarization on-the-fly using the hierarchical structure
        self.query_engine = self.index.as_query_engine(
            llm=self.llm,
            response_mode="tree_summarize",  # LlamaIndex's built-in hierarchical summarization
            similarity_top_k=15,  # Increased to retrieve more chunks for comprehensive summarization
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
- Provide comprehensive overviews and summaries using the hierarchical structure
- Include ALL claim types mentioned in the dataset (Auto, Health, Property, Travel, Life Insurance)
- Mention discrepancies between draft notes and final reports when relevant
- Explain timelines and sequences of events
- Identify key decisions and outcomes
- Highlight important entities and relationships
- Leverage the Claim → Document → Section hierarchy when relevant
- Reference metadata (claim_id, document_type, section, timestamp_range) when available
- Ensure completeness - don't omit claim types or important patterns

Use the Summary Index to answer the following query. 
Focus on high-level insights rather than specific details.
The tree_summarize response mode will automatically summarize relevant chunks hierarchically.

Query: {query}

Provide a comprehensive, well-structured response that covers all relevant information from the hierarchical structure.
"""
        )

    def _needs_date_parsing(self, query: str) -> bool:
        """Check if query requires date parsing tool"""
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in DATE_PARSING_KEYWORDS)

    def answer(self, query: str, return_chunks: bool = False) -> str | dict:
        """Answer high-level questions using the Summary Index with LlamaIndex's built-in summarization"""
        # Check if this needs date parsing
        if self.date_parser_tool and self._needs_date_parsing(query):
            try:
                # Extract dates from the query text
                dates_found = self.date_parser_tool.extract_dates_from_text(query)

                if dates_found:
                    # If dates were found, parse and normalize them
                    date_info = []
                    for date_data in dates_found:
                        date_info.append(
                            f"- Original: '{date_data['original']}' → "
                            f"Parsed: {date_data['normalized']}"
                        )

                    # If multiple dates found, calculate time difference
                    if len(dates_found) >= 2:
                        date1_str = dates_found[0]["original"]
                        date2_str = dates_found[1]["original"]
                        time_diff = self.date_parser_tool.calculate_date_difference(
                            date1_str, date2_str
                        )
                        if time_diff:
                            date_info.append(
                                f"\nTime Difference:\n"
                                f"- {time_diff['human_readable']} "
                                f"({time_diff['difference_days']} days, "
                                f"{time_diff['difference_hours']} hours)"
                            )

                    answer = f"Based on date parsing:\n\n" + "\n".join(date_info)
                    if return_chunks:
                        return {"answer": answer, "chunks": []}
                    return answer

            except Exception as e:
                print(
                    f"Warning: Date parser tool failed: {e}, falling back to standard query"
                )

        formatted_prompt = self.summarization_prompt.format(query=query)

        # Get retrieval results with scores
        if return_chunks:
            retriever = self.index.as_retriever(similarity_top_k=15)
            retrieved_nodes = retriever.retrieve(query)

            # Get top 3 chunks with scores
            top_chunks = []
            for i, node in enumerate(retrieved_nodes[:3]):
                score = (
                    node.score
                    if hasattr(node, "score")
                    else getattr(node, "score", 0.0)
                )
                chunk_text = (
                    node.text[:300] + "..." if len(node.text) > 300 else node.text
                )
                metadata = node.metadata if hasattr(node, "metadata") else {}
                top_chunks.append(
                    {
                        "rank": i + 1,
                        "score": float(score) if score else 0.0,
                        "text": chunk_text,
                        "metadata": metadata,
                    }
                )

            # Query the summary index - LlamaIndex handles summarization automatically via tree_summarize
            response = self.query_engine.query(formatted_prompt)
            return {"answer": str(response), "chunks": top_chunks}
        else:
            # Query the summary index - LlamaIndex handles summarization automatically via tree_summarize
            response = self.query_engine.query(formatted_prompt)
            return str(response)
