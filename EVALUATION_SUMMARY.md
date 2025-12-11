# System Evaluation Summary

## Overview

This document provides a summary of the LLM-as-a-Judge evaluation of the Multi-Agent System. The full evaluation details are available in `README.md`.

## Evaluation Metrics

The system is evaluated on three key metrics:

1. **Answer Correctness** (40% weight): Does the answer match ground truth?
2. **Context Relevancy** (30% weight): Did the agent use the correct index and relevant segments?
3. **Context Recall** (30% weight): Did the system retrieve the correct chunk(s)?

## Test Suite

The evaluation uses **8 test cases** covering:

- **High-Level Queries** (2 tests): Summary and categorization queries
- **Precise Factual Queries** (6 tests): Specific details from individual claim documents

### Test Cases

1. **Overall Summary Query** - High-level summary of all claims
2. **Driver Acknowledgment** (Claim 01) - Precise factual query
3. **Moisture Reading** (Claim 03) - Precise factual query
4. **Physical Therapy** (Claim 05) - Precise factual query
5. **Luggage Scanning** (Claim 06) - Precise factual query
6. **Billing Code Error** (Claim 07) - Precise factual query
7. **Claim Types** - High-level categorization
8. **Misrepresentation Evidence** (Claim 09) - Precise factual query

## Key Findings

### Overall Performance

- **Average Correctness Score**: Evaluated per test case
- **Average Relevancy Score**: Evaluated per test case
- **Average Recall Score**: Evaluated per test case
- **Overall Average Score**: Weighted combination of all metrics

### Routing Accuracy

- **Routing Decision Accuracy**: Percentage of queries correctly routed to HIGH_LEVEL vs PRECISE
- **Index Selection Accuracy**: Percentage of queries using the correct index (Summary vs Hierarchical)

### Performance by Category

- **High-Level Queries**: Performance on summary and overview queries
- **Precise Factual Queries**: Performance on specific detail queries

## Judge Model

- **Model**: GPT-4
- **Temperature**: 0 (deterministic)
- **Evaluation Method**: Structured JSON responses with scores and reasoning

## Running Evaluation

To run the full evaluation:

```bash
python src/run_evaluation.py
```

Results are saved to `evaluation_results.json` with detailed scores and reasoning for each test case.

## Evaluation Prompts

The system uses three specialized judge prompts:

1. **Correctness Prompt**: Evaluates factual accuracy and completeness
2. **Relevancy Prompt**: Evaluates index selection and context appropriateness
3. **Recall Prompt**: Evaluates retrieval of correct information chunks

Each prompt returns structured JSON with:
- Score (0.0 to 1.0)
- Reasoning explanation
- Boolean flags for specific criteria

## Notes

- Evaluation results may vary slightly between runs due to LLM non-determinism
- Ground truth is based on the `needleDetails.txt` file and document analysis
- The judge model (GPT-4) provides consistent and reliable evaluations


