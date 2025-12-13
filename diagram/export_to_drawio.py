"""
Export Agent System Diagram to Draw.io XML Format
Includes query expansion, fallback mechanism, and improved retrieval parameters
"""

from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom


def create_drawio_xml():
    """Create draw.io XML file with the updated agent system diagram"""

    # Create root element
    mxfile = ET.Element(
        "mxfile",
        {
            "host": "app.diagrams.net",
            "modified": datetime.now().isoformat() + "Z",
            "agent": "5.0",
            "version": "21.0.0",
            "etag": "diagram",
            "type": "device",
        },
    )

    diagram = ET.SubElement(
        mxfile, "diagram", {"name": "Multi-Agent System", "id": "multi-agent-diagram"}
    )

    mxGraphModel = ET.SubElement(
        diagram,
        "mxGraphModel",
        {
            "dx": "1800",
            "dy": "1000",
            "grid": "1",
            "gridSize": "10",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "1",
            "pageScale": "1",
            "pageWidth": "1800",
            "pageHeight": "1300",
            "math": "0",
            "shadow": "0",
        },
    )

    root = ET.SubElement(mxGraphModel, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})

    # Helper function to create cells
    def create_cell(cell_id, value, x, y, width, height, style, parent="1"):
        cell = ET.SubElement(
            root,
            "mxCell",
            {
                "id": cell_id,
                "value": value,
                "style": style,
                "vertex": "1",
                "parent": parent,
            },
        )
        ET.SubElement(
            cell,
            "mxGeometry",
            {
                "x": str(x),
                "y": str(y),
                "width": str(width),
                "height": str(height),
                "as": "geometry",
            },
        )
        return cell

    def create_edge(edge_id, source, target, style, label="", parent="1"):
        edge = ET.SubElement(
            root,
            "mxCell",
            {
                "id": edge_id,
                "value": label,
                "style": style,
                "edge": "1",
                "parent": parent,
            },
        )
        geometry = ET.SubElement(
            edge,
            "mxGeometry",
            {"width": "50", "height": "50", "relative": "1", "as": "geometry"},
        )
        ET.SubElement(geometry, "mxPoint", {"x": "0", "y": "0", "as": "sourcePoint"})
        ET.SubElement(geometry, "mxPoint", {"x": "0", "y": "0", "as": "targetPoint"})
        edge.set("source", source)
        edge.set("target", target)
        return edge

    # User Query
    create_cell(
        "user",
        "User Query",
        700,
        40,
        200,
        60,
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#000000;fontStyle=1;fontSize=14;",
    )

    # Manager Router Agent
    create_cell(
        "manager",
        "Manager Router Agent",
        700,
        160,
        200,
        80,
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#4A90E2;strokeColor=#000000;fontStyle=1;fontSize=12;fontColor=#ffffff;",
    )

    # Summary Index
    create_cell(
        "summary_index",
        "Summary Index\n\n(Large Chunks)\ntop_k=15",
        80,
        500,
        200,
        120,
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFD93D;strokeColor=#000000;fontStyle=1;fontSize=11;",
    )

    # Hierarchical Index
    create_cell(
        "hierarchical_index",
        "Hierarchical Index\n\n(Multi-size Chunks)\ntop_k=20",
        80,
        700,
        200,
        120,
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFD93D;strokeColor=#000000;fontStyle=1;fontSize=11;",
    )

    # Summarization Expert Agent
    create_cell(
        "summarization_agent",
        "Summarization\nExpert Agent\n\ntree_summarize",
        1520,
        500,
        200,
        120,
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#50C878;strokeColor=#000000;fontStyle=1;fontSize=11;fontColor=#000000;",
    )

    # Needle-in-a-Haystack Agent
    create_cell(
        "needle_agent",
        "Needle-in-a-\nHaystack Agent\n\ncompact + expansion",
        1520,
        700,
        200,
        120,
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#FF6B6B;strokeColor=#000000;fontStyle=1;fontSize=11;fontColor=#000000;",
    )

    # Query Expansion Box
    create_cell(
        "expansion",
        "Query Expansion\n\nSynonyms + Variations",
        1000,
        650,
        180,
        70,
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFA500;strokeColor=#000000;fontStyle=1;fontSize=9;alpha=0.7;",
    )

    # Fallback Box
    create_cell(
        "fallback",
        "Fallback Retry\n\nIf incomplete",
        1000,
        750,
        180,
        70,
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFA500;strokeColor=#000000;fontStyle=1;fontSize=9;alpha=0.7;",
    )

    # MCP Tool
    create_cell(
        "mcp_tool",
        "ClaimTimelineAnalyticsTool (MCP)\n\ntime_diff | sla_check |\ntimeline_summary_stats |\nevents_in_range",
        600,
        1000,
        400,
        140,
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#9B59B6;strokeColor=#000000;fontStyle=1;fontSize=11;fontColor=#ffffff;",
    )

    # Enhanced Features Note
    create_cell(
        "enhanced",
        "Enhanced Features:\n• Query Expansion\n• Fallback Retry",
        80,
        1000,
        200,
        80,
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F5E9;strokeColor=#4CAF50;fontStyle=1;fontSize=8;fontColor=#2E7D32;",
    )

    # Arrows: User → Manager
    create_edge(
        "arrow1",
        "user",
        "manager",
        "endArrow=classic;html=1;strokeWidth=2;strokeColor=#34495E;",
        "Query",
    )

    # Arrows: Manager → Agents
    create_edge(
        "arrow2",
        "manager",
        "summarization_agent",
        "endArrow=classic;html=1;strokeWidth=2;strokeColor=#50C878;",
        "HIGH_LEVEL",
    )

    create_edge(
        "arrow3",
        "manager",
        "needle_agent",
        "endArrow=classic;html=1;strokeWidth=2;strokeColor=#FF6B6B;",
        "PRECISE",
    )

    # Arrows: Manager → Indexes (selection)
    create_edge(
        "arrow4",
        "manager",
        "summary_index",
        "endArrow=classic;html=1;strokeWidth=2;strokeColor=#34495E;strokeDashArray=5 5;dashed=1;",
        "Select",
    )

    create_edge(
        "arrow5",
        "manager",
        "hierarchical_index",
        "endArrow=classic;html=1;strokeWidth=2;strokeColor=#34495E;strokeDashArray=5 5;dashed=1;",
        "Select",
    )

    # Arrows: Agents → Indexes
    create_edge(
        "arrow6",
        "summarization_agent",
        "summary_index",
        "endArrow=classic;html=1;strokeWidth=2;strokeColor=#50C878;",
        "Query",
    )

    create_edge(
        "arrow7",
        "needle_agent",
        "hierarchical_index",
        "endArrow=classic;html=1;strokeWidth=2;strokeColor=#FF6B6B;",
        "Query",
    )

    # Arrows: Indexes → Agents (response)
    create_edge(
        "arrow8",
        "summary_index",
        "summarization_agent",
        "endArrow=classic;html=1;strokeWidth=2;strokeColor=#50C878;strokeDashArray=2 2;dashed=1;",
        "15 Chunks",
    )

    create_edge(
        "arrow9",
        "hierarchical_index",
        "needle_agent",
        "endArrow=classic;html=1;strokeWidth=2;strokeColor=#FF6B6B;strokeDashArray=2 2;dashed=1;",
        "20 Chunks",
    )

    # Arrow: Needle Agent → Query Expansion
    create_edge(
        "arrow_expand",
        "needle_agent",
        "expansion",
        "endArrow=classic;html=1;strokeWidth=1.5;strokeColor=#FFA500;",
        "Expand",
    )

    # Arrow: Query Expansion → Hierarchical Index (retry)
    create_edge(
        "arrow_retry",
        "expansion",
        "hierarchical_index",
        "endArrow=classic;html=1;strokeWidth=1.5;strokeColor=#FFA500;strokeDashArray=5 5;dashed=1;",
        "Retry with Expanded Query",
    )

    # Arrow: Fallback → Needle Agent
    create_edge(
        "arrow_fallback",
        "fallback",
        "needle_agent",
        "endArrow=classic;html=1;strokeWidth=1.5;strokeColor=#FFA500;strokeDashArray=2 2;dashed=1;",
        "Fallback",
    )

    # Arrows: Agents → MCP Tool
    create_edge(
        "arrow10",
        "summarization_agent",
        "mcp_tool",
        "endArrow=classic;html=1;strokeWidth=2;strokeColor=#9B59B6;",
        "Timeline Query",
    )

    create_edge(
        "arrow11",
        "needle_agent",
        "mcp_tool",
        "endArrow=classic;html=1;strokeWidth=2;strokeColor=#9B59B6;",
        "",
    )

    # Arrows: MCP Tool → Agents (results)
    create_edge(
        "arrow12",
        "mcp_tool",
        "summarization_agent",
        "endArrow=classic;html=1;strokeWidth=2;strokeColor=#9B59B6;strokeDashArray=2 2;dashed=1;",
        "Analytics Results",
    )

    create_edge(
        "arrow13",
        "mcp_tool",
        "needle_agent",
        "endArrow=classic;html=1;strokeWidth=2;strokeColor=#9B59B6;strokeDashArray=2 2;dashed=1;",
        "",
    )

    # Arrows: Agents → User (final answer)
    create_edge(
        "arrow14",
        "summarization_agent",
        "user",
        "endArrow=classic;html=1;strokeWidth=2;strokeColor=#34495E;",
        "Answer",
    )

    create_edge(
        "arrow15",
        "needle_agent",
        "user",
        "endArrow=classic;html=1;strokeWidth=2;strokeColor=#34495E;",
        "Answer",
    )

    # Title
    create_cell(
        "title",
        "Multi-Agent System with MCP Integration\nEnhanced with Query Expansion & Fallback Mechanism",
        900,
        10,
        600,
        30,
        "text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=16;fontStyle=1;",
    )

    # Convert to pretty XML string
    rough_string = ET.tostring(mxfile, encoding="unicode")
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")

    # Remove extra blank lines
    lines = [line for line in pretty_xml.split("\n") if line.strip()]
    return "\n".join(lines)


if __name__ == "__main__":
    xml_content = create_drawio_xml()

    # Write to file
    with open("agent_diagram.drawio", "w", encoding="utf-8") as f:
        f.write(xml_content)

    print("✓ Draw.io file saved as 'agent_diagram.drawio'")
    print("  The diagram includes:")
    print("  - Manager → Sub-agent routing (HIGH_LEVEL vs PRECISE)")
    print("  - Flow of data between indexes and agents")
    print("  - MCP integration point (ClaimTimelineAnalyticsTool)")
    print("  - Query expansion and fallback mechanism for Needle Agent")
    print(
        "  - Updated retrieval parameters (top_k=15 for Summary, top_k=20 for Hierarchical)"
    )
