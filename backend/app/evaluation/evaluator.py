"""
RAG Evaluator — measures pipeline quality against test datasets.
"""

import time
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import EvaluationRun, EvaluationQuestion
from app.rag.pipeline import RAGPipeline
from app.providers.llm_provider import get_llm_provider

logger = structlog.get_logger()


class Evaluator:
    """Evaluates RAG pipeline quality using configurable metrics."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pipeline = RAGPipeline(db)
        self.llm = get_llm_provider()
    
    async def run(self, run_id: str):
        """Execute an evaluation run."""
        run_uuid = uuid.UUID(run_id)
        
        result = await self.db.execute(
            select(EvaluationRun).where(EvaluationRun.id == run_uuid)
        )
        run = result.scalar_one_or_none()
        if not run:
            raise ValueError(f"Evaluation run {run_id} not found")
        
        run.status = "RUNNING"
        await self.db.flush()
        
        # Get questions
        q_result = await self.db.execute(
            select(EvaluationQuestion).where(
                EvaluationQuestion.evaluation_run_id == run_uuid
            )
        )
        questions = q_result.scalars().all()
        
        metrics = {
            "faithfulness_scores": [],
            "relevance_scores": [],
            "context_precision_scores": [],
            "context_recall_scores": [],
            "retrieval_successes": [],
            "latencies": [],
        }
        
        for question in questions:
            try:
                await self._evaluate_question(question, run.knowledge_base_id, metrics)
            except Exception as e:
                logger.error("Question evaluation failed", question=question.question[:50], error=str(e))
                question.faithfulness_score = 0
                question.relevance_score = 0
        
        await self.db.flush()
        
        # Aggregate metrics
        run.faithfulness = self._avg(metrics["faithfulness_scores"])
        run.answer_relevance = self._avg(metrics["relevance_scores"])
        run.context_precision = self._avg(metrics["context_precision_scores"])
        run.context_recall = self._avg(metrics["context_recall_scores"])
        
        successes = metrics["retrieval_successes"]
        run.retrieval_success_rate = (sum(successes) / len(successes) * 100) if successes else 0
        
        # Hallucination rate = 1 - faithfulness
        run.hallucination_rate = max(0, 100 - (run.faithfulness or 0))
        run.avg_latency_ms = self._avg(metrics["latencies"])
        
        run.status = "COMPLETED"
        run.completed_at = datetime.now(timezone.utc)
        await self.db.flush()
        
        logger.info("Evaluation complete", run_id=run_id, faithfulness=run.faithfulness)
    
    async def _evaluate_question(
        self,
        question: EvaluationQuestion,
        knowledge_base_id: uuid.UUID,
        metrics: dict,
    ):
        """Evaluate a single question through the RAG pipeline."""
        start = time.perf_counter()
        
        # Run the RAG pipeline
        result = await self.pipeline.run(
            query=question.question,
            knowledge_base_id=knowledge_base_id,
        )
        
        latency = (time.perf_counter() - start) * 1000
        question.latency_ms = latency
        metrics["latencies"].append(latency)
        
        question.generated_answer = result["answer"]
        question.retrieved_sources = [
            {"document": c.get("document_name"), "chunk_id": str(c.get("chunk_id"))}
            for c in result.get("citations", [])
        ]
        
        # Check retrieval success — did we retrieve anything relevant?
        retrieval_success = len(result.get("citations", [])) > 0
        question.retrieval_success = retrieval_success
        metrics["retrieval_successes"].append(1 if retrieval_success else 0)
        
        # Use LLM to evaluate faithfulness and relevance
        if question.expected_answer and result["answer"]:
            eval_scores = await self._llm_evaluate(
                question.question,
                question.expected_answer,
                result["answer"],
                result.get("citations", []),
            )
            
            question.faithfulness_score = eval_scores.get("faithfulness", 0)
            question.relevance_score = eval_scores.get("relevance", 0)
            question.context_precision = eval_scores.get("context_precision", 0)
            question.context_recall = eval_scores.get("context_recall", 0)
            
            metrics["faithfulness_scores"].append(question.faithfulness_score)
            metrics["relevance_scores"].append(question.relevance_score)
            metrics["context_precision_scores"].append(question.context_precision)
            metrics["context_recall_scores"].append(question.context_recall)
    
    async def _llm_evaluate(
        self,
        question: str,
        expected: str,
        generated: str,
        citations: list,
    ) -> dict:
        """Use the LLM to evaluate answer quality."""
        prompt = f"""Evaluate this RAG-generated answer. Score each metric from 0 to 100.

QUESTION: {question}

EXPECTED ANSWER: {expected}

GENERATED ANSWER: {generated}

NUMBER OF CITATIONS: {len(citations)}

Score these metrics:
- faithfulness: Does the generated answer stick to the evidence? (0=completely fabricated, 100=fully grounded)
- relevance: Does the generated answer address the question? (0=irrelevant, 100=perfectly relevant)
- context_precision: Are the retrieved sources relevant to the question? (0=irrelevant sources, 100=all sources relevant)
- context_recall: Does the answer cover the expected answer's key points? (0=misses everything, 100=covers everything)

Respond with ONLY valid JSON: {{"faithfulness": N, "relevance": N, "context_precision": N, "context_recall": N}}"""
        
        try:
            response = await self.llm.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200,
            )
            
            import json
            content = response["content"].strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            
            scores = json.loads(content)
            return {k: min(100, max(0, float(v))) for k, v in scores.items()}
        except Exception as e:
            logger.warning("LLM evaluation failed", error=str(e))
            return {"faithfulness": 50, "relevance": 50, "context_precision": 50, "context_recall": 50}
    
    def _avg(self, values: list) -> float:
        if not values:
            return 0
        return round(sum(values) / len(values), 2)
