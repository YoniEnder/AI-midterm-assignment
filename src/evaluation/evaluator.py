"""
LLM-as-a-Judge Evaluation System
Evaluates agent responses based on Answer Correctness, Context Relevancy, and Context Recall
"""

from typing import Dict, List, Optional, Any
import os
from llama_index.llms.openai import OpenAI
from llama_index.core.prompts import PromptTemplate
from llama_index.core import VectorStoreIndex, SummaryIndex
from dotenv import load_dotenv
import json
from pathlib import Path

load_dotenv()


class SystemEvaluator:
    """
    Evaluates multi-agent system using LLM-as-a-judge approach
    """

    def __init__(self, judge_model: Optional[str] = None):
        """
        Initialize evaluator with judge LLM

        Args:
            judge_model: Model to use as judge (if None, reads from JUDGE_MODEL env var, defaults to gpt-4o-mini)
        """
        if judge_model is None:
            judge_model = os.getenv("JUDGE_MODEL", "gpt-4o-mini")
        self.judge_llm = OpenAI(temperature=0, model=judge_model)

        # Define judge prompts
        self.correctness_prompt = self._create_correctness_prompt()
        self.relevancy_prompt = self._create_relevancy_prompt()
        self.recall_prompt = self._create_recall_prompt()

    def _create_correctness_prompt(self) -> PromptTemplate:
        """Create prompt for answer correctness evaluation"""
        return PromptTemplate(
            """You are an expert evaluator judging the correctness of an AI system's answer.

Task: Evaluate whether the system's answer correctly addresses the user query and matches the ground truth.

User Query: {query}

Ground Truth: {ground_truth}

System Answer: {answer}

Evaluation Criteria:
1. Does the answer directly address the query?
2. Does the answer contain the key information from the ground truth?
3. Are there any factual errors or contradictions?
4. Is the answer complete (not missing important details)?

Respond with a JSON object:
{{
    "score": <float between 0.0 and 1.0>,
    "reasoning": "<brief explanation of the score>",
    "correct": <true if score >= 0.7, false otherwise>
}}

Score Guidelines:
- 1.0: Perfect match, all key information present
- 0.8-0.9: Mostly correct, minor details may differ
- 0.6-0.7: Partially correct, some key information missing
- 0.4-0.5: Somewhat relevant but incorrect or incomplete
- 0.0-0.3: Incorrect or irrelevant

Return ONLY the JSON object, no additional text.
"""
        )

    def _create_relevancy_prompt(self) -> PromptTemplate:
        """Create prompt for context relevancy evaluation"""
        return PromptTemplate(
            """You are an expert evaluator judging the relevancy of context used by an AI system.

Task: Evaluate whether the system used the correct index and relevant context segments.

User Query: {query}

Expected Index: {expected_index}
Actual Index Used: {actual_index}

Expected Context Topics: {expected_context}

System Answer: {answer}

Evaluation Criteria:
1. Was the correct index used? (Summary Index for high-level queries, Hierarchical Index for precise queries)
2. Does the answer reflect information from relevant document sections?
3. Are the retrieved chunks appropriate for the query type?
4. Would a human expert have used similar context?

Respond with a JSON object:
{{
    "score": <float between 0.0 and 1.0>,
    "reasoning": "<brief explanation of the score>",
    "correct_index": <true if correct index was used, false otherwise>,
    "relevant_context": <true if context is relevant, false otherwise>
}}

Score Guidelines:
- 1.0: Perfect - correct index and highly relevant context
- 0.8-0.9: Correct index, mostly relevant context
- 0.6-0.7: Correct index but context could be more relevant
- 0.4-0.5: Wrong index or mostly irrelevant context
- 0.0-0.3: Completely wrong index or irrelevant context

Return ONLY the JSON object, no additional text.
"""
        )

    def _create_recall_prompt(self) -> PromptTemplate:
        """Create prompt for context recall evaluation"""
        return PromptTemplate(
            """You are an expert evaluator judging whether an AI system retrieved the correct information chunks.

Task: Evaluate whether the system successfully retrieved the relevant chunks that contain the answer.

User Query: {query}

Ground Truth: {ground_truth}

System Answer: {answer}

Expected Information: {expected_info}

Evaluation Criteria:
1. Does the answer contain information from the expected chunks?
2. Were the correct document sections retrieved?
3. Is the retrieved information sufficient to answer the query?
4. Are there missing chunks that should have been retrieved?

Respond with a JSON object:
{{
    "score": <float between 0.0 and 1.0>,
    "reasoning": "<brief explanation of the score>",
    "retrieved_correct": <true if correct chunks were retrieved, false otherwise>,
    "missing_info": "<list any important information that seems missing>"
}}

Score Guidelines:
- 1.0: All relevant chunks retrieved, complete information
- 0.8-0.9: Most relevant chunks retrieved, minor gaps
- 0.6-0.7: Some relevant chunks retrieved, some important info missing
- 0.4-0.5: Few relevant chunks retrieved, significant gaps
- 0.0-0.3: Wrong chunks retrieved or critical information missing

Return ONLY the JSON object, no additional text.
"""
        )

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        import re

        # Try to extract JSON from response
        json_match = re.search(r"\{[^}]+\}", response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # Fallback: try parsing the whole response
        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            return {
                "score": 0.0,
                "reasoning": "Failed to parse judge response",
                "error": True,
            }

    def evaluate_correctness(
        self, query: str, answer: str, ground_truth: str
    ) -> Dict[str, Any]:
        """
        Evaluate answer correctness

        Args:
            query: User query
            answer: System's answer
            ground_truth: Expected correct answer

        Returns:
            Dictionary with score, reasoning, and correct flag
        """
        prompt = self.correctness_prompt.format(
            query=query, answer=answer, ground_truth=ground_truth
        )

        try:
            response = self.judge_llm.complete(prompt)
            result = self._parse_json_response(response.text)
            result["metric"] = "correctness"
            return result
        except Exception as e:
            return {
                "metric": "correctness",
                "score": 0.0,
                "reasoning": f"Evaluation error: {str(e)}",
                "correct": False,
                "error": True,
            }

    def evaluate_relevancy(
        self,
        query: str,
        answer: str,
        expected_index: str,
        actual_index: str,
        expected_context: str,
    ) -> Dict[str, Any]:
        """
        Evaluate context relevancy

        Args:
            query: User query
            answer: System's answer
            expected_index: Expected index type ("Summary Index" or "Hierarchical Index")
            actual_index: Actually used index
            expected_context: Description of expected context topics

        Returns:
            Dictionary with score, reasoning, and flags
        """
        prompt = self.relevancy_prompt.format(
            query=query,
            answer=answer,
            expected_index=expected_index,
            actual_index=actual_index,
            expected_context=expected_context,
        )

        try:
            response = self.judge_llm.complete(prompt)
            result = self._parse_json_response(response.text)
            result["metric"] = "relevancy"
            return result
        except Exception as e:
            return {
                "metric": "relevancy",
                "score": 0.0,
                "reasoning": f"Evaluation error: {str(e)}",
                "correct_index": False,
                "relevant_context": False,
                "error": True,
            }

    def evaluate_recall(
        self, query: str, answer: str, ground_truth: str, expected_info: str
    ) -> Dict[str, Any]:
        """
        Evaluate context recall

        Args:
            query: User query
            answer: System's answer
            ground_truth: Expected correct answer
            expected_info: Description of expected information/chunks

        Returns:
            Dictionary with score, reasoning, and flags
        """
        prompt = self.recall_prompt.format(
            query=query,
            answer=answer,
            ground_truth=ground_truth,
            expected_info=expected_info,
        )

        try:
            response = self.judge_llm.complete(prompt)
            result = self._parse_json_response(response.text)
            result["metric"] = "recall"
            return result
        except Exception as e:
            return {
                "metric": "recall",
                "score": 0.0,
                "reasoning": f"Evaluation error: {str(e)}",
                "retrieved_correct": False,
                "error": True,
            }

    def evaluate_query(
        self,
        query: str,
        answer: str,
        route: str,
        index_used: str,
        ground_truth: str,
        expected_index: str,
        expected_context: str,
        expected_info: str,
    ) -> Dict[str, Any]:
        """
        Evaluate a single query on all three metrics

        Args:
            query: User query
            answer: System's answer
            route: Routing decision (HIGH_LEVEL or PRECISE)
            index_used: Index actually used
            ground_truth: Expected correct answer
            expected_index: Expected index type
            expected_context: Expected context topics
            expected_info: Expected information/chunks

        Returns:
            Dictionary with all evaluation results
        """
        correctness = self.evaluate_correctness(query, answer, ground_truth)
        relevancy = self.evaluate_relevancy(
            query, answer, expected_index, index_used, expected_context
        )
        recall = self.evaluate_recall(query, answer, ground_truth, expected_info)

        # Calculate overall score (weighted average)
        overall_score = (
            correctness.get("score", 0.0) * 0.4
            + relevancy.get("score", 0.0) * 0.3
            + recall.get("score", 0.0) * 0.3
        )

        return {
            "query": query,
            "route": route,
            "index_used": index_used,
            "correctness": correctness,
            "relevancy": relevancy,
            "recall": recall,
            "overall_score": overall_score,
        }
