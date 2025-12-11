"""
Test script to verify agent implementation
Tests routing logic and agent functionality
"""

import sys
from pathlib import Path

# Add parent directory to path to allow imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from src.agents import (
    ManagerRouterAgent,
    SummarizationExpertAgent,
    NeedleInHaystackAgent,
)
from src.index_setup import load_or_create_indexes


def test_routing_logic():
    """Test the routing logic of the Manager Agent"""
    print("Testing Routing Logic...")
    print("=" * 80)

    # Load indexes
    summary_index, hierarchical_index = load_or_create_indexes()

    # Create manager agent
    manager = ManagerRouterAgent(summary_index, hierarchical_index)

    # Test queries based on actual claim documents
    test_cases = [
        # High-level queries
        ("What is the overall summary of all insurance claims?", "HIGH_LEVEL"),
        ("Give me a timeline of key events across all claims", "HIGH_LEVEL"),
        ("What are the key events in the health-related claims?", "HIGH_LEVEL"),
        ("What are the main types of insurance claims?", "HIGH_LEVEL"),
        # Precise queries
        ("What is the exact claim ID for Claim Document 01?", "PRECISE"),
        ("What was the moisture reading in Claim Document 03?", "PRECISE"),
        ("Did the driver acknowledge responsibility in Claim Document 01?", "PRECISE"),
        ("What time was the luggage scanned in Claim Document 06?", "PRECISE"),
        ("What billing code error was in Claim Document 07?", "PRECISE"),
    ]

    print("\nTesting routing decisions:\n")
    for query, expected in test_cases:
        result = manager.route_query(query)
        status = "✅" if result == expected else "❌"
        print(f"{status} Query: '{query}'")
        print(f"   Expected: {expected}, Got: {result}")
        print()

    print("=" * 80)


def test_agent_initialization():
    """Test that all agents can be initialized"""
    print("Testing Agent Initialization...")
    print("=" * 80)

    try:
        summary_index, hierarchical_index = load_or_create_indexes()

        # Test manager
        manager = ManagerRouterAgent(summary_index, hierarchical_index)
        print("✅ ManagerRouterAgent initialized")

        # Test summarization agent
        summarization_agent = SummarizationExpertAgent(summary_index)
        print("✅ SummarizationExpertAgent initialized")

        # Test needle agent
        needle_agent = NeedleInHaystackAgent(hierarchical_index)
        print("✅ NeedleInHaystackAgent initialized")

        print("\n✅ All agents initialized successfully!")

    except Exception as e:
        print(f"❌ Error initializing agents: {e}")
        raise

    print("=" * 80)


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Agent System Test Suite")
    print("=" * 80 + "\n")

    try:
        test_agent_initialization()
        print()
        test_routing_logic()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        import traceback

        traceback.print_exc()
