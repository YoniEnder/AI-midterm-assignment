# Multi-Agent System Implementation

This implementation demonstrates a multi-agent system using LlamaIndex with three specialized agents.

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

## Key Features Demonstrated

### ✅ Routing Logic
The Manager Agent uses a prompt-based routing function to classify queries:
- Analyzes query intent
- Determines if query needs high-level summary or precise facts
- Routes to appropriate agent

### ✅ Use of Indexes
- **Summary Index**: Optimized for high-level queries with larger chunks
- **Hierarchical Index**: Optimized for precise queries with smaller chunks
- Both indexes are persisted and can be reloaded

### ✅ Model Prompts as Functions
Each agent uses prompt functions:
- `_create_routing_prompt()`: Manager routing logic
- `_create_summarization_prompt()`: Summarization expert instructions
- `_create_precise_prompt()`: Needle-in-a-haystack instructions

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

## File Structure

```
src/
├── agents.py          # All three agent implementations
├── index_setup.py     # Index creation and loading logic
└── main.py            # Main demonstration and orchestration
```

## How It Works

1. **Index Creation**: 
   - Loads documents from `./data/` directory
   - Creates two indexes with different chunking strategies
   - Persists indexes to `./storage/` for reuse

2. **Query Processing**:
   - User submits a query
   - Manager Agent routes the query
   - Appropriate agent processes the query using its specialized index
   - Response includes routing decision and answer

3. **Demonstration**:
   - Shows routing decisions for different query types
   - Displays which agent and index were used
   - Provides the final answer

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

