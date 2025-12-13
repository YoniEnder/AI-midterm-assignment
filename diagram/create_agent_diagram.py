"""
Generate Agent System Diagram
Shows Manager → Sub-agent routing, data flow, and MCP integration
Updated with query expansion, fallback mechanism, and improved retrieval
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, ConnectionPatch
import matplotlib.patches as mpatches

# Create figure
fig, ax = plt.subplots(1, 1, figsize=(18, 13))
ax.set_xlim(0, 18)
ax.set_ylim(0, 13)
ax.axis("off")

# Define colors
color_manager = "#4A90E2"  # Blue
color_summarization = "#50C878"  # Green
color_needle = "#FF6B6B"  # Red
color_index = "#FFD93D"  # Yellow
color_mcp = "#9B59B6"  # Purple
color_data = "#34495E"  # Dark gray
color_user = "#E74C3C"  # Red
color_expansion = "#FFA500"  # Orange

# Define box styles
box_style = dict(
    boxstyle="round,pad=0.5", facecolor="white", edgecolor="black", linewidth=2
)
index_style = dict(
    boxstyle="round,pad=0.5",
    facecolor=color_index,
    edgecolor="black",
    linewidth=2,
    alpha=0.8,
)
agent_style = dict(
    boxstyle="round,pad=0.5", facecolor="white", edgecolor="black", linewidth=2
)
mcp_style = dict(
    boxstyle="round,pad=0.5",
    facecolor=color_mcp,
    edgecolor="black",
    linewidth=2,
    alpha=0.9,
)
expansion_style = dict(
    boxstyle="round,pad=0.4",
    facecolor=color_expansion,
    edgecolor="black",
    linewidth=1.5,
    alpha=0.7,
)

# User Query
user_box = FancyBboxPatch((7, 11.5), 4, 1, **box_style)
ax.add_patch(user_box)
ax.text(9, 12, "User Query", ha="center", va="center", fontsize=14, weight="bold")

# Manager Router Agent
manager_box = FancyBboxPatch((7, 9.5), 4, 1, **agent_style)
ax.add_patch(manager_box)
ax.text(
    9,
    10,
    "Manager Router Agent",
    ha="center",
    va="center",
    fontsize=12,
    weight="bold",
    color=color_manager,
)

# Indexes (left side)
summary_index_box = FancyBboxPatch((1, 6), 3, 1.5, **index_style)
ax.add_patch(summary_index_box)
ax.text(2.5, 7, "Summary Index", ha="center", va="center", fontsize=11, weight="bold")
ax.text(2.5, 6.5, "(Large Chunks)", ha="center", va="center", fontsize=9)
ax.text(2.5, 6.2, "top_k=15", ha="center", va="center", fontsize=8, style="italic")

hierarchical_index_box = FancyBboxPatch((1, 3.5), 3, 1.5, **index_style)
ax.add_patch(hierarchical_index_box)
ax.text(
    2.5, 4.5, "Hierarchical Index", ha="center", va="center", fontsize=11, weight="bold"
)
ax.text(2.5, 4, "(Multi-size Chunks)", ha="center", va="center", fontsize=9)
ax.text(2.5, 3.7, "top_k=20", ha="center", va="center", fontsize=8, style="italic")

# Agents (right side)
summarization_box = FancyBboxPatch((13.5, 6), 3.5, 1.5, **agent_style)
ax.add_patch(summarization_box)
ax.text(
    15.25,
    7,
    "Summarization",
    ha="center",
    va="center",
    fontsize=11,
    weight="bold",
    color=color_summarization,
)
ax.text(
    15.25,
    6.5,
    "Expert Agent",
    ha="center",
    va="center",
    fontsize=11,
    weight="bold",
    color=color_summarization,
)
ax.text(
    15.25, 6.2, "tree_summarize", ha="center", va="center", fontsize=8, style="italic"
)

needle_box = FancyBboxPatch((13.5, 3.5), 3.5, 1.5, **agent_style)
ax.add_patch(needle_box)
ax.text(
    15.25,
    4.5,
    "Needle-in-a-",
    ha="center",
    va="center",
    fontsize=11,
    weight="bold",
    color=color_needle,
)
ax.text(
    15.25,
    4,
    "Haystack Agent",
    ha="center",
    va="center",
    fontsize=11,
    weight="bold",
    color=color_needle,
)
ax.text(
    15.25,
    3.7,
    "compact + expansion",
    ha="center",
    va="center",
    fontsize=8,
    style="italic",
)

# Query Expansion Box (for Needle Agent)
expansion_box = FancyBboxPatch((10, 2.5), 2.5, 0.8, **expansion_style)
ax.add_patch(expansion_box)
ax.text(
    11.25, 2.9, "Query Expansion", ha="center", va="center", fontsize=9, weight="bold"
)
ax.text(11.25, 2.6, "Synonyms + Variations", ha="center", va="center", fontsize=7)

# Fallback Box (for Needle Agent)
fallback_box = FancyBboxPatch((10, 1.5), 2.5, 0.8, **expansion_style)
ax.add_patch(fallback_box)
ax.text(
    11.25, 1.9, "Fallback Retry", ha="center", va="center", fontsize=9, weight="bold"
)
ax.text(11.25, 1.6, "If incomplete", ha="center", va="center", fontsize=7)

# MCP Tool
mcp_box = FancyBboxPatch((5.5, 0.5), 7, 1, **mcp_style)
ax.add_patch(mcp_box)
ax.text(
    9,
    1,
    "ClaimTimelineAnalyticsTool (MCP)",
    ha="center",
    va="center",
    fontsize=12,
    weight="bold",
    color="white",
)
ax.text(
    9,
    0.7,
    "time_diff | sla_check | timeline_summary_stats | events_in_range",
    ha="center",
    va="center",
    fontsize=9,
    color="white",
)

# Arrows: User → Manager
arrow1 = FancyArrowPatch(
    (9, 11.5), (9, 10.5), arrowstyle="->", lw=2, color=color_data, mutation_scale=20
)
ax.add_patch(arrow1)
ax.text(9.5, 11, "Query", ha="left", va="center", fontsize=9, color=color_data)

# Arrows: Manager → Agents (routing decision)
arrow2 = FancyArrowPatch(
    (11, 10),
    (13.5, 7.5),
    arrowstyle="->",
    lw=2,
    color=color_summarization,
    mutation_scale=20,
)
ax.add_patch(arrow2)
ax.text(
    12,
    8.5,
    "HIGH_LEVEL",
    ha="center",
    va="center",
    fontsize=9,
    bbox=dict(boxstyle="round,pad=0.3", facecolor=color_summarization, alpha=0.3),
)

arrow3 = FancyArrowPatch(
    (11, 10), (13.5, 5), arrowstyle="->", lw=2, color=color_needle, mutation_scale=20
)
ax.add_patch(arrow3)
ax.text(
    12,
    7,
    "PRECISE",
    ha="center",
    va="center",
    fontsize=9,
    bbox=dict(boxstyle="round,pad=0.3", facecolor=color_needle, alpha=0.3),
)

# Arrows: Manager → Indexes (for routing decision)
arrow4 = FancyArrowPatch(
    (7, 10),
    (4, 7.5),
    arrowstyle="->",
    lw=2,
    color=color_data,
    linestyle="--",
    mutation_scale=15,
)
ax.add_patch(arrow4)
ax.text(5.5, 8.5, "Select", ha="center", va="center", fontsize=8, style="italic")

arrow5 = FancyArrowPatch(
    (7, 10),
    (4, 5),
    arrowstyle="->",
    lw=2,
    color=color_data,
    linestyle="--",
    mutation_scale=15,
)
ax.add_patch(arrow5)
ax.text(5.5, 7, "Select", ha="center", va="center", fontsize=8, style="italic")

# Arrows: Agents → Indexes (query)
arrow6 = FancyArrowPatch(
    (13.5, 6.75),
    (4, 7),
    arrowstyle="->",
    lw=2,
    color=color_summarization,
    mutation_scale=20,
)
ax.add_patch(arrow6)
ax.text(
    8.5, 7.2, "Query", ha="center", va="center", fontsize=9, color=color_summarization
)

arrow7 = FancyArrowPatch(
    (13.5, 4.25), (4, 5), arrowstyle="->", lw=2, color=color_needle, mutation_scale=20
)
ax.add_patch(arrow7)
ax.text(8.5, 4.5, "Query", ha="center", va="center", fontsize=9, color=color_needle)

# Arrows: Indexes → Agents (response)
arrow8 = FancyArrowPatch(
    (4, 6.5),
    (13.5, 6.5),
    arrowstyle="->",
    lw=2,
    color=color_summarization,
    linestyle=":",
    mutation_scale=15,
)
ax.add_patch(arrow8)
ax.text(
    8.5,
    6.2,
    "15 Chunks",
    ha="center",
    va="center",
    fontsize=8,
    style="italic",
    color=color_summarization,
)

arrow9 = FancyArrowPatch(
    (4, 4),
    (13.5, 4),
    arrowstyle="->",
    lw=2,
    color=color_needle,
    linestyle=":",
    mutation_scale=15,
)
ax.add_patch(arrow9)
ax.text(
    8.5,
    3.7,
    "20 Chunks",
    ha="center",
    va="center",
    fontsize=8,
    style="italic",
    color=color_needle,
)

# Arrow: Needle Agent → Query Expansion
arrow_expand = FancyArrowPatch(
    (13.5, 3.8),
    (12.5, 3.3),
    arrowstyle="->",
    lw=1.5,
    color=color_expansion,
    mutation_scale=15,
)
ax.add_patch(arrow_expand)
ax.text(13, 3.5, "Expand", ha="center", va="center", fontsize=7, color=color_expansion)

# Arrow: Query Expansion → Hierarchical Index (retry)
arrow_retry = FancyArrowPatch(
    (10, 2.9),
    (4, 4.5),
    arrowstyle="->",
    lw=1.5,
    color=color_expansion,
    linestyle="--",
    mutation_scale=12,
)
ax.add_patch(arrow_retry)
ax.text(
    7,
    3.5,
    "Retry with",
    ha="center",
    va="center",
    fontsize=7,
    style="italic",
    color=color_expansion,
)
ax.text(
    7,
    3.2,
    "Expanded Query",
    ha="center",
    va="center",
    fontsize=7,
    style="italic",
    color=color_expansion,
)

# Arrow: Fallback → Needle Agent (if incomplete)
arrow_fallback = FancyArrowPatch(
    (12.5, 1.9),
    (13.5, 3.8),
    arrowstyle="->",
    lw=1.5,
    color=color_expansion,
    linestyle=":",
    mutation_scale=12,
)
ax.add_patch(arrow_fallback)
ax.text(
    13,
    2.8,
    "Fallback",
    ha="center",
    va="center",
    fontsize=7,
    style="italic",
    color=color_expansion,
)

# Arrows: Agents → MCP Tool
arrow10 = FancyArrowPatch(
    (13.5, 5.5), (11.5, 1.5), arrowstyle="->", lw=2, color=color_mcp, mutation_scale=20
)
ax.add_patch(arrow10)
ax.text(
    12.5,
    3.2,
    "Timeline Query",
    ha="center",
    va="center",
    fontsize=9,
    bbox=dict(boxstyle="round,pad=0.3", facecolor=color_mcp, alpha=0.3),
    color="white",
)

arrow11 = FancyArrowPatch(
    (13.5, 4.5), (11.5, 1.5), arrowstyle="->", lw=2, color=color_mcp, mutation_scale=20
)
ax.add_patch(arrow11)

# Arrow: MCP Tool → Agents (results)
arrow12 = FancyArrowPatch(
    (5.5, 1.5),
    (13.5, 5.5),
    arrowstyle="->",
    lw=2,
    color=color_mcp,
    linestyle=":",
    mutation_scale=15,
)
ax.add_patch(arrow12)
ax.text(
    9.5,
    3.8,
    "Analytics Results",
    ha="center",
    va="center",
    fontsize=8,
    style="italic",
    color=color_mcp,
)

arrow13 = FancyArrowPatch(
    (5.5, 1.5),
    (13.5, 4.5),
    arrowstyle="->",
    lw=2,
    color=color_mcp,
    linestyle=":",
    mutation_scale=15,
)
ax.add_patch(arrow13)

# Arrow: Agents → User (final answer)
arrow14 = FancyArrowPatch(
    (15.25, 6.5), (9, 11.5), arrowstyle="->", lw=2, color=color_data, mutation_scale=20
)
ax.add_patch(arrow14)
ax.text(12, 9, "Answer", ha="center", va="center", fontsize=9, color=color_data)

arrow15 = FancyArrowPatch(
    (15.25, 4), (9, 11.5), arrowstyle="->", lw=2, color=color_data, mutation_scale=20
)
ax.add_patch(arrow15)

# Add enhanced features note
enhanced_box = FancyBboxPatch(
    (1, 0.5),
    3.5,
    0.8,
    boxstyle="round,pad=0.3",
    facecolor="#E8F5E9",
    edgecolor="#4CAF50",
    linewidth=1.5,
)
ax.add_patch(enhanced_box)
ax.text(
    2.75,
    0.9,
    "Enhanced Features:",
    ha="center",
    va="center",
    fontsize=8,
    weight="bold",
    color="#2E7D32",
)
ax.text(
    2.75,
    0.65,
    "• Query Expansion",
    ha="center",
    va="center",
    fontsize=7,
    color="#2E7D32",
)
ax.text(
    2.75, 0.5, "• Fallback Retry", ha="center", va="center", fontsize=7, color="#2E7D32"
)

# Add legend
legend_elements = [
    mpatches.Patch(facecolor=color_manager, label="Manager Router", edgecolor="black"),
    mpatches.Patch(
        facecolor=color_summarization, label="Summarization Agent", edgecolor="black"
    ),
    mpatches.Patch(facecolor=color_needle, label="Needle Agent", edgecolor="black"),
    mpatches.Patch(
        facecolor=color_index, label="Indexes", edgecolor="black", alpha=0.8
    ),
    mpatches.Patch(facecolor=color_mcp, label="MCP Tool", edgecolor="black", alpha=0.9),
    mpatches.Patch(
        facecolor=color_expansion, label="Query Expansion", edgecolor="black", alpha=0.7
    ),
]
ax.legend(handles=legend_elements, loc="upper right", fontsize=10, framealpha=0.9)

# Add title
ax.text(
    9,
    12.8,
    "Multi-Agent System with MCP Integration",
    ha="center",
    va="center",
    fontsize=16,
    weight="bold",
)
ax.text(
    9,
    12.5,
    "Enhanced with Query Expansion & Fallback Mechanism",
    ha="center",
    va="center",
    fontsize=11,
    style="italic",
    color="#666",
)

# Add flow labels
ax.text(
    0.5,
    5,
    "Data Storage",
    ha="left",
    va="center",
    fontsize=10,
    weight="bold",
    rotation=90,
)
ax.text(
    17.5, 5, "Agents", ha="right", va="center", fontsize=10, weight="bold", rotation=90
)

# Save
plt.tight_layout()
plt.savefig("agent_diagram.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.savefig("agent_diagram.jpg", dpi=300, bbox_inches="tight", facecolor="white")
print("✓ Diagram saved as 'agent_diagram.png' and 'agent_diagram.jpg'")
print("  The diagram shows:")
print("  - Manager → Sub-agent routing (HIGH_LEVEL vs PRECISE)")
print("  - Flow of data between indexes and agents")
print("  - MCP integration point (ClaimTimelineAnalyticsTool)")
print("  - Query expansion and fallback mechanism for Needle Agent")
print(
    "  - Updated retrieval parameters (top_k=15 for Summary, top_k=20 for Hierarchical)"
)
