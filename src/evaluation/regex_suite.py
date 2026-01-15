"""
Regex-based evaluation suite.

These tests are lightweight checks that validate system outputs using simple regexes.
They are intended to run alongside the LLM-as-a-judge evaluation.

Note: Avoid date-parser shortcut keywords (see src/agents/constants.py) in queries for
Needle tests, otherwise the system may answer via DateParserTool instead of retrieval.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Optional

RegexTarget = Literal["answer", "route"]


@dataclass(frozen=True)
class RegexTestCase:
    id: str
    category: str  # e.g. "Regex: Needle" / "Regex: Manager"
    query: str
    target: RegexTarget
    pattern: str
    flags: int = re.IGNORECASE | re.MULTILINE

    # Optional enforcement checks (useful to ensure the right component ran)
    expected_route: Optional[str] = None  # "HIGH_LEVEL" or "PRECISE"
    expected_agent_used: Optional[str] = None  # e.g. "Needle-in-a-Haystack Agent"
    expected_date_parser_tool_used: Optional[bool] = None


def get_regex_test_cases() -> list[RegexTestCase]:
    """
    Return exactly 20 regex tests:
    - 15 Needle tests: diverse factual checks (names, amounts, locations, HH:MM stamps, and one tool-usage check)
      and must route PRECISE.
    - 5 Manager tests: router decision must match expected route (regex evaluated against route).
    """

    tests: list[RegexTestCase] = []

    # --- 15 Needle tests: diverse checks against the synthetic timeline dataset (docstore.json)
    # Case 1 – Auto Collision Claim #AC-2024-0193
    tests.extend(
        [
            RegexTestCase(
                id="needle_case1_claim_number",
                category="Regex: Needle",
                query="In Case 1 (Auto Collision), what is the claim number?",
                target="answer",
                pattern=r"\bAC-2024-0193\b",
                expected_route="PRECISE",
                expected_agent_used="Needle-in-a-Haystack Agent",
            ),
            RegexTestCase(
                id="needle_case1_policyholder",
                category="Regex: Needle",
                query="In Case 1 (Auto Collision), what is the policyholder's name?",
                target="answer",
                pattern=r"\bDaniel\s+Cohen\b",
                expected_route="PRECISE",
                expected_agent_used="Needle-in-a-Haystack Agent",
            ),
            RegexTestCase(
                id="needle_case1_policy_number",
                category="Regex: Needle",
                query="In Case 1 (Auto Collision), what is the policy number?",
                target="answer",
                pattern=r"\bAUTO-XL-774532\b",
                expected_route="PRECISE",
                expected_agent_used="Needle-in-a-Haystack Agent",
            ),
            RegexTestCase(
                id="needle_case1_insurer",
                category="Regex: Needle",
                query="In Case 1 (Auto Collision), what is the insurer name?",
                target="answer",
                pattern=r"\bSafeRoad\s+Mutual\s+Insurance\b",
                expected_route="PRECISE",
                expected_agent_used="Needle-in-a-Haystack Agent",
            ),
            RegexTestCase(
                id="needle_case1_deductible_amount",
                category="Regex: Needle",
                query="In Case 1 (Auto Collision), what is the deductible amount (in dollars)?",
                target="answer",
                pattern=r"\$\s*500\b",
                expected_route="PRECISE",
                expected_agent_used="Needle-in-a-Haystack Agent",
            ),
            RegexTestCase(
                id="needle_case1_accident_location",
                category="Regex: Needle",
                query="In Case 1 (Auto Collision), at which intersection did the accident occur?",
                target="answer",
                pattern=r"(King\s*St.*5th\s*Ave|5th\s*Ave.*King\s*St)",
                expected_route="PRECISE",
                expected_agent_used="Needle-in-a-Haystack Agent",
            ),
            RegexTestCase(
                id="needle_case1_officer_name",
                category="Regex: Needle",
                query="In Case 1 (Auto Collision), what is the police officer name listed in the report?",
                target="answer",
                pattern=r"\bOfficer\s+L\.\s*Goldman\b",
                expected_route="PRECISE",
                expected_agent_used="Needle-in-a-Haystack Agent",
            ),
            RegexTestCase(
                id="needle_case1_police_arrival_hhmm",
                category="Regex: Needle",
                query="In Case 1 (Auto Collision), what was the police arrival clock value (HH:MM)?",
                target="answer",
                pattern=r"\b0?8:12\b",
                expected_route="PRECISE",
                expected_agent_used="Needle-in-a-Haystack Agent",
            ),
            RegexTestCase(
                id="needle_case1_repair_shop_name",
                category="Regex: Needle",
                query="In Case 1 (Auto Collision), what is the name of the partnered repair shop?",
                target="answer",
                pattern=r"\bUrban\s+Auto\s+Body\b",
                expected_route="PRECISE",
                expected_agent_used="Needle-in-a-Haystack Agent",
            ),
            RegexTestCase(
                id="needle_case1_payment_authorized_amount",
                category="Regex: Needle",
                query="In Case 1 (Auto Collision), what payment amount was authorized to the repair shop?",
                target="answer",
                # Accept "$1,950" or "$1950"
                pattern=r"\$\s*1\s*,?\s*950\b",
                expected_route="PRECISE",
                expected_agent_used="Needle-in-a-Haystack Agent",
            ),
        ]
    )

    # Case 2 – Home Water Damage Claim #PD-2023-4410
    tests.extend(
        [
            RegexTestCase(
                id="needle_case2_claim_number",
                category="Regex: Needle",
                query="In Case 2 (Home Water Damage), what is the claim number?",
                target="answer",
                pattern=r"\bPD-2023-4410\b",
                expected_route="PRECISE",
                expected_agent_used="Needle-in-a-Haystack Agent",
            ),
            RegexTestCase(
                id="needle_case2_policyholder",
                category="Regex: Needle",
                query="In Case 2 (Home Water Damage), what is the policyholder's name?",
                target="answer",
                pattern=r"\bYael\s+Ben-Ami\b",
                expected_route="PRECISE",
                expected_agent_used="Needle-in-a-Haystack Agent",
            ),
            RegexTestCase(
                id="needle_case2_policy_number",
                category="Regex: Needle",
                query="In Case 2 (Home Water Damage), what is the policy number?",
                target="answer",
                pattern=r"\bHOME-PLUS-119844\b",
                expected_route="PRECISE",
                expected_agent_used="Needle-in-a-Haystack Agent",
            ),
            RegexTestCase(
                id="needle_tool_date_parser_used",
                category="Regex: Needle",
                query="Parse and normalize the date from January 15, 2024.",
                target="answer",
                pattern=r"\b2024-01-15T",
                expected_date_parser_tool_used=True,
            ),
        ]
    )

    # Case 3 – Health Insurance Claim #HI-2025-8831
    tests.append(
        RegexTestCase(
            id="needle_case3_claim_number",
            category="Regex: Needle",
            query="In Case 3 (Health Insurance), what is the claim number?",
            target="answer",
            pattern=r"\bHI-2025-8831\b",
            expected_route="PRECISE",
            expected_agent_used="Needle-in-a-Haystack Agent",
        )
    )

    # --- 5 Manager tests: route decision checks
    # These validate the router output (system_result["route"]) via regex.
    tests.extend(
        [
            RegexTestCase(
                id="manager_route_high_level_summary",
                category="Regex: Manager",
                query="What is the overall summary of all insurance claims?",
                target="route",
                pattern=r"^HIGH_LEVEL$",
            ),
            RegexTestCase(
                id="manager_route_high_level_categorization",
                category="Regex: Manager",
                query="What are the main types of insurance claims in the dataset?",
                target="route",
                pattern=r"^HIGH_LEVEL$",
            ),
            RegexTestCase(
                id="manager_route_precise_claim_id",
                category="Regex: Manager",
                query="What is the claim ID for Claim Document 07?",
                target="route",
                pattern=r"^PRECISE$",
            ),
            RegexTestCase(
                id="manager_route_precise_yes_no",
                category="Regex: Manager",
                query="In Claim Document 01, did the other driver acknowledge responsibility?",
                target="route",
                pattern=r"^PRECISE$",
            ),
            RegexTestCase(
                id="manager_route_precise_underwriting",
                category="Regex: Manager",
                query="Was there evidence of misrepresentation in Claim Document 09?",
                target="route",
                pattern=r"^PRECISE$",
            ),
        ]
    )

    if len(tests) != 20:
        raise RuntimeError(f"Expected exactly 20 regex tests, got {len(tests)}")

    return tests
