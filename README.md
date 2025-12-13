# Multi-Agent System with MCP Integration

A comprehensive multi-agent system using LlamaIndex that demonstrates routing logic, index usage, model prompts as functions, and MCP (Model Context Protocol) tool integration for insurance claim analysis.

## Table of Contents

- [Architecture Explanation](#architecture-explanation)
- [Data Segmentation Decisions](#data-segmentation-decisions)
- [Chunking Rationale](#chunking-rationale)
- [Index Schemas](#index-schemas)
- [Agent Design + Prompt Structure](#agent-design--prompt-structure)
- [MCP Usage Explanation](#mcp-usage-explanation)
- [Evaluation Methodology + Examples](#evaluation-methodology--examples)
- [Limitations & Trade-offs](#limitations--trade-offs)
- [Setup](#setup)
- [Usage](#usage)
- [File Structure](#file-structure)

---

## Architecture Explanation

The system implements a **three-agent architecture** with intelligent routing and specialized indexes:

```
User Query
    ↓
Manager (Router) Agent
    ├─→ HIGH_LEVEL → Summarization Expert Agent → Summary Index
    └─→ PRECISE → Needle-in-a-Haystack Agent → Hierarchical Index
                    ↓
            DateParserTool (MCP) [when needed]
```

### System Components

#### 1. Manager (Router) Agent

- **Purpose**: Intelligent query routing based on intent analysis
- **Decision Logic**: Uses LLM-based prompt function to classify queries as HIGH_LEVEL or PRECISE
- **Fallback**: Keyword-based routing if LLM response is unclear
- **Output**: Routes to appropriate agent and index

#### 2. Summarization Expert Agent

- **Purpose**: Handles high-level analytical queries requiring overviews and summaries
- **Index**: Summary Index (large chunks, 800-1200 tokens)
- **Response Mode**: `tree_summarize` (LlamaIndex's built-in hierarchical summarization)
- **Retrieval**: `similarity_top_k=15` for comprehensive context
- **Optimization**: On-the-fly summarization (no upfront API calls)

#### 3. Needle-in-a-Haystack Agent

- **Purpose**: Handles precise factual queries requiring exact details
- **Index**: Hierarchical Index (multi-size chunks: small 200, medium 500, large 1000 tokens)
- **Response Mode**: `compact` for focused answers
- **Retrieval**: `similarity_top_k=20` for maximum recall
- **Features**: Query expansion, fallback mechanism, emphasis on rare information

#### 4. DateParserTool (MCP)

- **Purpose**: Extends LLM capabilities beyond text retrieval with date parsing and normalization
- **Integration**: Automatically invoked when date parsing keywords detected
- **Functions**: Parse dates from various formats, normalize dates, extract dates from text, calculate date differences

---

## Data Segmentation Decisions

### Hierarchical Structure

The system organizes data in a **four-level hierarchy**:

```
Claim → Document → Section → Chunk
```

**Rationale**:

- **Claim Level**: Top-level organization by insurance claim
- **Document Level**: Individual claim documents (PDFs)
- **Section Level**: Document sections (headers, call logs, draft notes, etc.)
- **Chunk Level**: Text segments with metadata

**Benefits**:

- Preserves relationships between events, notes, and decisions
- Enables targeted retrieval using metadata filters
- Supports both broad (claim-level) and narrow (chunk-level) queries
- Maintains context across document boundaries

### Metadata-Driven Segmentation

Each chunk carries rich metadata extracted using LLM-based structured extraction:

- **`claim_id`**: Claim identifier (e.g., "01", "02", "CLM-2025-1001")
- **`document_type`**: Type of claim (Auto Collision, Health, Property Damage, Travel, Life Insurance)
- **`section`**: Document section name (e.g., "CALL LOG", "DRAFT NOTES", "MEDICAL REVIEWER NOTES")
- **`chunk_size`**: Size category (small, medium, large)
- **`timestamp_range`**: Date range covered by the chunk
- **`page_numbers`**: Page references (if available)

**Why LLM-based extraction?**

- Handles varied document formats and naming conventions
- Extracts structured data from unstructured text
- Falls back to regex if LLM extraction fails
- More robust than manual pattern matching

---

## Chunking Rationale

### Multi-Size Chunking Strategy

The system uses **three chunk sizes** with different purposes:

#### Small Chunks (200 tokens)

- **Purpose**: High precision for specific facts
- **Use Case**: Finding exact details, dates, names, numbers
- **Example**: "What was the moisture reading in the earliest inspection?"
- **Trade-off**: May miss broader context

#### Medium Chunks (500 tokens)

- **Purpose**: Balanced reasoning for related events
- **Use Case**: Understanding sequences of related actions
- **Example**: "What happened between the accident and the first adjuster contact?"
- **Trade-off**: Balance between precision and context

#### Large Chunks (1000 tokens)

- **Purpose**: High-level context for summarization
- **Use Case**: Overview queries, timeline reconstruction
- **Example**: "What is the overall summary of all claims?"
- **Trade-off**: May include irrelevant details

### Overlap Strategy

**15-20% overlap** between consecutive chunks to:

- Prevent loss of important details at chunk boundaries
- Improve recall for information spanning multiple chunks
- Ensure context continuity

**Example**:

- Chunk 1: tokens 0-200
- Chunk 2: tokens 170-370 (30 token overlap)
- Chunk 3: tokens 340-540 (30 token overlap)

### Chunk Size Distribution

- **Hierarchical Index**: Contains ALL chunk sizes (small, medium, large)

  - Small chunks prioritized for precise queries
  - Medium chunks provide context
  - Large chunks offer broader understanding

- **Summary Index**: Contains ONLY large chunks
  - Sufficient context for summarization
  - Reduces index size and query complexity
  - Small/medium chunks remain in Hierarchical Index for precise queries

---

## Index Schemas

### Summary Index Schema

**Type**: `SummaryIndex` (LlamaIndex)
**Storage**: ChromaDB collection `summary_index`
**Chunks**: Large chunks only (1000 tokens)
**Response Mode**: `tree_summarize`

**Schema**:

```python
{
    "text": "<chunk content>",
    "metadata": {
        "claim_id": "01",
        "document_type": "Auto Collision",
        "section": "CLAIM SUMMARY",
        "chunk_size": "large",
        "timestamp_range": "2024-01-08 to 2024-01-15",
        "page_numbers": "1-3"
    },
    "node_id": "<unique_id>"
}
```

**Query Engine Configuration**:

- `similarity_top_k=15`: Retrieve 15 most relevant chunks
- `response_mode="tree_summarize"`: Hierarchical summarization
- `llm=GPT-4`: Temperature 0.3 for creative summarization

**Use Cases**:

- High-level overviews
- Claim type categorization
- Timeline summaries
- Pattern identification across claims

### Hierarchical Index Schema

**Type**: `VectorStoreIndex` (LlamaIndex)
**Storage**: ChromaDB collection `hierarchical_index`
**Chunks**: All sizes (small 200, medium 500, large 1000 tokens)
**Response Mode**: `compact`

**Schema**:

```python
{
    "text": "<chunk content>",
    "metadata": {
        "claim_id": "01",
        "document_type": "Auto Collision",
        "section": "CALL LOG",
        "chunk_size": "small",  # or "medium" or "large"
        "timestamp_range": "2024-01-08",
        "page_numbers": "2"
    },
    "node_id": "<unique_id>",
    "embedding": [<1536-dim vector>]  # OpenAI text-embedding-3-small
}
```

**Query Engine Configuration**:

- `similarity_top_k=20`: Retrieve 20 most relevant chunks (increased for better recall)
- `response_mode="compact"`: Focused, precise answers
- `llm=GPT-4`: Temperature 0 for deterministic answers

**Use Cases**:

- Precise factual queries
- Finding specific details
- Extracting exact values
- Searching for rare information

### ChromaDB Storage

Both indexes use **ChromaDB** for persistent vector storage:

- **Persistence**: Indexes survive restarts
- **Collections**: Separate collections for each index
- **Embeddings**: OpenAI `text-embedding-3-small` (1536 dimensions)
- **Metadata Filtering**: Supports filtering by claim_id, document_type, section, etc.

---

## Agent Design + Prompt Structure

### Model Prompts as Functions

Each agent uses **prompt functions** that encapsulate instructions and can be reused/modified:

#### 1. Manager Router Prompt

**Function**: `_create_routing_prompt()`

**Purpose**: Classify queries as HIGH_LEVEL or PRECISE

**Prompt Structure**:

```
You are a routing agent that determines which specialist agent should handle a query.

Query types:
1. HIGH_LEVEL: Questions about summaries, timelines, overviews, general trends
2. PRECISE: Questions about specific facts, exact details, dates, names, numbers

User Query: {query}

Respond with ONLY one word: either "HIGH_LEVEL" or "PRECISE"
```

**Design Rationale**:

- Simple, focused classification task
- Explicit examples reduce ambiguity
- Single-word response ensures consistency
- Fallback to keyword-based routing if LLM fails

#### 2. Summarization Expert Prompt

**Function**: `_create_summarization_prompt()`

**Purpose**: Guide high-level analysis and summarization

**Prompt Structure**:

```
You are a Summarization Expert Agent specializing in high-level analysis.

The Summary Index uses LlamaIndex's built-in tree_summarize with hierarchical structure:
- Large chunks organized by Claim → Document → Section hierarchy
- Metadata includes: claim_id, document_type, section, timestamp_range

Your role is to:
- Provide comprehensive overviews and summaries
- Include ALL claim types mentioned in the dataset
- Mention discrepancies between draft notes and final reports when relevant
- Explain timelines and sequences of events
- Identify key decisions and outcomes
- Ensure completeness - don't omit claim types or important patterns

Query: {query}

Provide a comprehensive, well-structured response that covers all relevant information.
```

**Design Rationale**:

- Emphasizes completeness (all claim types)
- Mentions specific metadata fields to leverage
- Instructs to check for discrepancies (important for evaluation)
- Guides hierarchical thinking

#### 3. Needle-in-a-Haystack Prompt

**Function**: `_create_precise_prompt()`

**Purpose**: Guide precise factual retrieval

**Prompt Structure**:

```
You are a Needle-in-a-Haystack Agent specializing in precise factual retrieval.

The Hierarchical Index uses multi-size chunking with metadata:
- Small chunks (150-250 tokens): High precision for specific facts
- Medium chunks (400-600 tokens): Balanced reasoning for related events
- Large chunks (800-1200 tokens): Context for broader understanding

CRITICAL INSTRUCTIONS:
- Search THOROUGHLY through ALL retrieved chunks - information may appear only once
- Pay special attention to draft notes, call logs, internal memos, and one-off mentions
- Information that appears only once is often the most important - don't dismiss it
- Check ALL sections including: call logs, draft notes, internal communications, medical reviewer notes, provider notes, underwriting remarks
- Be persistent - rare information requires careful examination of all retrieved chunks
- Never say "information not available" without thoroughly checking all retrieved chunks

Query: {query}

Search through the hierarchical index and provide the exact, precise answer.
If you find information in draft notes, call logs, or internal memos, explicitly mention this source.
```

**Design Rationale**:

- **Emphasizes thoroughness**: Critical for finding rare information
- **Mentions specific document types**: Draft notes, call logs (where rare info hides)
- **Warns against premature "not found"**: Prevents false negatives
- **Instructs source citation**: Helps with evaluation and trust

### Query Expansion

The Needle-in-a-Haystack Agent includes **query expansion** to improve retrieval:

**Function**: `_expand_query()`

**Expansion Strategy**:

- Adds synonyms for key terms (e.g., "acknowledge" → ["admit", "accept", "recognize"])
- Handles claim document number variations ("01" → "1", "01", "claim document 01")
- Expands domain-specific terms (e.g., "therapy" → ["treatment", "rehabilitation", "PT"])

**Example**:

```
Original: "Did the driver acknowledge responsibility?"
Expanded: "Did the driver acknowledge responsibility admit accept recognize confirm liability fault blame"
```

### Fallback Mechanism

If initial query returns "not available" or similar phrases, the system:

1. Automatically retries with expanded query
2. Compares answer lengths
3. Uses expanded result if significantly more informative

---

## MCP Usage Explanation

### What is MCP?

**Model Context Protocol (MCP)** allows LLMs to extend their capabilities beyond text generation by calling external tools/functions. This demonstrates **tool-augmented reasoning**.

### DateParserTool

**Purpose**: Parses and normalizes dates from various formats found in insurance claim documents. Uses the `python-dateutil` package to handle multiple date formats automatically.

**Why MCP?**

- LLMs are good at reading text but **struggle with consistent date parsing**
- Insurance documents contain dates in many formats (MM/DD/YYYY, "January 15, 2024", ISO, etc.)
- MCP tool provides **programmatic date parsing** using a well-tested library
- Returns **structured datetime objects** that LLM can use for calculations and formatting

### Tool Functions

#### 1. `parse_date(date_string: str)`

**Purpose**: Parse a date string into a datetime object

**Input**: Date string in any format

**Examples**:

```python
parse_date("2024-01-15")           # ISO format
parse_date("January 15, 2024")      # Full month name
parse_date("15/01/2024")            # European format
parse_date("Jan 15, 2024")          # Abbreviated month
```

**Output**: `datetime` object or `None` if parsing fails

**Use Case**: "Parse the date from 'January 15, 2024'"

#### 2. `normalize_date(date_string: str, format: str = "iso")`

**Purpose**: Normalize a date string to a standard format

**Formats**: "iso", "us", "european", "readable"

**Example**:

```python
normalize_date("Jan 15, 2024", "iso")        # → "2024-01-15T00:00:00"
normalize_date("2024-01-15", "us")           # → "01/15/2024"
normalize_date("2024-01-15", "readable")      # → "January 15, 2024"
```

**Use Case**: "Normalize the date 'Jan 15, 2024' to ISO format"

#### 3. `extract_dates_from_text(text: str)`

**Purpose**: Extract all date-like strings from text

**Input**: Text containing dates

**Example**:

```python
extract_dates_from_text("The claim was filed on Jan 15, 2024 and closed on Feb 20, 2024")
```

**Output**: List of dictionaries with parsed date information:

```python
[
    {
        "original": "Jan 15, 2024",
        "parsed": datetime(2024, 1, 15),
        "normalized": "2024-01-15T00:00:00"
    },
    {
        "original": "Feb 20, 2024",
        "parsed": datetime(2024, 2, 20),
        "normalized": "2024-02-20T00:00:00"
    }
]
```

**Use Case**: "Extract all dates from this claim document text"

#### 4. `calculate_date_difference(date1_str: str, date2_str: str, unit: str = "days")`

**Purpose**: Calculate the difference between two dates

**Input**: Two date strings

**Output**:

```python
{
    "date1": "2024-01-15T00:00:00",
    "date2": "2024-02-20T00:00:00",
    "difference_seconds": 3110400,
    "difference_days": 36,
    "difference_hours": 864.0,
    "difference_minutes": 51840.0,
    "human_readable": "36 days"
}
```

**Use Case**: "Calculate the time difference between January 15, 2024 and February 20, 2024"

### Integration Flow

```
User Query: "What date was the claim filed? Parse 'January 15, 2024'"
    ↓
Agent detects date parsing keywords ("date", "parse")
    ↓
Agent extracts date strings from query
    ↓
Agent calls: date_parser_tool.parse_date("January 15, 2024")
    ↓
Tool returns datetime object
    ↓
Agent formats tool output into natural language answer
    ↓
Final Answer: "The date 'January 15, 2024' was parsed and normalized to 2024-01-15T00:00:00"
```

### Detection Logic

**Keywords that trigger MCP tool**:

- "date", "when", "timestamp"
- "format", "parse date", "normalize date"
- "extract date", "date string", "convert date"
- "time difference", "calculate time", "between dates"

**Both agents** (Summarization Expert and Needle-in-a-Haystack) can use the tool when needed.

### Package Used

The tool uses the **`python-dateutil`** package, a well-established library for date parsing:

- Handles many date formats automatically
- Robust parsing with fuzzy matching
- No LLM dependency - pure computational tool
- Commonly used in Python projects

---

## Evaluation Methodology + Examples

### Evaluation Approach: LLM-as-a-Judge

The system uses **GPT-4 as a judge model** to evaluate performance across three metrics:

1. **Answer Correctness** (40% weight)
2. **Context Relevancy** (30% weight)
3. **Context Recall** (30% weight)

**Why LLM-as-a-Judge?**

- More nuanced than exact string matching
- Can evaluate semantic correctness
- Provides reasoning explanations
- Handles variations in phrasing

### Evaluation Metrics

#### 1. Answer Correctness

**Prompt**: Evaluates whether the system's answer correctly addresses the query and matches ground truth.

**Criteria**:

- Does the answer directly address the query?
- Does it contain key information from ground truth?
- Is it factually accurate?
- Is it complete (not missing important details)?

**Scoring**:

- 0.8-1.0: Excellent match with ground truth
- 0.6-0.7: Good match, minor details missing
- 0.4-0.5: Partial match, some key information missing
- 0.0-0.3: Poor match or incorrect

**Example**:

```
Query: "In Claim Document 01, did the other driver acknowledge responsibility?"
Ground Truth: "Yes, the other driver informally acknowledged responsibility according to an internal call log."
System Answer: "Yes, the driver acknowledged responsibility in a call log."

Score: 0.8
Reasoning: Answer correctly identifies acknowledgment but misses "informally" and "internal call log" details.
```

#### 2. Context Relevancy

**Prompt**: Evaluates whether the system used the correct index and relevant context segments.

**Criteria**:

- Was the correct index used (Summary vs Hierarchical)?
- Does the answer reflect information from relevant document sections?
- Is the context appropriate for the query type?

**Scoring**:

- 0.9-1.0: Correct index, highly relevant context
- 0.7-0.8: Correct index, mostly relevant context
- 0.5-0.6: Correct index but some irrelevant context
- 0.0-0.4: Wrong index or irrelevant context

**Example**:

```
Query: "What was the moisture reading in Claim Document 03?"
Expected Index: Hierarchical Index
Actual Index: Hierarchical Index
Expected Context: Moisture readings, inspection reports, draft notes

Score: 0.9
Reasoning: Correct index used, context is relevant to moisture readings and inspections.
```

#### 3. Context Recall

**Prompt**: Evaluates whether the system retrieved the correct information chunks.

**Criteria**:

- Does the answer contain information from expected chunks?
- Were the correct document sections retrieved?
- Is important information missing?

**Scoring**:

- 0.8-1.0: Correct chunks retrieved, complete information
- 0.6-0.7: Some relevant chunks retrieved, some important info missing
- 0.4-0.5: Partial retrieval, significant gaps
- 0.0-0.3: Failed to retrieve correct chunks

**Example**:

```
Query: "What billing code error was mentioned in Claim Document 07?"
Expected Info: Provider notes about billing code errors
System Answer: "No information available about billing code errors."

Score: 0.0
Reasoning: System failed to retrieve the provider note containing billing code error information.
Missing Info: Provider's note about incorrectly coded billed charge.
```

### Test Suite

**8 test cases** covering different scenarios:

#### High-Level Queries (2 tests)

1. **Overall Summary**

   - Query: "What is the overall summary of all insurance claims?"
   - Expected: Summary Index, HIGH_LEVEL route
   - Ground Truth: Dataset contains 10 insurance claims covering various types...

2. **Claim Types**
   - Query: "What are the main types of insurance claims in the dataset?"
   - Expected: Summary Index, HIGH_LEVEL route
   - Ground Truth: Auto Collision, Health, Property Damage, Travel, Life Insurance...

#### Precise Factual Queries (6 tests)

3. **Driver Acknowledgment** (Claim 01)

   - Query: "In Claim Document 01, did the other driver acknowledge responsibility?"
   - Expected: Hierarchical Index, PRECISE route
   - Ground Truth: Yes, informally acknowledged in internal call log...

4. **Moisture Reading** (Claim 03)

   - Query: "What was the moisture reading in the earliest inspection for the Apartment Water Damage claim?"
   - Expected: Hierarchical Index, PRECISE route
   - Ground Truth: Significantly higher than final report value, appears only in draft note...

5. **Physical Therapy** (Claim 05)

   - Query: "Did the patient complete conservative physical therapy in Claim Document 05?"
   - Expected: Hierarchical Index, PRECISE route
   - Ground Truth: Yes, medical reviewer noted completion...

6. **Luggage Scanning** (Claim 06)

   - Query: "What time was the luggage scanned in Claim Document 06?"
   - Expected: Hierarchical Index, PRECISE route
   - Ground Truth: Scanned earlier than reported time, timestamp ignored in claim outcome...

7. **Billing Code Error** (Claim 07)

   - Query: "What billing code error was mentioned in Claim Document 07?"
   - Expected: Hierarchical Index, PRECISE route
   - Ground Truth: Provider confirmed incorrect coding in one-line note...

8. **Misrepresentation Evidence** (Claim 09)
   - Query: "Was there evidence of misrepresentation in Claim Document 09?"
   - Expected: Hierarchical Index, PRECISE route
   - Ground Truth: No evidence, underwriting remark states no misrepresentation...

### Running Evaluation

```bash
python src/run_evaluation.py
```

**Output**:

1. Per-test-case scores and reasoning
2. Summary statistics (average scores, routing accuracy, index selection accuracy)
3. Category breakdown (high-level vs precise queries)
4. Detailed JSON results saved to `evaluation_results.json`

### Evaluation Results Format

```json
{
  "timestamp": "2025-01-27T12:00:00",
  "total_tests": 8,
  "successful_evaluations": 8,
  "results": [
    {
      "test_case": {
        "query": "...",
        "category": "Precise Factual",
        "expected_route": "PRECISE",
        "expected_index": "Hierarchical Index"
      },
      "system_result": {
        "route": "PRECISE",
        "index_used": "Hierarchical Index",
        "agent_used": "Needle-in-a-Haystack Agent",
        "date_parser_tool_used": false
      },
      "evaluation": {
        "correctness": {
          "score": 0.8,
          "reasoning": "...",
          "correct": true
        },
        "relevancy": {
          "score": 0.9,
          "reasoning": "...",
          "correct_index": true,
          "relevant_context": true
        },
        "recall": {
          "score": 0.7,
          "reasoning": "...",
          "retrieved_correct": true,
          "missing_info": "..."
        },
        "overall_score": 0.8
      }
    }
  ]
}
```

### Summary Statistics

- **Average Correctness**: Weighted average across all test cases
- **Average Relevancy**: Weighted average across all test cases
- **Average Recall**: Weighted average across all test cases
- **Overall Score**: Weighted combination (40% correctness + 30% relevancy + 30% recall)
- **Routing Accuracy**: Percentage of queries correctly routed
- **Index Selection Accuracy**: Percentage of queries using correct index

---

## Limitations & Trade-offs

### 1. Retrieval Limitations

**Challenge**: Finding rare information that appears only once in draft notes or specific sections.

**Mitigation**:

- Increased `similarity_top_k` to 20 for precise queries
- Query expansion with synonyms
- Enhanced prompts emphasizing thoroughness
- Fallback mechanism for failed retrievals

**Trade-off**: Higher `similarity_top_k` increases API costs and latency.

### 2. LLM-Based Metadata Extraction

**Challenge**: LLM extraction may be inconsistent or fail for unusual document formats.

**Mitigation**:

- Fallback to JSON mode parsing
- Final fallback to regex-based extraction
- Error handling and default values

**Trade-off**: More robust but slower than pure regex. May incur API costs during indexing.

### 3. ChromaDB Storage

**Challenge**: Index size grows with document count.

**Mitigation**:

- Separate collections for Summary and Hierarchical indexes
- Large chunks only in Summary Index
- Persistent storage allows reuse without re-indexing

**Trade-off**: Disk space usage, but enables fast querying without re-indexing.

### 4. Evaluation Cost

**Challenge**: LLM-as-a-Judge requires API calls for each test case (3 calls per test: correctness, relevancy, recall).

**Impact**: 8 test cases × 3 evaluations = 24 judge API calls per evaluation run.

**Trade-off**: More nuanced evaluation than exact matching, but higher cost.

### 5. Query Expansion Overhead

**Challenge**: Query expansion and fallback mechanism may increase latency.

**Mitigation**:

- Expansion only for Needle-in-a-Haystack Agent
- Fallback only triggered when initial answer indicates failure
- Cached query engines reduce repeated initialization

**Trade-off**: Better recall vs. increased latency.

### 6. Date Parser Tool Limitations

**Challenge**: DateParserTool relies on dateutil's parsing, which may misinterpret ambiguous dates.

**Mitigation**:

- dateutil handles most common formats automatically
- Fuzzy parsing can extract dates from context
- Graceful error handling if parsing fails

**Trade-off**: Simpler than custom parsing, but may occasionally misinterpret ambiguous date formats.

### 7. Prompt Engineering Sensitivity

**Challenge**: System performance depends on prompt quality.

**Mitigation**:

- Iterative prompt refinement based on evaluation results
- Explicit instructions for rare information retrieval
- Clear role definitions for each agent

**Trade-off**: Better prompts improve performance, but require careful design and testing.

### 8. Multi-Size Chunking Complexity

**Challenge**: Managing three chunk sizes increases complexity.

**Mitigation**:

- Clear separation: Summary Index (large only) vs Hierarchical Index (all sizes)
- Metadata-driven filtering
- Overlap prevents boundary issues

**Trade-off**: More complex indexing, but better precision and recall.

### 9. Routing Accuracy

**Challenge**: LLM-based routing may misclassify ambiguous queries.

**Mitigation**:

- Keyword-based fallback
- Explicit examples in routing prompt
- Validation of routing decisions

**Trade-off**: More flexible than rule-based routing, but less deterministic.

### 10. API Rate Limits

**Challenge**: Multiple LLM calls (routing, querying, evaluation) may hit rate limits.

**Mitigation**:

- Caching of query engines
- Batch processing where possible
- Error handling with retries

**Trade-off**: Better performance vs. potential rate limit issues.

---

## Setup

1. **Install dependencies**:

```bash
conda activate midterm-assignment
pip install -r requirements.txt
```

2. **Set up OpenAI API key**:
   Create a `.env` file in the project root:

```
OPENAI_API_KEY=your_api_key_here
```

3. **Run the demonstration**:

```bash
python src/main.py
```

4. **Run in interactive mode**:

```bash
python src/main.py --interactive
```

5. **Run evaluation**:

```bash
python src/run_evaluation.py
```

## Usage

### Basic Query Examples

**High-Level Query:**

```
Query: What is the overall summary of all insurance claims?
→ Routes to: Summarization Expert Agent
→ Uses: Summary Index
```

**Precise Query:**

```
Query: What was the moisture reading in Claim Document 03?
→ Routes to: Needle-in-a-Haystack Agent
→ Uses: Hierarchical Index
```

**Date Parsing Query:**

```
Query: What date was the claim filed? Parse 'January 15, 2024'
→ Routes to: Appropriate Agent
→ Uses: DateParserTool MCP
```

## File Structure

```
.
├── src/
│   ├── agents.py              # Multi-agent system implementation
│   ├── index_setup.py         # Index creation and loading
│   ├── document_processor.py  # Hierarchical document processing
│   ├── date_parser_tool.py  # MCP tool for date parsing (using python-dateutil)
│   ├── evaluator.py           # LLM-as-a-judge evaluation system
│   ├── evaluation_suite.py    # Test cases with ground truth
│   ├── run_evaluation.py      # Evaluation runner script
│   └── main.py                # Main demonstration script
├── data/                      # Claim documents (PDFs)
├── storage/                   # Persisted data
│   ├── hierarchy_info.json    # Hierarchy metadata
├── chroma_db/                # ChromaDB vector store
├── evaluation_results.json    # Detailed evaluation results
├── README.md                  # This file
├── README-agents.md           # Agent system documentation
├── README-section2.md         # Data management documentation
├── EVALUATION_SUMMARY.md      # Evaluation summary
└── requirements.txt           # Python dependencies
```

## Example Output

```
Query: What is the overall summary of the insurance claim?

📊 Routing Decision: HIGH_LEVEL
🤖 Agent Used: Summarization Expert Agent
📚 Index Used: Summary Index

💬 Answer:
[Comprehensive summary based on Summary Index]
```

```
Query: What is the exact claim ID?

📊 Routing Decision: PRECISE
🤖 Agent Used: Needle-in-a-Haystack Agent
📚 Index Used: Hierarchical Index

💬 Answer:
[Precise answer with claim ID from Hierarchical Index]
```

```
Query: What date was the claim filed? Parse 'January 15, 2024'

📊 Routing Decision: PRECISE
🤖 Agent Used: Needle-in-a-Haystack Agent
📚 Index Used: Hierarchical Index
🔧 Date Parser Tool Used: Yes (DateParserTool MCP)

💬 Answer:
[Date parsing result from MCP tool]
```

## License

This project is part of a midterm assignment.
