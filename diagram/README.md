# Diagram Files

This folder contains all diagram-related files for the multi-agent system.

## Files

- **`agent_diagram.drawio`** - Draw.io XML format diagram file (editable in draw.io)
- **`agent_diagram.png`** - PNG version of the diagram (high resolution)
- **`agent_diagram.jpg`** - JPG version of the diagram (high resolution)
- **`agent_diagram.svg`** - SVG version of the diagram (vector format)
- **`view_diagram.html`** - HTML file to view the diagram in a browser
- **`create_agent_diagram.py`** - Python script to generate the diagram using matplotlib
- **`export_to_drawio.py`** - Python script to export the diagram as Draw.io XML format

## Usage

### Generate Diagram (Matplotlib)

```bash
cd diagram
python create_agent_diagram.py
```

This will generate `agent_diagram.png` and `agent_diagram.jpg` in the diagram folder.

### Export to Draw.io Format

```bash
cd diagram
python export_to_drawio.py
```

This will generate `agent_diagram.drawio` in the diagram folder.

### View Diagram

Open `view_diagram.html` in a web browser to view the diagram.

## Diagram Contents

The diagram shows:

- Manager → Sub-agent routing (HIGH_LEVEL vs PRECISE)
- Flow of data between indexes and agents
- MCP integration point (ClaimTimelineAnalyticsTool)
- Query expansion and fallback mechanism for Needle Agent
- Updated retrieval parameters (top_k=15 for Summary, top_k=20 for Hierarchical)
