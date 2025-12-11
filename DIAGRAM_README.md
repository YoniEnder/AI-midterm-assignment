# Agent System Diagram

This directory contains diagrams showing the Multi-Agent System architecture with MCP integration.

## Files

1. **`agent_diagram.svg`** - Scalable Vector Graphics format
   - Can be opened in any web browser
   - Can be converted to PNG/JPEG using online tools or image editors
   - Best for high-quality printing and scaling

2. **`agent_diagram.drawio`** - Draw.io format
   - Can be opened in [draw.io](https://app.diagrams.net/) (free, web-based)
   - Can be edited and exported to PNG/JPEG
   - Best for making edits

3. **`create_agent_diagram.py`** - Python script (requires matplotlib)
   - Generates PNG and JPG versions
   - Run: `python create_agent_diagram.py`
   - Requires: `pip install matplotlib`

## Quick View/Convert Options

### Option 1: View SVG in Browser
1. Open `agent_diagram.svg` in any web browser
2. Right-click → "Save image as" → Save as PNG/JPEG

### Option 2: Use Draw.io (Recommended)
1. Go to [app.diagrams.net](https://app.diagrams.net/)
2. File → Open → Select `agent_diagram.drawio`
3. File → Export as → PNG or JPEG
4. Set resolution to 300 DPI for high quality

### Option 3: Online SVG to PNG Converter
1. Upload `agent_diagram.svg` to:
   - [CloudConvert](https://cloudconvert.com/svg-to-png)
   - [Convertio](https://convertio.co/svg-png/)
   - [Any other SVG converter](https://www.google.com/search?q=svg+to+png+converter)
2. Download PNG/JPEG

### Option 4: Command Line (if ImageMagick installed)
```bash
convert agent_diagram.svg -density 300 agent_diagram.png
```

## Diagram Contents

The diagram shows:

1. **Manager → Sub-agent Routing**
   - User Query → Manager Router Agent
   - Manager routes to HIGH_LEVEL (Summarization) or PRECISE (Needle)
   - Color-coded arrows show routing decisions

2. **Flow of Data Between Indexes and Agents**
   - Agents query their respective indexes (solid arrows)
   - Indexes return retrieved chunks (dashed arrows)
   - Summary Index ↔ Summarization Agent (green)
   - Hierarchical Index ↔ Needle Agent (red)

3. **MCP Integration Point**
   - Both agents can call ClaimTimelineAnalyticsTool (purple)
   - Tool provides timeline analytics (time_diff, sla_check, stats)
   - Results flow back to agents (dashed purple arrows)

## Color Coding

- **Blue**: Manager Router Agent
- **Green**: Summarization Expert Agent
- **Red**: Needle-in-a-Haystack Agent
- **Yellow**: Indexes (Summary & Hierarchical)
- **Purple**: MCP Tool (ClaimTimelineAnalyticsTool)
- **Gray**: Data flow arrows

## Submission

For submission, export as:
- **PNG**: 300 DPI, minimum 1600x1200 pixels
- **JPEG**: High quality (90%+), minimum 1600x1200 pixels


