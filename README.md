# Multi-Agent System with MCP Integration

A comprehensive multi-agent system using LlamaIndex that demonstrates routing logic, index usage, model prompts as functions, and MCP (Model Context Protocol) tool integration for insurance claim analysis.

## Table of Contents

- [Architecture](#architecture)
- [Features](#features)
- [Setup](#setup)
- [Usage](#usage)
- [MCP Integration](#mcp-integration)
- [System Evaluation](#system-evaluation)
- [File Structure](#file-structure)

## Architecture

### 1. Manager (Router) Agent

- **Purpose**: Receives user queries and determines which agent should handle them
- **Functionality**:
  - Analyzes query intent using a routing prompt function
  - Routes to either HIGH_LEVEL or PRECISE queries
  - Selects the appropriate index (Summary vs Hierarchical)

### 2. Summarization Expert Agent

- **Purpose**: Answers high-level questions about summaries, timelines, and overviews
- **Index Used**: Summary Index
- **Optimization**: Uses larger chunks (800-1200 tokens) for better context
- **Use Cases**:
  - "What is the overall summary?"
  - "Give me a timeline of events"
  - "What are the key decisions?"

### 3. Needle-in-a-Haystack Agent

- **Purpose**: Handles precise factual queries requiring exact details
- **Index Used**: Hierarchical Index (VectorStore)
- **Optimization**: Uses smaller chunks (150-250 tokens) for better precision
- **Use Cases**:
  - "What is the exact claim ID?"
  - "What was the specific date?"
  - "Who signed document X?"

### 4. ClaimTimelineAnalyticsTool (MCP)

- **Purpose**: Performs numerical and logical analysis over claim timelines
- **Functions**:
  - `time_diff()`: Calculate time differences between events
  - `sla_check()`: Check SLA violations
  - `timeline_summary_stats()`: Get timeline statistics
  - `events_in_range()`: Get events within a time range

## Features

### ✅ Routing Logic

The Manager Agent uses a prompt-based routing function to classify queries:

- Analyzes query intent
- Determines if query needs high-level summary or precise facts
- Routes to appropriate agent

### ✅ Use of Indexes

- **Summary Index**: Optimized for high-level queries with larger chunks
- **Hierarchical Index**: Optimized for precise queries with smaller chunks
- Both indexes are persisted in ChromaDB and can be reloaded

### ✅ Model Prompts as Functions

Each agent uses prompt functions:

- `_create_routing_prompt()`: Manager routing logic
- `_create_summarization_prompt()`: Summarization expert instructions
- `_create_precise_prompt()`: Needle-in-a-haystack instructions

### ✅ MCP Tool Integration

- Automatic detection of timeline analytics queries
- Both agents can call ClaimTimelineAnalyticsTool when needed
- Tool provides precise numerical analysis beyond text retrieval

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

**Timeline Analytics Query:**

```
Query: How many hours passed between the accident and first inspection?
→ Routes to: Appropriate Agent
→ Uses: ClaimTimelineAnalyticsTool MCP
```

## MCP Integration

The ClaimTimelineAnalyticsTool is automatically invoked when queries contain timeline analytics keywords such as:

- "how long", "hours between", "time between"
- "sla", "violated", "breach"
- "duration", "total time", "timeline stats"

### Example MCP Usage

```python
# Time difference calculation
result = timeline_tool.time_diff(
    claim_id="01",
    from_event_type="FNOL_REPORTED",
    to_event_type="FIRST_ADJUSTER_CONTACT"
)

# SLA violation check
result = timeline_tool.sla_check(
    claim_id="01",
    sla_hours=48,
    from_event_type="FNOL_REPORTED",
    to_event_type="FIRST_ADJUSTER_CONTACT"
)
```

## System Evaluation

### Evaluation Methodology

The system is evaluated using **LLM-as-a-Judge** approach with GPT-4 as the judge model. Evaluation covers three key metrics:

1. **Answer Correctness** (40% weight): Does the answer match ground truth?
2. **Context Relevancy** (30% weight): Did the agent use the correct index and relevant segments?
3. **Context Recall** (30% weight): Did the system retrieve the correct chunk(s)?

### Test Suite

The evaluation uses **8 test cases** covering:

- **High-Level Queries** (2 tests): Summary and categorization queries
- **Precise Factual Queries** (6 tests): Specific details from individual claim documents

#### Test Cases

1. **Overall Summary Query**

   - Query: "What is the overall summary of all insurance claims?"
   - Expected: Summary Index, HIGH_LEVEL route
   - Ground Truth: Dataset contains 10 insurance claims covering various types...

2. **Driver Acknowledgment** (Claim 01)

   - Query: "In Claim Document 01, did the other driver acknowledge responsibility?"
   - Expected: Hierarchical Index, PRECISE route
   - Ground Truth: Yes, informally acknowledged in internal call log...

3. **Moisture Reading** (Claim 03)

   - Query: "What was the moisture reading in the earliest inspection for the Apartment Water Damage claim?"
   - Expected: Hierarchical Index, PRECISE route
   - Ground Truth: Significantly higher than final report value...

4. **Physical Therapy** (Claim 05)

   - Query: "Did the patient complete conservative physical therapy in Claim Document 05?"
   - Expected: Hierarchical Index, PRECISE route
   - Ground Truth: Yes, medical reviewer noted completion...

5. **Luggage Scanning** (Claim 06)

   - Query: "What time was the luggage scanned in Claim Document 06?"
   - Expected: Hierarchical Index, PRECISE route
   - Ground Truth: Scanned earlier than reported time...

6. **Billing Code Error** (Claim 07)

   - Query: "What billing code error was mentioned in Claim Document 07?"
   - Expected: Hierarchical Index, PRECISE route
   - Ground Truth: Provider confirmed incorrect coding...

7. **Claim Types**

   - Query: "What are the main types of insurance claims in the dataset?"
   - Expected: Summary Index, HIGH_LEVEL route
   - Ground Truth: Auto Collision, Health, Property Damage, Travel, Life Insurance...

8. **Misrepresentation Evidence** (Claim 09)
   - Query: "Was there evidence of misrepresentation in Claim Document 09?"
   - Expected: Hierarchical Index, PRECISE route
   - Ground Truth: No evidence, underwriting remark states...

### Running Evaluation

```bash
python src/run_evaluation.py
```

This will:

1. Load the system and indexes
2. Run all 8 test cases
3. Evaluate each using LLM-as-a-judge
4. Generate summary statistics
5. Save detailed results to `evaluation_results.json`

### Evaluation Prompts

#### Correctness Prompt

Evaluates whether the system's answer correctly addresses the query and matches ground truth. Returns:

- Score (0.0 to 1.0)
- Reasoning explanation
- Correct flag (true if score >= 0.7)

#### Relevancy Prompt

Evaluates whether the system used the correct index and relevant context segments. Returns:

- Score (0.0 to 1.0)
- Reasoning explanation
- Correct index flag
- Relevant context flag

#### Recall Prompt

Evaluates whether the system retrieved the correct information chunks. Returns:

- Score (0.0 to 1.0)
- Reasoning explanation
- Retrieved correct flag
- Missing information list

### Evaluation Results Format

Each test case evaluation includes:

```json
{
  "query": "...",
  "route": "HIGH_LEVEL" | "PRECISE",
  "index_used": "Summary Index" | "Hierarchical Index",
  "correctness": {
    "score": 0.0-1.0,
    "reasoning": "...",
    "correct": true/false
  },
  "relevancy": {
    "score": 0.0-1.0,
    "reasoning": "...",
    "correct_index": true/false,
    "relevant_context": true/false
  },
  "recall": {
    "score": 0.0-1.0,
    "reasoning": "...",
    "retrieved_correct": true/false,
    "missing_info": "..."
  },
  "overall_score": 0.0-1.0
}
```

### Summary Statistics

The evaluation generates:

- Average scores for each metric
- Overall weighted average score
- Routing accuracy percentage
- Index selection accuracy percentage
- Performance breakdown by query category

See `EVALUATION_SUMMARY.md` for a concise summary of results.

## File Structure

```
.
├── src/
│   ├── agents.py              # Multi-agent system implementation
│   ├── index_setup.py         # Index creation and loading
│   ├── document_processor.py  # Hierarchical document processing
│   ├── timeline_analytics_tool.py  # MCP tool for timeline analytics
│   ├── timeline_extractor.py  # Timeline event extraction
│   ├── evaluator.py           # LLM-as-a-judge evaluation system
│   ├── evaluation_suite.py    # Test cases with ground truth
│   ├── run_evaluation.py      # Evaluation runner script
│   └── main.py                # Main demonstration script
├── data/                      # Claim documents (PDFs)
├── storage/                   # Persisted data
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
Query: How many hours passed between the accident and first inspection?

📊 Routing Decision: PRECISE
🤖 Agent Used: Needle-in-a-Haystack Agent
📚 Index Used: Hierarchical Index
🔧 Timeline Tool Used: Yes (ClaimTimelineAnalyticsTool MCP)

💬 Answer:
[Precise time calculation from MCP tool]
```

## License

This project is part of a midterm assignment.

