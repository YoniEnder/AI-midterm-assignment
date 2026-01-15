"""
Run System Evaluation
Executes test suite and evaluates system performance using LLM-as-a-judge
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Add project root directory to path
# __file__ is src/evaluation/run_evaluation.py
# parent.parent.parent gives us the project root
project_root = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

from src.agents import MultiAgentSystem
from src.evaluation.evaluation_suite import get_test_cases
from src.evaluation.evaluator import SystemEvaluator
from src.evaluation.human_grader_suite import get_human_grader_test_cases
from src.evaluation.regex_suite import get_regex_test_cases
from src.indexing import load_or_create_indexes

load_dotenv()


def _format_usage(usage: dict | None) -> str:
    if not usage:
        return "Usage: llm_total=0 (p=0 c=0) | embed_tokens=0"
    llm = usage.get("llm", {}) if isinstance(usage, dict) else {}
    emb = usage.get("embeddings", {}) if isinstance(usage, dict) else {}
    p = llm.get("prompt_tokens", 0)
    c = llm.get("completion_tokens", 0)
    t = llm.get("total_tokens", 0)
    e = emb.get("total_tokens", 0)
    return f"Usage: llm_total={t} (p={p} c={c}) | embed_tokens={e}"


def _regex_flag_names(flags: int) -> list[str]:
    names: list[str] = []
    if flags & re.IGNORECASE:
        names.append("IGNORECASE")
    if flags & re.MULTILINE:
        names.append("MULTILINE")
    if flags & re.DOTALL:
        names.append("DOTALL")
    return names


def run_regex_tests(system: MultiAgentSystem) -> dict:
    """
    Run regex-based evaluation tests and return a JSON-serializable result object.
    """
    test_cases = get_regex_test_cases()
    passed = 0
    results: list[dict] = []

    print("\n" + "=" * 80)
    print("REGEX TESTS")
    print("=" * 80)
    print(f"Running {len(test_cases)} regex tests...\n")

    for i, tc in enumerate(test_cases, 1):
        try:
            system_result = system.query(tc.query)
            target_text = (
                system_result["answer"]
                if tc.target == "answer"
                else system_result["route"]
            )
            match = re.search(tc.pattern, target_text, flags=tc.flags)
            print(f"  {_format_usage(system_result.get('usage'))}")

            enforcement_ok = True
            enforcement_errors: list[str] = []
            if (
                tc.expected_route is not None
                and system_result.get("route") != tc.expected_route
            ):
                enforcement_ok = False
                enforcement_errors.append(
                    f"route expected {tc.expected_route} got {system_result.get('route')}"
                )
            if (
                tc.expected_agent_used is not None
                and system_result.get("agent_used") != tc.expected_agent_used
            ):
                enforcement_ok = False
                enforcement_errors.append(
                    f"agent expected {tc.expected_agent_used} got {system_result.get('agent_used')}"
                )
            if getattr(
                tc, "expected_date_parser_tool_used", None
            ) is not None and system_result.get("date_parser_tool_used") != getattr(
                tc, "expected_date_parser_tool_used"
            ):
                enforcement_ok = False
                enforcement_errors.append(
                    "date_parser_tool_used expected "
                    f"{getattr(tc, 'expected_date_parser_tool_used')} got "
                    f"{system_result.get('date_parser_tool_used')}"
                )

            ok = bool(match) and enforcement_ok
            if ok:
                passed += 1

            status = "PASS" if ok else "FAIL"
            matched = match.group(0) if match else None
            print(f"[{status}] {i:02d}/{len(test_cases)} {tc.id} | {tc.category}")
            print(f"  Query: {tc.query}")
            print(f"  Target: {tc.target}")
            print(f"  Pattern: {tc.pattern}")

            def _one_line(s: str) -> str:
                return re.sub(r"\s+", " ", s).strip()

            if match is not None:
                before = 60
                after = 60
                start = match.start()
                end = match.end()
                left = max(0, start - before)
                right = min(len(target_text), end + after)
                excerpt = target_text[left:right]
                prefix = "..." if left > 0 else ""
                suffix = "..." if right < len(target_text) else ""
                print(f"  Matched: {matched}")
                print(f"  MatchContext: {prefix}{_one_line(excerpt)}{suffix}")
            else:
                # Print a small start-of-answer excerpt: first sentence if possible, else first N chars.
                cleaned = target_text.strip()
                first_sentence = re.split(r"(?<=[.!?])\s+|\n+", cleaned, maxsplit=1)[
                    0
                ].strip()
                excerpt = first_sentence if first_sentence else cleaned[:200]
                if len(excerpt) > 240:
                    excerpt = excerpt[:240] + "..."
                print(f"  NoMatchExcerpt: {_one_line(excerpt)}")
            if not enforcement_ok:
                print(f"  Enforcement: FAIL ({'; '.join(enforcement_errors)})")
            print()

            results.append(
                {
                    "id": tc.id,
                    "category": tc.category,
                    "query": tc.query,
                    "target": tc.target,
                    "pattern": tc.pattern,
                    "flags": _regex_flag_names(tc.flags),
                    "passed": ok,
                    "matched": matched,
                    "system_result": {
                        "route": system_result.get("route"),
                        "index_used": system_result.get("index_used"),
                        "agent_used": system_result.get("agent_used"),
                        "date_parser_tool_used": system_result.get(
                            "date_parser_tool_used", False
                        ),
                        "usage": system_result.get("usage"),
                    },
                    "enforcement": {
                        "expected_route": tc.expected_route,
                        "expected_agent_used": tc.expected_agent_used,
                        "ok": enforcement_ok,
                        "errors": enforcement_errors,
                    },
                }
            )
        except Exception as e:
            print(f"[ERROR] {i:02d}/{len(test_cases)} {tc.id} | {tc.category}")
            print(f"  Query: {tc.query}")
            print(f"  Error: {e}")
            print()
            results.append(
                {
                    "id": tc.id,
                    "category": tc.category,
                    "query": tc.query,
                    "target": tc.target,
                    "pattern": tc.pattern,
                    "flags": _regex_flag_names(tc.flags),
                    "passed": False,
                    "error": str(e),
                }
            )

    print("-" * 80)
    print(
        f"Regex Tests Passed: {passed}/{len(test_cases)} ({passed/len(test_cases)*100:.1f}%)"
    )

    return {"total": len(test_cases), "passed": passed, "results": results}


def run_human_grader_tests(system: MultiAgentSystem, interactive: bool = False) -> dict:
    """
    Run human-grader tests (manual Pass/Fail + notes) and return a JSON-serializable result object.
    """
    test_cases = get_human_grader_test_cases()
    results: list[dict] = []

    print("\n" + "=" * 80)
    print("HUMAN GRADER TESTS (PASS/FAIL)")
    print("=" * 80)
    print(f"Running {len(test_cases)} human grader tests...\n")

    for i, tc in enumerate(test_cases, 1):
        system_result = system.query(tc.query)

        answer = system_result.get("answer", "")
        print(f"  {_format_usage(system_result.get('usage'))}")
        # Print a capped answer so terminal output stays readable
        answer_preview = answer
        if len(answer_preview) > 2000:
            answer_preview = answer_preview[:2000] + "..."

        print(f"[HUMAN] {i:02d}/{len(test_cases)} {tc.id} | {tc.category}")
        print(f"  Query: {tc.query}")
        if tc.reference:
            print(f"  Reference: {tc.reference}")
        print(f"  Route: {system_result.get('route')}")
        print(f"  Agent: {system_result.get('agent_used')}")
        print("  Answer:")
        print(answer_preview)
        human_pass = None
        if interactive:
            while True:
                resp = input("\nGrade this test: [p]ass / [f]ail > ").strip().lower()
                if resp in ("p", "pass"):
                    human_pass = True
                    break
                if resp in ("f", "fail"):
                    human_pass = False
                    break
                print("Please enter 'p' or 'f'.")
        else:
            print("\n  HumanResult: PASS | FAIL")
        print("-" * 80)

        results.append(
            {
                "id": tc.id,
                "category": tc.category,
                "query": tc.query,
                "reference": tc.reference,
                "system_result": {
                    "route": system_result.get("route"),
                    "index_used": system_result.get("index_used"),
                    "agent_used": system_result.get("agent_used"),
                    "date_parser_tool_used": system_result.get(
                        "date_parser_tool_used", False
                    ),
                    "usage": system_result.get("usage"),
                    "answer": answer,
                },
                "human": {"pass": human_pass},
            }
        )

    return {"total": len(test_cases), "results": results}


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
            print(_format_usage(system_result.get("usage")))
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
                        "usage": system_result.get("usage"),
                        "answer": answer,
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

    # Run regex tests (lightweight checks)
    regex_tests = run_regex_tests(system)

    # Run human grader tests (manual) - non-interactive by default so full runs don't block
    human_grader_tests = run_human_grader_tests(system, interactive=False)

    # Save detailed results
    results_file = Path(__file__).parent / "evaluation_results.json"
    with open(results_file, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(test_cases),
                "successful_evaluations": len(successful_results),
                "results": results,
                "regex_tests": regex_tests,
                "human_grader_tests": human_grader_tests,
            },
            f,
            indent=2,
        )

    print(f"\n✓ Detailed results saved to: {results_file}")

    return results


if __name__ == "__main__":
    # Usage:
    #   python src/evaluation/run_evaluation.py            -> full LLM-judge suite + regex tests
    #   python src/evaluation/run_evaluation.py --regex-only -> regex tests only
    if "--human-only" in sys.argv:
        print("=" * 80)
        print("System Evaluation - Human Grader Tests Only")
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

        human_grader_tests = run_human_grader_tests(system, interactive=True)

        # Save human-only results in the same output file for consistency
        results_file = Path(__file__).parent / "evaluation_results.json"
        with open(results_file, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "total_tests": 0,
                    "successful_evaluations": 0,
                    "results": [],
                    "regex_tests": {"total": 0, "passed": 0, "results": []},
                    "human_grader_tests": human_grader_tests,
                },
                f,
                indent=2,
            )

        print(f"\n✓ Detailed results saved to: {results_file}")
    elif "--regex-only" in sys.argv:
        print("=" * 80)
        print("System Evaluation - Regex Tests Only")
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

        regex_tests = run_regex_tests(system)

        # Save regex-only results in the same output file for consistency
        results_file = Path(__file__).parent / "evaluation_results.json"
        with open(results_file, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "total_tests": 0,
                    "successful_evaluations": 0,
                    "results": [],
                    "regex_tests": regex_tests,
                    "human_grader_tests": {"total": 0, "results": []},
                },
                f,
                indent=2,
            )

        print(f"\n✓ Detailed results saved to: {results_file}")
    else:
        run_evaluation()
