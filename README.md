# Midterm Assignment

## Setup

### Using Conda

1. Create the conda environment:
```bash
conda env create -f environment.yml
```

2. Activate the environment:
```bash
conda activate midterm-assignment
```

3. Install additional dependencies (if any):
```bash
pip install -r requirements.txt
```

## Development

Activate the conda environment before working:
```bash
conda activate midterm-assignment
```

## Project Structure

```
.
├── environment.yml          # Conda environment configuration
├── requirements.txt         # Python package dependencies
├── README.md               # Project documentation
├── README-agents.md        # Multi-agent system documentation
├── README-section2.md      # Data management & indexing documentation
├── .env                    # Environment variables (create from .env.example)
├── data/                   # Data directory (PDFs, documents)
├── storage/                # Persisted indexes (created automatically)
└── src/                    # Source code directory
    ├── agents.py           # Multi-agent system implementation
    ├── index_setup.py      # Index creation and loading
    ├── main.py             # Main demonstration script
    └── test_agents.py      # Test suite for agents
```

## Multi-Agent System

This project implements a multi-agent system using LlamaIndex with three specialized agents:

1. **Manager (Router) Agent** - Routes queries to appropriate agents
2. **Summarization Expert Agent** - Handles high-level questions using Summary Index
3. **Needle-in-a-Haystack Agent** - Handles precise queries using Hierarchical Index

See [README-agents.md](README-agents.md) for detailed documentation.

### Quick Start

1. Set up your OpenAI API key in `.env`:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

2. Run the demonstration:
   ```bash
   python src/main.py
   ```

3. Or run in interactive mode:
   ```bash
   python src/main.py --interactive
   ```

