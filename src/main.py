"""
Main entry point for the Multi-Agent System
Demonstrates routing logic, use of indexes, and model prompts as functions
"""

import sys
from pathlib import Path

# Add parent directory to path to allow imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from src.agents import MultiAgentSystem
from src.indexing import load_or_create_indexes
from src.evaluation.evaluator import SystemEvaluator
from dotenv import load_dotenv
import os

load_dotenv()


def demonstrate_routing():
    """Demonstrate the multi-agent system with various query types"""

    print("=" * 80)
    print("Multi-Agent System Demonstration")
    print("=" * 80)
    print()

    # Load or create indexes
    print("Loading indexes...")
    summary_index, hierarchical_index = load_or_create_indexes()
    print()

    # Initialize multi-agent system
    print("Initializing Multi-Agent System...")
    system = MultiAgentSystem(summary_index, hierarchical_index)
    print("System ready!")
    print("✓ DateParserTool MCP integrated")
    print()
    print("=" * 80)
    print()

    # Test queries demonstrating different routing scenarios
    # Based on the 10 claim documents in the data folder
    test_queries = [
        # High-level queries (should route to Summarization Expert)
        "What is the overall summary of all insurance claims?",
        "Give me a timeline of key events across all claims",
        "What are the main types of insurance claims in the dataset?",
        "What are the key decisions and outcomes across all claims?",
        "Summarize the health-related claims (knee surgery and workplace injury)",
        # Date parsing queries (should use DateParserTool MCP)
        "What date was the claim filed?",
        "When was the inspection completed?",
        "Parse the date from 'January 15, 2024' and normalize it",
        # Precise queries (should route to Needle-in-a-Haystack)
        "What is the exact claim ID for the Auto Collision claim?",
        "In Claim Document 01, did the other driver acknowledge responsibility?",
        "What was the moisture reading in the earliest inspection for the Apartment Water Damage claim?",
        "What did the adjuster email say about photos in Claim Document 04 (Kitchen Fire)?",
        "Did the patient complete conservative physical therapy in Claim Document 05?",
        "What time was the luggage scanned in Claim Document 06 (Travel Delay)?",
        "What billing code error was mentioned in Claim Document 07?",
        "What structural measurement indicated pre-existing weakening in Claim Document 08?",
        "Was there evidence of misrepresentation in Claim Document 09?",
        "What caused the payment approval delay in Claim Document 10?",
        # Edge cases - testing routing logic
        "What happened overall in the auto collision claims and what are the specific claim IDs?",  # Mixed query
    ]

    # Limit to first 10 queries
    test_queries = test_queries[:10]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"Query {i}: {query}")
        print(f"{'=' * 80}")

        result = system.query(query)

        print(f"\n📊 Routing Decision: {result['route']}")
        print(f"🤖 Agent Used: {result['agent_used']}")
        print(f"📚 Index Used: {result['index_used']}")
        if result.get("date_parser_tool_used", False):
            print(f"🔧 Date Parser Tool Used: Yes (DateParserTool MCP)")
        print("\n💬 Answer:")
        print(result["answer"])
        print()


def interactive_mode():
    """Interactive mode for querying the system"""

    print("=" * 80)
    print("Interactive Multi-Agent System")
    print("=" * 80)
    print()

    # Load or create indexes
    print("Loading indexes...")
    summary_index, hierarchical_index = load_or_create_indexes()
    print()

    # Initialize multi-agent system
    print("Initializing Multi-Agent System...")
    system = MultiAgentSystem(summary_index, hierarchical_index)
    print("System ready!")
    print("✓ DateParserTool MCP integrated")
    print()

    # Initialize evaluator
    judge_model = os.getenv("JUDGE_MODEL", "gpt-4o-mini")
    print(f"Initializing Evaluator (Judge: {judge_model})...")
    evaluator = SystemEvaluator(judge_model=judge_model)
    print("✓ Evaluator initialized")
    print()

    print("=" * 80)
    print("Enter your queries (type 'exit' to quit)")
    print("Try date parsing queries like:")
    print("  - 'What date was the claim filed?'")
    print("  - 'When was the inspection completed?'")
    print("  - 'Parse and normalize the date from January 15, 2024'")
    print("=" * 80)
    print()

    while True:
        query = input("\n🔍 Your query: ").strip()

        if query.lower() in ["exit", "quit", "q"]:
            print("\nGoodbye!")
            break

        if not query:
            continue

        try:
            result = system.query(query, return_chunks=True)

            print(f"\n📊 Routing Decision: {result['route']}")
            print(f"🤖 Agent Used: {result['agent_used']}")
            print(f"📚 Index Used: {result['index_used']}")
            if result.get("date_parser_tool_used", False):
                print(f"🔧 Date Parser Tool Used: Yes (DateParserTool MCP)")

            # Display top 3 chunks with scores
            chunks = result.get("chunks", [])
            if chunks:
                # Clarify what type of chunks are being shown
                if result["route"] == "HIGH_LEVEL":
                    print("\n📄 Top 3 Most Relevant Summary Chunks:")
                    print("   Note: These are pre-computed document summaries")
                else:
                    print("\n📄 Top 3 Most Relevant Chunks:")
                print("-" * 80)
                for chunk in chunks:
                    score = chunk.get("score", 0.0)
                    rank = chunk.get("rank", 0)
                    text = chunk.get("text", "")
                    metadata = chunk.get("metadata", {})

                    print(f"\n  Rank {rank} | Relevance Score: {score:.4f}")
                    if metadata:
                        metadata_str = ", ".join(
                            [f"{k}: {v}" for k, v in list(metadata.items())[:3]]
                        )
                        if metadata_str:
                            print(f"  Metadata: {metadata_str}")
                    print(f"  Text: {text}")
                print("-" * 80)
            else:
                print("\n📄 No chunks retrieved (date parsing mode)")

            print("\n💬 Answer:")
            print(result["answer"])

            # Run evaluation
            print("\n" + "=" * 80)
            print("📊 Evaluation (LLM-as-a-Judge)")
            print("=" * 80)
            try:
                # Evaluate relevancy (doesn't require ground truth)
                expected_index = (
                    "Summary Index"
                    if result["route"] == "HIGH_LEVEL"
                    else "Hierarchical Index"
                )
                expected_context = f"Information relevant to: {query}"

                relevancy = evaluator.evaluate_relevancy(
                    query=query,
                    answer=result["answer"],
                    expected_index=expected_index,
                    actual_index=result["index_used"],
                    expected_context=expected_context,
                )

                print(f"\n✓ Relevancy Score: {relevancy.get('score', 0.0):.2f}/1.0")
                print(
                    f"  Correct Index: {'✓' if relevancy.get('correct_index', False) else '✗'}"
                )
                print(
                    f"  Relevant Context: {'✓' if relevancy.get('relevant_context', False) else '✗'}"
                )
                reasoning = relevancy.get("reasoning", "N/A")
                if len(reasoning) > 250:
                    reasoning = reasoning[:250] + "..."
                print(f"  Reasoning: {reasoning}")

            except Exception as e:
                print(f"⚠️  Evaluation error: {e}")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback

            traceback.print_exc()


def main():
    """Main function"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        demonstrate_routing()


if __name__ == "__main__":
    main()
