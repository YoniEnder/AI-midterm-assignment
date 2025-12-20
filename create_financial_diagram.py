"""
Create DrawIO diagram for 3-Block Agentic Architecture for Financial Analysis
"""

from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom

def create_financial_diagram():
    """Create DrawIO XML diagram for financial analysis architecture"""
    
    # DrawIO uses mxGraph format
    mxfile = ET.Element(
        "mxfile",
        host="app.diagrams.net",
        modified="2024-01-01T00:00:00.000Z",
        agent="draw.io",
        version="21.0.0",
    )
    
    diagram = ET.SubElement(
        mxfile,
        "diagram",
        id="financial-agentic-architecture",
        name="3-Block Agentic Architecture",
    )
    
    mxGraphModel = ET.SubElement(
        diagram,
        "mxGraphModel",
        dx="1422",
        dy="794",
        grid="1",
        gridSize="10",
        guides="1",
        tooltips="1",
        connect="1",
        arrows="1",
        fold="1",
        page="1",
        pageScale="1",
        pageWidth="1400",
        pageHeight="1000",
        math="0",
        shadow="0",
    )
    
    root = ET.SubElement(mxGraphModel, "root")
    
    # Add mxCell for root
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")
    
    # Helper function to create a cell
    def create_cell(parent, cell_id, value, x, y, width, height, style, vertex="1"):
        cell = ET.SubElement(
            parent,
            "mxCell",
            id=str(cell_id),
            value=str(value),
            style=str(style),
            vertex=vertex,
            parent="1",
        )
        geometry = ET.SubElement(
            cell,
            "mxGeometry",
            x=str(x),
            y=str(y),
            width=str(width),
            height=str(height),
        )
        geometry.set("as", "geometry")
        return cell
    
    # Helper function to create an edge
    def create_edge(parent, edge_id, source, target, style, value=""):
        edge = ET.SubElement(
            parent,
            "mxCell",
            id=str(edge_id),
            value=str(value),
            style=str(style),
            edge="1",
            parent="1",
        )
        edge.set("source", str(source))
        edge.set("target", str(target))
        geometry = ET.SubElement(edge, "mxGeometry")
        geometry.set("relative", "1")
        geometry.set("as", "geometry")
        ET.SubElement(geometry, "mxPoint").set("as", "sourcePoint")
        ET.SubElement(geometry, "mxPoint").set("as", "targetPoint")
        return edge
    
    # Positions
    center_x = 700
    top_y = 80
    orchestrator_y = 150
    agent_y = 400
    box_width = 280
    box_height = 320
    left_x = 200
    middle_x = center_x - box_width / 2
    right_x = 920
    
    # Title
    create_cell(
        root,
        10,
        "3-Block Agentic Architecture for Financial Analysis",
        center_x - 200,
        top_y,
        400,
        40,
        "text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=18;fontStyle=1",
    )
    
    # User (left of orchestrator)
    create_cell(
        root,
        20,
        "User",
        center_x - 300,
        orchestrator_y + 20,
        80,
        40,
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;fontColor=#000000;fontStyle=1",
    )
    
    # Orchestrator Agent (center top)
    orchestrator_text = """Orchestrator Agent

• Receives user financial query
• Selects primary agent
• Invokes supporting agents
• Iterative reflection loop
• Consistency & accuracy checks
• Synthesizes final response"""
    
    create_cell(
        root,
        30,
        orchestrator_text,
        middle_x,
        orchestrator_y,
        box_width,
        box_height,
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#3498db;strokeColor=#2980b9;fontColor=#ffffff;fontStyle=1;align=left;verticalAlign=top;spacingLeft=10;spacingTop=10",
    )
    
    # Financial Domain Expert Agent (FDE) - Left
    fde_text = """Financial Domain Expert Agent (FDE)

Responsibilities:
• Financial statement interpretation
• GAAP / IFRS reasoning
• Ratio & benchmark analysis
• Risk & anomaly detection

ReAct – Reason:
• Identify financial context
• Select applicable principles
• Validate internal consistency

ReAct – Act:
• Apply financial formulas
• Retrieve domain knowledge
• Generate evidence-based insights"""
    
    create_cell(
        root,
        40,
        fde_text,
        left_x,
        agent_y,
        box_width,
        box_height + 100,
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#27ae60;strokeColor=#229954;fontColor=#ffffff;fontStyle=1;align=left;verticalAlign=top;spacingLeft=10;spacingTop=10",
    )
    
    # Financial Data Science Agent (FDS) - Middle
    fds_text = """Financial Data Science Agent (FDS)

Responsibilities:
• Time-series analysis
• Statistical evaluation
• Forecasting & trend detection
• Code generation (Python / pandas)

ReAct – Reason:
• Define analysis plan
• Choose statistical methods
• Detect missing / noisy data

ReAct – Act:
• Execute calculations
• Produce tables & plots
• Validate numeric outputs"""
    
    create_cell(
        root,
        50,
        fds_text,
        middle_x,
        agent_y,
        box_width,
        box_height + 100,
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#f39c12;strokeColor=#e67e22;fontColor=#ffffff;fontStyle=1;align=left;verticalAlign=top;spacingLeft=10;spacingTop=10",
    )
    
    # Financial Strategy Advisor Agent (FSA) - Right
    fsa_text = """Financial Strategy Advisor Agent (FSA)

Responsibilities:
• Decision support
• Scenario & sensitivity analysis
• Risk-aware recommendations
• Goal-aligned insights

ReAct – Reason:
• Identify user objective
• Assess trade-offs & risks
• Test assumption validity

ReAct – Act:
• Generate recommendations
• Propose action plans
• Adapt advice to user profile"""
    
    create_cell(
        root,
        60,
        fsa_text,
        right_x,
        agent_y,
        box_width,
        box_height + 100,
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#e74c3c;strokeColor=#c0392b;fontColor=#ffffff;fontStyle=1;align=left;verticalAlign=top;spacingLeft=10;spacingTop=10",
    )
    
    # Evaluation Layer (bottom, optional)
    eval_text = """Evaluation Layer

• Accuracy vs Base LLM
• Reasoning Quality
• Code Execution Rate
• User Preference Studies"""
    
    create_cell(
        root,
        70,
        eval_text,
        center_x - 150,
        agent_y + box_height + 150,
        300,
        100,
        "rounded=1;whiteSpace=wrap;html=1;fillColor=#95a5a6;strokeColor=#7f8c8d;fontColor=#ffffff;fontStyle=1;align=left;verticalAlign=top;spacingLeft=10;spacingTop=10",
    )
    
    # Edges
    # User -> Orchestrator
    create_edge(
        root,
        100,
        20,
        30,
        "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=2;strokeColor=#34495e;endArrow=block;endFill=1;",
        "Financial Question / Analysis Request",
    )
    
    # Orchestrator -> FDE
    create_edge(
        root,
        110,
        30,
        40,
        "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=2;strokeColor=#34495e;endArrow=block;endFill=1;labelBackgroundColor=#ffffff;",
        "Request domain interpretation",
    )
    
    # Orchestrator -> FDS
    create_edge(
        root,
        120,
        30,
        50,
        "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=2;strokeColor=#34495e;endArrow=block;endFill=1;labelBackgroundColor=#ffffff;",
        "Request quantitative analysis",
    )
    
    # Orchestrator -> FSA
    create_edge(
        root,
        130,
        30,
        60,
        "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=2;strokeColor=#34495e;endArrow=block;endFill=1;labelBackgroundColor=#ffffff;",
        "Request strategic recommendation",
    )
    
    # FDE -> Orchestrator
    create_edge(
        root,
        140,
        40,
        30,
        "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=2;strokeColor=#27ae60;endArrow=block;endFill=1;labelBackgroundColor=#ffffff;",
        "Validated insights & outputs",
    )
    
    # FDS -> Orchestrator
    create_edge(
        root,
        150,
        50,
        30,
        "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=2;strokeColor=#f39c12;endArrow=block;endFill=1;labelBackgroundColor=#ffffff;",
        "Validated insights & outputs",
    )
    
    # FSA -> Orchestrator
    create_edge(
        root,
        160,
        60,
        30,
        "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=2;strokeColor=#e74c3c;endArrow=block;endFill=1;labelBackgroundColor=#ffffff;",
        "Validated insights & outputs",
    )
    
    # Reflection loop (self-connection on Orchestrator)
    # This is a curved arrow - DrawIO handles this automatically with edgeStyle
    reflection_edge = ET.SubElement(
        root,
        "mxCell",
        id="170",
        value="Reflection & Self-Correction Loop",
        style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeWidth=2;strokeColor=#3498db;endArrow=block;endFill=1;curved=1;labelBackgroundColor=#ffffff;",
        edge="1",
        parent="1",
    )
    reflection_edge.set("source", "30")
    reflection_edge.set("target", "30")
    geometry = ET.SubElement(reflection_edge, "mxGeometry")
    geometry.set("relative", "1")
    geometry.set("as", "geometry")
    ET.SubElement(geometry, "mxPoint", x="140", y="310").set("as", "sourcePoint")
    ET.SubElement(geometry, "mxPoint", x="140", y="310").set("as", "targetPoint")
    array = ET.SubElement(geometry, "Array")
    array.set("as", "points")
    ET.SubElement(array, "mxPoint", x="560", y="200")
    ET.SubElement(array, "mxPoint", x="560", y="420")
    
    # Pretty print and save
    rough_string = ET.tostring(mxfile, encoding="unicode")
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Remove the XML declaration line
    lines = pretty_xml.split("\n")
    if lines[0].startswith("<?xml"):
        lines = lines[1:]
    pretty_xml = "\n".join(lines)
    
    output_path = Path("financial_architecture.drawio")
    output_path.write_text(pretty_xml, encoding="utf-8")
    print(f"✓ Created DrawIO diagram: {output_path}")

if __name__ == "__main__":
    create_financial_diagram()



