# Multi-Agent System with MCP Integration

A multi-agent system using LlamaIndex for insurance claim analysis with intelligent routing, specialized indexes, and MCP (Model Context Protocol) tool integration.

## Architecture Explanation

**Three-agent architecture with intelligent routing:**

```
User Query → Manager Router Agent
    ├─→ HIGH_LEVEL → Summarization Expert Agent → Summary Index
    └─→ PRECISE → Needle-in-a-Haystack Agent → Hierarchical Index
                    ↓
            DateParserTool (MCP) [when needed]
```

**Components:**

- **Manager Router Agent**: LLM-based query classification (HIGH_LEVEL vs PRECISE) with keyword fallback
- **Summarization Expert Agent**: Handles overviews, timelines, summaries using `tree_summarize` mode, `top_k=15`
- **Needle-in-a-Haystack Agent**: Handles precise facts, exact details using `compact` mode, `top_k=30`, with query expansion
- **DateParserTool (MCP)**: Extends LLM capabilities with date parsing, normalization, and calculation

## Data Segmentation Decisions

**Hierarchical Structure:** Claim → Document → Section → Chunk

Documents are organized by:

- **Claim ID**: Extracted identifiers (e.g., "01", "CLM-2025-1001")
- **Document Type**: Auto Collision, Health, Property Damage, Fire, Travel, Life Insurance
- **Section**: Document sections (call logs, draft notes, internal memos, medical reviews, etc.)
- **Timestamp Range**: Date ranges extracted from documents

Metadata is extracted using LLM with structured output (Pydantic models) for consistency.

## Chunking Rationale

**Multi-size chunking strategy:**

- **Small chunks (150-250 tokens)**: High precision for specific facts, rare information
- **Medium chunks (400-600 tokens)**: Balanced reasoning for related events
- **Large chunks (800-1200 tokens)**: High-level context for summarization

**Rationale:** Different query types require different granularity. Precise queries need small chunks to find rare information (e.g., draft notes, one-off mentions). Summary queries need large chunks with sufficient context for hierarchical summarization.

## Index Schemas

**Summary Index:**

- **Chunks**: Large chunks only (800-1200 tokens)
- **Storage**: ChromaDB (persistent)
- **Use Case**: High-level queries, overviews, timelines
- **Response Mode**: `tree_summarize` (LlamaIndex built-in hierarchical summarization)

**Hierarchical Index:**

- **Chunks**: Multi-size (small/medium/large)
- **Storage**: ChromaDB (persistent)
- **Use Case**: Precise factual queries, exact details
- **Response Mode**: `compact` for focused answers
- **Metadata**: claim_id, document_type, section, chunk_size, timestamp_range

## Agent Design + Prompt Structure

**Manager Router Agent:**

- **Prompt**: Classifies queries as HIGH_LEVEL (summaries, timelines, overviews) or PRECISE (exact facts, dates, names, numbers)
- **Fallback**: Keyword-based routing if LLM response unclear

**Summarization Expert Agent:**

- **Prompt**: Emphasizes comprehensive overviews, hierarchical structure (Claim → Document → Section), completeness
- **Response Mode**: `tree_summarize` for automatic hierarchical summarization
- **Retrieval**: `similarity_top_k=15`

**Needle-in-a-Haystack Agent:**

- **Prompt**: Emphasizes thorough search, attention to draft notes/call logs/internal memos, rare information that appears only once
- **Response Mode**: `compact` for focused answers
- **Retrieval**: `similarity_top_k=30` for maximum recall
- **Query Expansion**: Synonyms, related terms, document number variations
- **Fallback**: Multiple retrieval attempts if initial answer incomplete

## MCP Usage Explanation

**DateParserTool (MCP)** extends LLM capabilities beyond text retrieval:

- **Automatic Detection**: Triggered by date-related keywords (date, time, when, timestamp, etc.)
- **Functions**:
  - Parse dates from various formats (natural language, ISO, etc.)
  - Normalize dates to standard format
  - Extract dates from text
  - Calculate date differences
- **Integration**: Available to both agents when date parsing is needed
- **Use Case**: Queries like "What date was the claim filed?" or "When was the inspection completed?"

## Evaluation Methodology + Examples

**LLM-as-a-Judge Evaluation:**

- **Metrics**: Correctness (0.4 weight), Relevancy (0.3 weight), Recall (0.3 weight)
- **Test Suite**: 11 test cases (6 precise + 4 summary tests + 1 categorization)
- **Categories**: High-Level Summary, Precise Factual, High-Level Categorization

**Example Results:**

- **High-Level Summary**: 0.95 average score (4 tests) - comprehensive summaries with excellent recall
- **Precise Factual**: 0.77 average score (6 tests) - challenges with rare information appearing only once (scores range from 0.44 to 1.0)
- **High-Level Categorization**: 0.96 average score (1 test)
- **Routing Accuracy**: 100% - correct index selection for all 11 queries

**Evaluation Example:**

```
Query: "What is the overall summary of all insurance claims?"
Route: HIGH_LEVEL → Summarization Expert → Summary Index
Score: Correctness 1.00, Relevancy 1.00, Recall 1.00, Overall 1.00
```

## Limitations & Trade-offs

**Limitations:**

- **Rare Information**: Information appearing only once (draft notes, internal memos) may be missed despite `top_k=30`
- **Precise Queries**: Some precise queries score lower (0.44-0.97) due to difficulty retrieving rare information, with average of 0.77
- **Summary Index**: Uses VectorStoreIndex instead of SummaryIndex for ChromaDB persistence (functional equivalence)
- **Query Expansion**: May retrieve irrelevant chunks, but improves recall for rare information

**Trade-offs:**

- **Chunk Size vs Precision**: Small chunks improve precision but may miss context; large chunks provide context but reduce precision
- **Retrieval Count**: Higher `top_k` improves recall but increases processing time and token usage
- **Routing**: LLM-based routing is flexible but may misclassify ambiguous queries (mitigated by keyword fallback)
- **Persistence**: ChromaDB persistence adds complexity but enables faster subsequent runs

**Setup:** Install dependencies (`pip install -r requirements.txt`), set `OPENAI_API_KEY`, run `python src/main.py` or `python src/evaluation/run_evaluation.py`
