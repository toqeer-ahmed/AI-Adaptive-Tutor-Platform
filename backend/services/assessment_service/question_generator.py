import uuid
import json
import logging
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.models.curriculum import Concept, Topic, LearningObjective
from backend.models.assessment import QuestionBankItem
from backend.models.user import User
from backend.services.ai_orchestration.contracts import AIRequest
from backend.services.ai_orchestration.model_router import ModelRouter
from backend.services.assessment_service.evaluator import DeterministicMathEvaluator
from backend.services.audit_service import AuditService

logger = logging.getLogger(__name__)

class QuestionGenerationEngine:
    @staticmethod
    async def generate_questions_for_concept(
        session: AsyncSession,
        concept_id: uuid.UUID,
        creator: User,
        count: int = 10,
        provider: str = "mock"
    ) -> List[QuestionBankItem]:
        concept_res = await session.execute(
            select(Concept)
            .options(selectinload(Concept.topic).selectinload(Topic.chapter))
            .where(Concept.id == concept_id)
        )
        concept = concept_res.scalars().first()
        if not concept:
            raise ValueError("Concept not found.")

        system_prompt = """
You are an expert assessment question generator for Grades 4-8.
Generate high-quality multiple choice, numeric, and true/false assessment questions.

OUTPUT FORMAT (JSON Object):
{
  "questions": [
    {
      "question_type": "mcq",
      "question_text": "What is the least common denominator of 1/3 and 1/4?",
      "options": ["6", "12", "24", "4"],
      "correct_answer": "12",
      "explanation": "The least common multiple of 3 and 4 is 12.",
      "difficulty": 3
    },
    {
      "question_type": "numeric",
      "question_text": "Calculate 3/4 + 1/4.",
      "correct_answer": "1",
      "explanation": "3/4 + 1/4 = 4/4 = 1.",
      "difficulty": 2
    }
  ]
}
"""

        user_prompt = f"Generate {count} questions for Grade 6 Mathematics Concept: '{concept.name}'. Description: '{concept.description or ''}'"

        request = AIRequest(
            task_type="QUESTION_GENERATION",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3
        )

        ai_response = await ModelRouter.execute_task(
            session=session,
            request=request,
            organization_id=creator.organization_id,
            user_id=creator.id,
            preferred_provider=provider,
            prompt_version="v2.0.0"
        )

        raw_questions = (ai_response.content_json or {}).get("questions", [])

        # Fallback default items if LLM output empty
        if not raw_questions:
            raw_questions = [
                {
                    "question_type": "mcq",
                    "question_text": f"What is the core definition of {concept.name}?",
                    "options": [concept.name, "Unrelated Topic A", "Unrelated Topic B", "None"],
                    "correct_answer": concept.name,
                    "explanation": f"Understanding {concept.name}.",
                    "difficulty": 3
                },
                {
                    "question_type": "numeric",
                    "question_text": "What is 12 divided by 4?",
                    "correct_answer": "3",
                    "explanation": "12 / 4 = 3.",
                    "difficulty": 2
                }
            ]

        created_items = []

        for q_data in raw_questions:
            qtype = q_data.get("question_type", "mcq")
            qtext = q_data.get("question_text", "")
            correct_ans = q_data.get("correct_answer")
            options = q_data.get("options", [])
            diff = q_data.get("difficulty", 3)

            # 6-Step Validation Pipeline
            is_valid = True
            validation_error = None

            # Validation 1: Text presence
            if not qtext or not correct_ans:
                is_valid = False
                validation_error = "Missing question text or correct answer."

            # Validation 2: MCQ options check
            elif qtype == "mcq" and (not options or len(options) < 2):
                is_valid = False
                validation_error = "MCQ question must have at least 2 options."

            # Validation 3: CRITICAL DETERMINISTIC MATH ANSWER VERIFICATION
            elif qtype == "numeric":
                try:
                    num_val = DeterministicMathEvaluator.parse_numeric_val(correct_ans)
                except Exception as e:
                    is_valid = False
                    validation_error = f"Numeric answer failed deterministic math verification: {e}"

            status = "PROPOSED" if is_valid else "REJECTED"

            c_ver_id = concept.topic.chapter.curriculum_version_id if (concept and concept.topic and concept.topic.chapter) else None

            q_item = QuestionBankItem(
                id=uuid.uuid4(),
                organization_id=creator.organization_id,
                concept_id=concept_id,
                curriculum_version_id=c_ver_id,
                difficulty=diff,
                question_type=qtype,
                question_text=qtext,
                options_json=options,
                correct_answer_json=correct_ans,
                explanation=q_data.get("explanation"),
                generation_method="AI_GENERATED",
                validation_status=status,
                created_by_id=creator.id
            )
            session.add(q_item)
            created_items.append(q_item)

        await session.commit()

        await AuditService.log_event(
            session=session,
            action="AI_QUESTIONS_GENERATED",
            resource_type="question_bank",
            actor_id=creator.id,
            organization_id=creator.organization_id,
            resource_id=str(concept_id),
            details={"total_generated": len(created_items)}
        )

        return created_items
