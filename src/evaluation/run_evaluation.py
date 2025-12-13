"""
Run System Evaluation
Executes test suite and evaluates system performance using LLM-as-a-judge
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add project root directory to path
# __file__ is src/evaluation/run_evaluation.py
# parent.parent.parent gives us the project root
project_root = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(project_root))

from src.agents import MultiAgentSystem
from src.indexing import load_or_create_indexes
from src.evaluation.evaluator import SystemEvaluator
from src.evaluation.evaluation_suite import get_test_cases
from dotenv import load_dotenv

load_dotenv()


def run_evaluation():
    """Run full evaluation suite"""

    print("=" * 80)
    print("System Evaluation - LLM-as-a-Judge")
    print("=" * 80)
    print()

    # Load indexes
    print("Loading indexes...")
    summary_index, hierarchical_index = load_or_create_indexes()
    print("✓ Indexes loaded\n")

    # Initialize system
    print("Initializing Multi-Agent System...")
    system = MultiAgentSystem(summary_index, hierarchical_index)
    print("✓ System initialized\n")

    # Initialize evaluator
    import os
    judge_model = os.getenv("JUDGE_MODEL", "gpt-4o-mini")
    print(f"Initializing Evaluator (Judge: {judge_model})...")
    evaluator = SystemEvaluator(judge_model=judge_model)
    print("✓ Evaluator initialized\n")

    # Get test cases
    test_cases = get_test_cases()
    print(f"Running {len(test_cases)} test cases...\n")
    print("=" * 80)
    print()

    # Run evaluation
    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"Test Case {i}/{len(test_cases)}: {test_case.category}")
        print(f"{'=' * 80}")
        print(f"Query: {test_case.query}")
        print()

        # Run query
        try:
            system_result = system.query(test_case.query)
            answer = system_result["answer"]
            route = system_result["route"]
            index_used = system_result["index_used"]

            print(f"Route: {route}")
            print(f"Index Used: {index_used}")
            print(f"Agent: {system_result['agent_used']}")
            if system_result.get("date_parser_tool_used"):
                print("Date Parser Tool Used: Yes")
            print()
            print(
                f"Answer: {answer[:200]}..."
                if len(answer) > 200
                else f"Answer: {answer}"
            )
            print()

            # Evaluate
            print("Evaluating...")
            evaluation = evaluator.evaluate_query(
                query=test_case.query,
                answer=answer,
                route=route,
                index_used=index_used,
                ground_truth=test_case.ground_truth,
                expected_index=test_case.expected_index,
                expected_context=test_case.expected_context,
                expected_info=test_case.expected_info,
            )

            # Display results
            print("\n📊 Evaluation Results:")
            print(
                f"  Correctness: {evaluation['correctness']['score']:.2f} - {evaluation['correctness'].get('reasoning', 'N/A')[:100]}"
            )
            print(
                f"  Relevancy: {evaluation['relevancy']['score']:.2f} - {evaluation['relevancy'].get('reasoning', 'N/A')[:100]}"
            )
            print(
                f"  Recall: {evaluation['recall']['score']:.2f} - {evaluation['recall'].get('reasoning', 'N/A')[:100]}"
            )
            print(f"  Overall Score: {evaluation['overall_score']:.2f}")

            results.append(
                {
                    "test_case": {
                        "query": test_case.query,
                        "category": test_case.category,
                        "expected_route": test_case.expected_route,
                        "expected_index": test_case.expected_index,
                    },
                    "system_result": {
                        "route": route,
                        "index_used": index_used,
                        "agent_used": system_result["agent_used"],
                        "date_parser_tool_used": system_result.get(
                            "date_parser_tool_used", False
                        ),
                    },
                    "evaluation": evaluation,
                }
            )

        except Exception as e:
            print(f"❌ Error processing test case: {e}")
            results.append(
                {
                    "test_case": {
                        "query": test_case.query,
                        "category": test_case.category,
                    },
                    "error": str(e),
                }
            )

    # Calculate summary statistics
    print("\n" + "=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)
    print()

    successful_results = [r for r in results if "evaluation" in r]

    if successful_results:
        correctness_scores = [
            r["evaluation"]["correctness"]["score"] for r in successful_results
        ]
        relevancy_scores = [
            r["evaluation"]["relevancy"]["score"] for r in successful_results
        ]
        recall_scores = [r["evaluation"]["recall"]["score"] for r in successful_results]
        overall_scores = [r["evaluation"]["overall_score"] for r in successful_results]

        print(f"Total Test Cases: {len(test_cases)}")
        print(f"Successful Evaluations: {len(successful_results)}")
        print()
        print("Average Scores:")
        print(f"  Correctness: {sum(correctness_scores) / len(correctness_scores):.3f}")
        print(f"  Relevancy: {sum(relevancy_scores) / len(relevancy_scores):.3f}")
        print(f"  Recall: {sum(recall_scores) / len(recall_scores):.3f}")
        print(f"  Overall: {sum(overall_scores) / len(overall_scores):.3f}")
        print()

        # Routing accuracy
        routing_correct = sum(
            1
            for r in successful_results
            if r["system_result"]["route"] == r["test_case"]["expected_route"]
        )
        print(
            f"Routing Accuracy: {routing_correct}/{len(successful_results)} ({routing_correct/len(successful_results)*100:.1f}%)"
        )

        # Index selection accuracy
        index_correct = sum(
            1
            for r in successful_results
            if r["system_result"]["index_used"] == r["test_case"]["expected_index"]
        )
        print(
            f"Index Selection Accuracy: {index_correct}/{len(successful_results)} ({index_correct/len(successful_results)*100:.1f}%)"
        )
        print()

        # Category breakdown
        print("Scores by Category:")
        categories = {}
        for r in successful_results:
            cat = r["test_case"]["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(r["evaluation"]["overall_score"])

        for cat, scores in categories.items():
            avg = sum(scores) / len(scores)
            print(f"  {cat}: {avg:.3f} ({len(scores)} tests)")

    # Save detailed results
    results_file = Path(__file__).parent / "evaluation_results.json"
    with open(results_file, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(test_cases),
                "successful_evaluations": len(successful_results),
                "results": results,
            },
            f,
            indent=2,
        )

    print(f"\n✓ Detailed results saved to: {results_file}")

    return results


if __name__ == "__main__":
    run_evaluation()
