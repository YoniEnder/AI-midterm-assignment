"""
Evaluation Test Suite
Contains test queries with ground truth for system evaluation
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class TestCase:
    """Test case with query and expected results"""

    query: str
    ground_truth: str
    expected_index: str  # "Summary Index" or "Hierarchical Index"
    expected_route: str  # "HIGH_LEVEL" or "PRECISE"
    expected_context: str  # Description of expected context
    expected_info: str  # Description of expected information/chunks
    category: str  # Category of query


# Test suite with 8 queries covering different scenarios
EVALUATION_TEST_CASES: List[TestCase] = [
    # Test Case 1: High-level summary query
    TestCase(
        query="What is the overall summary of all insurance claims?",
        ground_truth="The dataset contains 10 insurance claims covering various types including Auto Collision, Health (knee surgery and workplace injury), Property Damage (water damage, fire, storm), Travel (delay and lost luggage), and Life Insurance. Claims involve various stages from filing to settlement, with some containing discrepancies between draft notes and final reports.",
        expected_index="Summary Index",
        expected_route="HIGH_LEVEL",
        expected_context="High-level overview of all claims, claim types, general patterns, and outcomes across the dataset",
        expected_info="Summary chunks from all claim documents covering claim types, general outcomes, and patterns",
        category="High-Level Summary",
    ),
    # Test Case 2: Precise factual query - Claim Document 01
    TestCase(
        query="In Claim Document 01, did the other driver acknowledge responsibility?",
        ground_truth="Yes, the other driver informally acknowledged responsibility according to an internal call log, but this was never included in any outbound communication or summary letter.",
        expected_index="Hierarchical Index",
        expected_route="PRECISE",
        expected_context="Claim Document 01 (Auto Collision), internal call log, driver acknowledgment, communication records",
        expected_info="Small/medium chunks from Claim Document 01 containing call log information about driver acknowledgment",
        category="Precise Factual",
    ),
    # Test Case 3: Precise factual query - Claim Document 03
    TestCase(
        query="What was the moisture reading in the earliest inspection for the Apartment Water Damage claim?",
        ground_truth="The moisture reading from the earliest inspection was significantly higher than the value used in the final report. The original measurement appears only once in a draft note.",
        expected_index="Hierarchical Index",
        expected_route="PRECISE",
        expected_context="Claim Document 03 (Apartment Water Damage), moisture readings, inspection reports, draft notes",
        expected_info="Small chunks from Claim Document 03 containing moisture reading measurements, particularly from draft notes",
        category="Precise Factual",
    ),
    # Test Case 4: Precise factual query - Claim Document 05
    TestCase(
        query="Did the patient complete conservative physical therapy in Claim Document 05?",
        ground_truth="Yes, a medical reviewer noted that the patient completed several weeks of conservative physical therapy, contradicting the denial letter's statement that conservative care was insufficient.",
        expected_index="Hierarchical Index",
        expected_route="PRECISE",
        expected_context="Claim Document 05 (Health - Knee Surgery Dispute), medical reviewer notes, physical therapy records, denial letter",
        expected_info="Small/medium chunks from Claim Document 05 containing medical reviewer notes about physical therapy completion",
        category="Precise Factual",
    ),
    # Test Case 5: Precise factual query - Claim Document 06
    TestCase(
        query="What time was the luggage scanned in Claim Document 06?",
        ground_truth="Airline baggage records showed the insured's luggage was scanned at the destination earlier than the reported time, but this timestamp appears only once and is ignored in the claim outcome.",
        expected_index="Hierarchical Index",
        expected_route="PRECISE",
        expected_context="Claim Document 06 (Travel Delay + Lost Luggage), airline baggage records, scanning timestamps, claim outcome",
        expected_info="Small chunks from Claim Document 06 containing baggage scanning timestamps and airline records",
        category="Precise Factual",
    ),
    # Test Case 6: Precise factual query - Claim Document 07
    TestCase(
        query="What billing code error was mentioned in Claim Document 07?",
        ground_truth="A provider confirmed in a one-line note that one billed charge was incorrectly coded, but the correction was never reflected in the reimbursement decision.",
        expected_index="Hierarchical Index",
        expected_route="PRECISE",
        expected_context="Claim Document 07 (Workplace Injury - Health), billing codes, provider notes, reimbursement decisions",
        expected_info="Small chunks from Claim Document 07 containing provider notes about billing code errors",
        category="Precise Factual",
    ),
    # Test Case 7: High-level query about claim types
    TestCase(
        query="What are the main types of insurance claims in the dataset?",
        ground_truth="The dataset contains Auto Collision claims (highway and regular), Health claims (knee surgery dispute and workplace injury), Property Damage claims (apartment water damage, kitchen fire, storm damage), Travel claims (delay and lost luggage), and Life Insurance claims (critical illness review).",
        expected_index="Summary Index",
        expected_route="HIGH_LEVEL",
        expected_context="Overview of claim types across all documents, categorization of different insurance claim types",
        expected_info="Summary chunks covering claim type classifications and distributions across the dataset",
        category="High-Level Categorization",
    ),
    # Test Case 8: Precise factual query - Claim Document 09
    TestCase(
        query="Was there evidence of misrepresentation in Claim Document 09?",
        ground_truth="No, an underwriting remark states there was no evidence of misrepresentation, even though the claim was initially flagged for contestability review. This remark appears nowhere else.",
        expected_index="Hierarchical Index",
        expected_route="PRECISE",
        expected_context="Claim Document 09 (Life Insurance - Critical Illness Review), underwriting remarks, misrepresentation evidence, contestability review",
        expected_info="Small chunks from Claim Document 09 containing underwriting remarks about misrepresentation",
        category="Precise Factual",
    ),
]


def get_test_cases() -> List[TestCase]:
    """Get all test cases"""
    return EVALUATION_TEST_CASES
