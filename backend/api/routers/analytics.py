import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.api.deps import get_db, get_current_user, require_roles
from backend.models.class_model import Class, Enrollment
from backend.models.mastery import StudentMastery
from backend.models.misconception import StudentMisconception
from backend.models.assessment import AssessmentAttempt
from backend.models.user import User

router = APIRouter(prefix="/analytics", tags=["Teacher Analytics"])

@router.get("/class/{class_id}", response_model=dict)
async def get_class_analytics(
    class_id: str,
    current_user: User = Depends(require_roles(["Teacher", "SchoolAdmin", "SuperAdmin"])),
    session: AsyncSession = Depends(get_db)
):
    cls_uuid = uuid.UUID(class_id)

    # 1. Class Security Guard: Verify teacher access
    cls_stmt = select(Class).where(
        Class.id == cls_uuid,
        Class.organization_id == current_user.organization_id
    )
    cls_res = await session.execute(cls_stmt)
    class_obj = cls_res.scalars().first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found or unauthorized.")

    user_roles = [ur.role.name for ur in current_user.roles] if hasattr(current_user, 'roles') and current_user.roles else []
    if "Teacher" in user_roles and "SuperAdmin" not in user_roles and "SchoolAdmin" not in user_roles:
        if class_obj.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cross-class access denied. Teacher is not assigned to this class."
            )

    # 2. Fetch Enrolled Students
    enr_stmt = select(Enrollment).options(selectinload(Enrollment.student)).where(Enrollment.class_id == cls_uuid)
    enr_res = await session.execute(enr_stmt)
    enrollments = enr_res.scalars().all()
    student_ids = [e.student_id for e in enrollments]

    if not student_ids:
        return {
            "data": {
                "class_id": class_id,
                "class_name": class_obj.name,
                "student_count": 0,
                "class_average_mastery": 0.0,
                "concept_heatmap": [],
                "students_needing_remediation": [],
                "students_ready_for_challenge": [],
                "misconception_trends": [],
                "completion_rate": 1.0
            },
            "error": None,
            "meta": {}
        }

    # 3. Aggregate Student Masteries
    sm_stmt = select(StudentMastery).where(StudentMastery.student_id.in_(student_ids))
    sm_res = await session.execute(sm_stmt)
    masteries = sm_res.scalars().all()

    avg_mastery = sum(m.mastery_score for m in masteries) / len(masteries) if masteries else 0.0

    # Students needing remediation (< 0.40) vs challenge (>= 0.90)
    remediation_students = []
    challenge_students = []
    student_map = {e.student_id: e.student.full_name for e in enrollments if e.student}

    for m in masteries:
        s_name = student_map.get(m.student_id, "Student")
        if m.mastery_score < 0.40 and s_name not in [s["name"] for s in remediation_students]:
            remediation_students.append({"student_id": str(m.student_id), "name": s_name, "mastery_score": m.mastery_score})
        elif m.mastery_score >= 0.90 and s_name not in [s["name"] for s in challenge_students]:
            challenge_students.append({"student_id": str(m.student_id), "name": s_name, "mastery_score": m.mastery_score})

    # Concept Heatmap
    concept_scores: Dict[str, List[float]] = {}
    for m in masteries:
        c_id = str(m.concept_id)
        concept_scores.setdefault(c_id, []).append(m.mastery_score)

    heatmap = [
        {"concept_id": cid, "average_mastery": sum(scores)/len(scores), "student_count": len(scores)}
        for cid, scores in concept_scores.items()
    ]

    # Misconception Trends
    misc_stmt = select(StudentMisconception).options(selectinload(StudentMisconception.taxonomy)).where(
        StudentMisconception.student_id.in_(student_ids),
        StudentMisconception.status.in_(["DETECTED", "PERSISTENT"])
    )
    misc_res = await session.execute(misc_stmt)
    misconceptions = misc_res.scalars().all()

    misc_counts: Dict[str, Dict[str, Any]] = {}
    for m in misconceptions:
        code = m.taxonomy.code if m.taxonomy else "UNKNOWN"
        name = m.taxonomy.name if m.taxonomy else "Misconception"
        if code not in misc_counts:
            misc_counts[code] = {"code": code, "name": name, "count": 0}
        misc_counts[code]["count"] += 1

    # Assessment Completion Rate
    att_stmt = select(AssessmentAttempt).where(AssessmentAttempt.student_id.in_(student_ids))
    att_res = await session.execute(att_stmt)
    attempts = att_res.scalars().all()

    graded_count = sum(1 for a in attempts if a.status == "GRADED")
    completion_rate = graded_count / len(attempts) if attempts else 1.0

    return {
        "data": {
            "class_id": class_id,
            "class_name": class_obj.name,
            "student_count": len(student_ids),
            "class_average_mastery": round(avg_mastery, 2),
            "concept_heatmap": heatmap,
            "students_needing_remediation": remediation_students,
            "students_ready_for_challenge": challenge_students,
            "misconception_trends": list(misc_counts.values()),
            "completion_rate": round(completion_rate, 2)
        },
        "error": None,
        "meta": {}
    }

@router.get("/student/{student_id}", response_model=dict)
async def get_authorized_student_detail(
    student_id: str,
    current_user: User = Depends(require_roles(["Teacher", "SchoolAdmin", "SuperAdmin"])),
    session: AsyncSession = Depends(get_db)
):
    stud_uuid = uuid.UUID(student_id)

    sm_stmt = select(StudentMastery).where(
        StudentMastery.student_id == stud_uuid,
        StudentMastery.organization_id == current_user.organization_id
    )
    sm_res = await session.execute(sm_stmt)
    masteries = sm_res.scalars().all()

    # Raw mastery data accessible to authorized teachers
    return {
        "data": {
            "student_id": student_id,
            "masteries": [
                {
                    "concept_id": str(m.concept_id),
                    "raw_mastery_score": m.mastery_score, # Raw float allowed for authorized teachers
                    "confidence": m.confidence,
                    "attempt_count": m.attempt_count,
                    "correct_count": m.correct_count,
                    "incorrect_count": m.incorrect_count,
                    "status": m.status,
                    "misconception_tags": [str(t) for t in (m.misconception_tags or [])]
                } for m in masteries
            ]
        },
        "error": None,
        "meta": {}
    }
