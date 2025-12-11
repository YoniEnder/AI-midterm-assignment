"""
Generate Agent System Diagram
Shows Manager → Sub-agent routing, data flow, and MCP integration
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, ConnectionPatch
import matplotlib.patches as mpatches

# Create figure
fig, ax = plt.subplots(1, 1, figsize=(16, 12))
ax.set_xlim(0, 16)
ax.set_ylim(0, 12)
ax.axis('off')

# Define colors
color_manager = '#4A90E2'  # Blue
color_summarization = '#50C878'  # Green
color_needle = '#FF6B6B'  # Red
color_index = '#FFD93D'  # Yellow
color_mcp = '#9B59B6'  # Purple
color_data = '#34495E'  # Dark gray
color_user = '#E74C3C'  # Red

# Define box styles
box_style = dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='black', linewidth=2)
index_style = dict(boxstyle='round,pad=0.5', facecolor=color_index, edgecolor='black', linewidth=2, alpha=0.8)
agent_style = dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='black', linewidth=2)
mcp_style = dict(boxstyle='round,pad=0.5', facecolor=color_mcp, edgecolor='black', linewidth=2, alpha=0.9)

# User Query
user_box = FancyBboxPatch((6.5, 10.5), 3, 1, **box_style)
ax.add_patch(user_box)
ax.text(8, 11, 'User Query', ha='center', va='center', fontsize=14, weight='bold')

# Manager Router Agent
manager_box = FancyBboxPatch((6.5, 8.5), 3, 1, **agent_style)
ax.add_patch(manager_box)
ax.text(8, 9, 'Manager Router Agent', ha='center', va='center', fontsize=12, weight='bold', color=color_manager)

# Indexes (left side)
summary_index_box = FancyBboxPatch((1, 5), 2.5, 1.5, **index_style)
ax.add_patch(summary_index_box)
ax.text(2.25, 6, 'Summary Index', ha='center', va='center', fontsize=11, weight='bold')
ax.text(2.25, 5.5, '(Large Chunks)', ha='center', va='center', fontsize=9)

hierarchical_index_box = FancyBboxPatch((1, 2.5), 2.5, 1.5, **index_style)
ax.add_patch(hierarchical_index_box)
ax.text(2.25, 3.5, 'Hierarchical Index', ha='center', va='center', fontsize=11, weight='bold')
ax.text(2.25, 3, '(Multi-size Chunks)', ha='center', va='center', fontsize=9)

# Agents (right side)
summarization_box = FancyBboxPatch((12.5, 5), 3, 1.5, **agent_style)
ax.add_patch(summarization_box)
ax.text(14, 6, 'Summarization', ha='center', va='center', fontsize=11, weight='bold', color=color_summarization)
ax.text(14, 5.5, 'Expert Agent', ha='center', va='center', fontsize=11, weight='bold', color=color_summarization)

needle_box = FancyBboxPatch((12.5, 2.5), 3, 1.5, **agent_style)
ax.add_patch(needle_box)
ax.text(14, 3.5, 'Needle-in-a-', ha='center', va='center', fontsize=11, weight='bold', color=color_needle)
ax.text(14, 3, 'Haystack Agent', ha='center', va='center', fontsize=11, weight='bold', color=color_needle)

# MCP Tool
mcp_box = FancyBboxPatch((5.5, 0.5), 5, 1, **mcp_style)
ax.add_patch(mcp_box)
ax.text(8, 1, 'ClaimTimelineAnalyticsTool (MCP)', ha='center', va='center', fontsize=12, weight='bold', color='white')
ax.text(8, 0.7, 'time_diff | sla_check | timeline_summary_stats', ha='center', va='center', fontsize=9, color='white')

# Arrows: User → Manager
arrow1 = FancyArrowPatch((8, 10.5), (8, 9.5), 
                        arrowstyle='->', lw=2, color=color_data, mutation_scale=20)
ax.add_patch(arrow1)
ax.text(8.5, 10, 'Query', ha='left', va='center', fontsize=9, color=color_data)

# Arrows: Manager → Agents (routing decision)
arrow2 = FancyArrowPatch((9.5, 9), (12.5, 6.5), 
                        arrowstyle='->', lw=2, color=color_summarization, mutation_scale=20)
ax.add_patch(arrow2)
ax.text(11, 7.5, 'HIGH_LEVEL', ha='center', va='center', fontsize=9, 
        bbox=dict(boxstyle='round,pad=0.3', facecolor=color_summarization, alpha=0.3))

arrow3 = FancyArrowPatch((9.5, 9), (12.5, 3.5), 
                        arrowstyle='->', lw=2, color=color_needle, mutation_scale=20)
ax.add_patch(arrow3)
ax.text(11, 6, 'PRECISE', ha='center', va='center', fontsize=9,
        bbox=dict(boxstyle='round,pad=0.3', facecolor=color_needle, alpha=0.3))

# Arrows: Manager → Indexes (for routing decision)
arrow4 = FancyArrowPatch((6.5, 9), (3.5, 6.5), 
                        arrowstyle='->', lw=2, color=color_data, linestyle='--', mutation_scale=15)
ax.add_patch(arrow4)
ax.text(5, 7.5, 'Select', ha='center', va='center', fontsize=8, style='italic')

arrow5 = FancyArrowPatch((6.5, 9), (3.5, 3.5), 
                        arrowstyle='->', lw=2, color=color_data, linestyle='--', mutation_scale=15)
ax.add_patch(arrow5)
ax.text(5, 6, 'Select', ha='center', va='center', fontsize=8, style='italic')

# Arrows: Agents → Indexes (query)
arrow6 = FancyArrowPatch((12.5, 5.75), (3.5, 6), 
                        arrowstyle='->', lw=2, color=color_summarization, mutation_scale=20)
ax.add_patch(arrow6)
ax.text(8, 6.5, 'Query', ha='center', va='center', fontsize=9, color=color_summarization)

arrow7 = FancyArrowPatch((12.5, 3.25), (3.5, 3.5), 
                        arrowstyle='->', lw=2, color=color_needle, mutation_scale=20)
ax.add_patch(arrow7)
ax.text(8, 3.5, 'Query', ha='center', va='center', fontsize=9, color=color_needle)

# Arrows: Indexes → Agents (response)
arrow8 = FancyArrowPatch((3.5, 5.5), (12.5, 5.5), 
                        arrowstyle='->', lw=2, color=color_summarization, linestyle=':', mutation_scale=15)
ax.add_patch(arrow8)
ax.text(8, 5.2, 'Retrieved Chunks', ha='center', va='center', fontsize=8, style='italic', color=color_summarization)

arrow9 = FancyArrowPatch((3.5, 3), (12.5, 3), 
                        arrowstyle='->', lw=2, color=color_needle, linestyle=':', mutation_scale=15)
ax.add_patch(arrow9)
ax.text(8, 2.7, 'Retrieved Chunks', ha='center', va='center', fontsize=8, style='italic', color=color_needle)

# Arrows: Agents → MCP Tool
arrow10 = FancyArrowPatch((12.5, 4.5), (10.5, 1.5), 
                         arrowstyle='->', lw=2, color=color_mcp, mutation_scale=20)
ax.add_patch(arrow10)
ax.text(11.5, 2.8, 'Timeline Query', ha='center', va='center', fontsize=9, 
        bbox=dict(boxstyle='round,pad=0.3', facecolor=color_mcp, alpha=0.3), color='white')

arrow11 = FancyArrowPatch((12.5, 3.5), (10.5, 1.5), 
                         arrowstyle='->', lw=2, color=color_mcp, mutation_scale=20)
ax.add_patch(arrow11)

# Arrow: MCP Tool → Agents (results)
arrow12 = FancyArrowPatch((5.5, 1.5), (12.5, 4.5), 
                         arrowstyle='->', lw=2, color=color_mcp, linestyle=':', mutation_scale=15)
ax.add_patch(arrow12)
ax.text(9, 3.2, 'Analytics Results', ha='center', va='center', fontsize=8, style='italic', color=color_mcp)

arrow13 = FancyArrowPatch((5.5, 1.5), (12.5, 3.5), 
                         arrowstyle='->', lw=2, color=color_mcp, linestyle=':', mutation_scale=15)
ax.add_patch(arrow13)

# Arrow: Agents → User (final answer)
arrow14 = FancyArrowPatch((14, 5.5), (8, 10.5), 
                         arrowstyle='->', lw=2, color=color_data, mutation_scale=20)
ax.add_patch(arrow14)
ax.text(11, 8, 'Answer', ha='center', va='center', fontsize=9, color=color_data)

arrow15 = FancyArrowPatch((14, 3), (8, 10.5), 
                         arrowstyle='->', lw=2, color=color_data, mutation_scale=20)
ax.add_patch(arrow15)

# Add legend
legend_elements = [
    mpatches.Patch(facecolor=color_manager, label='Manager Router', edgecolor='black'),
    mpatches.Patch(facecolor=color_summarization, label='Summarization Agent', edgecolor='black'),
    mpatches.Patch(facecolor=color_needle, label='Needle Agent', edgecolor='black'),
    mpatches.Patch(facecolor=color_index, label='Indexes', edgecolor='black', alpha=0.8),
    mpatches.Patch(facecolor=color_mcp, label='MCP Tool', edgecolor='black', alpha=0.9),
]
ax.legend(handles=legend_elements, loc='upper right', fontsize=10, framealpha=0.9)

# Add title
ax.text(8, 11.8, 'Multi-Agent System with MCP Integration', ha='center', va='center', 
        fontsize=16, weight='bold')

# Add flow labels
ax.text(0.5, 6, 'Data Storage', ha='left', va='center', fontsize=10, weight='bold', rotation=90)
ax.text(15.5, 4, 'Agents', ha='right', va='center', fontsize=10, weight='bold', rotation=90)

# Save
plt.tight_layout()
plt.savefig('agent_diagram.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.savefig('agent_diagram.jpg', dpi=300, bbox_inches='tight', facecolor='white')
print("✓ Diagram saved as 'agent_diagram.png' and 'agent_diagram.jpg'")
print("  The diagram shows:")
print("  - Manager → Sub-agent routing (HIGH_LEVEL vs PRECISE)")
print("  - Flow of data between indexes and agents")
print("  - MCP integration point (ClaimTimelineAnalyticsTool)")


