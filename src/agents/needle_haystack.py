"""
Needle-in-a-Haystack Agent
Handles precise factual queries by searching deep inside the hierarchical index
Uses multi-size chunks (small, medium, large) with metadata for precise retrieval
Can use DateParserTool MCP for date parsing and normalization
"""

from typing import Optional
import re
import os
from llama_index.core import VectorStoreIndex
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


class NeedleInHaystackAgent:
    """
    Needle-in-a-Haystack Agent
    Handles precise factual queries by searching deep inside the hierarchical index
    Uses multi-size chunks (small, medium, large) with metadata for precise retrieval
    Can use DateParserTool MCP for date parsing and normalization
    """

    def __init__(
        self,
        hierarchical_index: VectorStoreIndex,
        date_parser_tool: Optional[DateParserTool] = None,
    ):
        self.index = hierarchical_index
        needle_model = os.getenv("NEEDLE_MODEL", "gpt-4o-mini")
        self.llm = OpenAI(temperature=0, model=needle_model)
        self.date_parser_tool = date_parser_tool

        # Create query engine optimized for precise retrieval
        # The hierarchical index contains multi-size chunks with metadata:
        # - Small chunks (150-250 tokens): High precision
        # - Medium chunks (400-600 tokens): Balanced reasoning
        # - Large chunks (800-1200 tokens): High-level context
        self.query_engine = self.index.as_query_engine(
            llm=self.llm,
            similarity_top_k=30,  # Increased to retrieve more chunks for better recall of rare information
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
- section: Section within the document (may include draft notes, call logs, internal memos, etc.)
- chunk_size: Size category (small, medium, large)
- timestamp_range: Time period covered

CRITICAL INSTRUCTIONS:
- Search THOROUGHLY through ALL retrieved chunks - information may appear only once
- Pay special attention to draft notes, call logs, internal memos, and one-off mentions
- Information that appears only once is often the most important - don't dismiss it
- If the query mentions a specific claim document (e.g., "Claim Document 01"), focus on chunks with matching claim_id or document metadata
- Check ALL sections including: call logs, draft notes, internal communications, medical reviewer notes, provider notes, underwriting remarks
- If initial chunks don't contain the answer, consider related terms and synonyms
- Be persistent - rare information requires careful examination of all retrieved chunks
- For numerical queries (readings, measurements, times), extract the EXACT value even if mentioned only once
- For yes/no questions, search for both positive and negative statements in all chunks
- If query asks about "Claim Document XX", search for that specific document number in all forms (01, 1, Document 01, etc.)

Your role is to:
- Find exact details, dates, names, numbers, and specific facts - even if mentioned only once
- Extract precise information from documents using metadata, especially from draft notes and internal documents
- Provide accurate, citation-ready answers with source context
- Search deeply through the hierarchical index structure (Claim → Document → Section → Chunk)
- Leverage chunk metadata (claim_id, document_type, section, timestamp_range) to focus your search
- Never say "information not available" without thoroughly checking all retrieved chunks

Query: {query}

Search through the hierarchical index with multi-size chunks and provide the exact, precise answer. 
Include specific details like dates, claim IDs, document numbers, names, and reference the metadata when available.
If you find information in draft notes, call logs, or internal memos, explicitly mention this source.
"""
        )

    def _needs_date_parsing(self, query: str) -> bool:
        """Check if query requires date parsing tool"""
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in DATE_PARSING_KEYWORDS)

    def _expand_query(self, query: str) -> str:
        """Expand query with synonyms and related terms to improve retrieval"""
        query_lower = query.lower()

        # Add synonyms and related terms for common concepts
        expansions = {
            "acknowledge": ["acknowledge", "admit", "accept", "recognize", "confirm"],
            "responsibility": ["responsibility", "liability", "fault", "blame"],
            "moisture": ["moisture", "humidity", "water", "dampness", "wetness"],
            "reading": ["reading", "measurement", "value", "level", "amount"],
            "inspection": [
                "inspection",
                "examination",
                "assessment",
                "review",
                "evaluation",
            ],
            "therapy": [
                "therapy",
                "treatment",
                "rehabilitation",
                "physical therapy",
                "PT",
            ],
            "complete": ["complete", "finished", "done", "completed", "finished"],
            "scanned": ["scanned", "read", "detected", "recorded", "logged"],
            "billing": ["billing", "charge", "code", "coding", "billed"],
            "error": ["error", "mistake", "incorrect", "wrong", "fault"],
            "misrepresentation": [
                "misrepresentation",
                "false statement",
                "misstatement",
                "inaccuracy",
            ],
        }

        # Build expanded query
        expanded_terms = [query]
        for key, synonyms in expansions.items():
            if key in query_lower:
                # Add synonyms that aren't already in the query
                for synonym in synonyms:
                    if synonym not in query_lower:
                        expanded_terms.append(synonym)

        # Also add claim document number variations if mentioned
        claim_match = re.search(r"claim\s+document\s+(\d+)", query, re.IGNORECASE)
        if claim_match:
            doc_num = claim_match.group(1)
            expanded_terms.extend(
                [
                    f"claim {doc_num}",
                    f"document {doc_num}",
                    f"claim document {doc_num}",
                ]
            )
            # Add zero-padded version only if doc_num is a valid integer
            try:
                doc_num_int = int(doc_num)
                expanded_terms.extend(
                    [
                        f"claim document {doc_num_int:02d}",
                        f"document {doc_num_int:02d}",
                        f"claim {doc_num_int:02d}",
                    ]
                )
            except ValueError:
                # If not a valid integer, just add the original
                expanded_terms.append(f"claim document {doc_num}")

        return " ".join(expanded_terms)

    def answer(self, query: str) -> str:
        """Answer precise factual queries using the Hierarchical Index with multi-size chunks"""
        # Check if this needs date parsing
        if self.date_parser_tool and self._needs_date_parsing(query):
            try:
                # First, get context from the index to find dates
                context_query = f"Extract dates and timestamps mentioned in: {query}"
                context_response = self.query_engine.query(context_query)
                context_text = str(context_response)

                # Extract dates from query and context
                query_dates = self.date_parser_tool.extract_dates_from_text(query)
                context_dates = self.date_parser_tool.extract_dates_from_text(
                    context_text
                )

                all_dates = query_dates + context_dates

                if all_dates:
                    # Format date information
                    date_info = []
                    for date_data in all_dates[:5]:  # Limit to first 5 dates
                        date_info.append(
                            f"- Found: '{date_data['original']}' → "
                            f"Normalized: {date_data['normalized']}"
                        )

                    # If multiple dates found, calculate time difference
                    if len(all_dates) >= 2:
                        date1_str = all_dates[0]["original"]
                        date2_str = all_dates[1]["original"]
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

                    return f"Based on date parsing:\n\n" + "\n".join(date_info)

            except Exception as e:
                print(
                    f"Warning: Date parser tool failed: {e}, falling back to standard query"
                )

        # Expand query for better retrieval
        expanded_query = self._expand_query(query)

        # Create enhanced prompt with expanded query
        formatted_prompt = self.precise_prompt.format(query=query)

        # Try primary query
        response = self.query_engine.query(formatted_prompt)
        answer = str(response)

        # Fallback: If answer seems incomplete or says "not available", try expanded query
        incomplete_phrases = [
            "not available",
            "cannot find",
            "no information",
            "unable to",
            "no mention",
            "does not mention",
            "not found",
            "unclear",
        ]

        if any(phrase in answer.lower() for phrase in incomplete_phrases):
            # Try with expanded query
            expanded_prompt = self.precise_prompt.format(
                query=f"{query} (Also search for: {expanded_query})"
            )
            fallback_response = self.query_engine.query(expanded_prompt)
            fallback_answer = str(fallback_response)

            # Use fallback if it seems more informative or doesn't contain incomplete phrases
            if len(fallback_answer) > len(answer) * 1.2 or not any(
                phrase in fallback_answer.lower() for phrase in incomplete_phrases
            ):
                return fallback_answer

        # Additional fallback: For queries asking about specific values or yes/no, try direct retrieval
        if any(
            keyword in query.lower()
            for keyword in [
                "reading",
                "value",
                "measurement",
                "time",
                "did",
                "was there",
            ]
        ):
            # Try a more direct query focusing on the specific information
            direct_query = f"Find the exact information: {query}. Search all chunks including draft notes and internal documents."
            direct_prompt = self.precise_prompt.format(query=direct_query)
            direct_response = self.query_engine.query(direct_prompt)
            direct_answer = str(direct_response)

            # Use direct answer if it's more informative and doesn't contain incomplete phrases
            if len(direct_answer) > len(answer) * 1.1 and not any(
                phrase in direct_answer.lower() for phrase in incomplete_phrases
            ):
                return direct_answer

        return answer
