# Quick Start Guide

## Running the System

### 1. Basic Demonstration
```bash
python src/main.py
```

### 2. Interactive Mode
```bash
python src/main.py --interactive
```

### 3. Run Evaluation
```bash
python src/run_evaluation.py
```

## Evaluation Overview

The evaluation system uses **LLM-as-a-Judge** with GPT-4 to evaluate:

1. **Answer Correctness** - Does the answer match ground truth?
2. **Context Relevancy** - Did the agent use the correct index?
3. **Context Recall** - Did the system retrieve correct chunks?

### Test Suite

8 test cases covering:
- 2 High-level queries (summaries, categorization)
- 6 Precise factual queries (specific claim details)

### Results

- Console output with scores and reasoning
- Detailed JSON results in `evaluation_results.json`
- Summary statistics (averages, routing accuracy, etc.)

## Key Files

- `src/evaluator.py` - Evaluation system with judge prompts
- `src/evaluation_suite.py` - Test cases with ground truth
- `src/run_evaluation.py` - Evaluation runner
- `evaluation_results.json` - Detailed results (generated)
- `EVALUATION_SUMMARY.md` - Summary of results

## Example Evaluation Output

```
Test Case 1/8: Precise Factual
Query: In Claim Document 01, did the other driver acknowledge responsibility?

Route: PRECISE
Index Used: Hierarchical Index
Agent: Needle-in-a-Haystack Agent

📊 Evaluation Results:
  Correctness: 0.85 - Answer correctly identifies driver acknowledgment
  Relevancy: 0.90 - Correct index used, relevant context retrieved
  Recall: 0.80 - Correct chunks retrieved, minor details present
  Overall Score: 0.85
```


