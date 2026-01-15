"""
Human grader evaluation suite.

These tests are intended for manual review (Pass/Fail + notes). We reuse queries from
src/evaluation/evaluation_suite.py so you can compare with LLM-as-a-judge runs.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HumanGraderTestCase:
    id: str
    category: str
    query: str
    reference: str = ""  # Optional hint for graders: what to look for


def get_human_grader_test_cases() -> list[HumanGraderTestCase]:
    """
    Return exactly 5 human-grader tests (reused from evaluation_suite.py):
    - 2 HIGH_LEVEL
    - 3 PRECISE
    """

    tests: list[HumanGraderTestCase] = [
        HumanGraderTestCase(
            id="hg_01_overall_summary",
            category="Human Grader: High-Level",
            query="What is the overall summary of all insurance claims?",
            reference="Should cover claim types (Auto/Health/Property/Travel/Life) and key outcomes; note any discrepancies mention.",
        ),
        HumanGraderTestCase(
            id="hg_02_claim_types",
            category="Human Grader: High-Level",
            query="What are the main types of insurance claims in the dataset?",
            reference="Should enumerate the main categories and ideally mention examples/subtypes.",
        ),
        HumanGraderTestCase(
            id="hg_03_acknowledge_responsibility_doc01",
            category="Human Grader: Precise",
            query="In Claim Document 01, did the other driver acknowledge responsibility?",
            reference="Look for the call-log/internal note nuance (informal acknowledgment vs official comms).",
        ),
        HumanGraderTestCase(
            id="hg_04_billing_code_error_doc07",
            category="Human Grader: Precise",
            query="What billing code error was mentioned in Claim Document 07?",
            reference="Should identify what was incorrectly coded (one-line provider note) and whether it impacted reimbursement.",
        ),
        HumanGraderTestCase(
            id="hg_05_misrepresentation_doc09",
            category="Human Grader: Precise",
            query="Was there evidence of misrepresentation in Claim Document 09?",
            reference="Should reflect underwriting remark / contestability nuance (no evidence).",
        ),
    ]

    if len(tests) != 5:
        raise RuntimeError(f"Expected exactly 5 human grader tests, got {len(tests)}")

    return tests

