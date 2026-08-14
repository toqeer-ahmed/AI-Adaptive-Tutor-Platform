import uuid
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_db, get_current_user, require_roles
from backend.services.user_service.service import ClassService
from backend.services.security_service import SecurityService
from backend.services.audit_service import AuditService
from backend.models.user import User

router = APIRouter(prefix="/classes", tags=["Classes"])

class CreateClassRequest(BaseModel):
    school_id: str
    teacher_id: str
    name: str
    grade_level: int
    academic_year: str

class EnrollStudentRequest(BaseModel):
    student_id: str

@router.post("", response_model=dict, dependencies=[Depends(require_roles(["OrgAdmin", "SchoolAdmin", "Teacher", "SuperAdmin"]))])
async def create_class(
    req: CreateClassRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    cls = await ClassService.create_class(
        session=session,
        organization_id=current_user.organization_id,
        school_id=uuid.UUID(req.school_id),
        teacher_id=uuid.UUID(req.teacher_id),
        name=req.name,
        grade_level=req.grade_level,
        academic_year=req.academic_year
    )

    await AuditService.log_event(
        session=session,
        action="CLASS_CREATED",
        resource_type="class",
        actor_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_id=str(cls.id),
        details={"name": cls.name, "grade_level": cls.grade_level}
    )

    return {
        "data": {
            "id": str(cls.id),
            "organization_id": str(cls.organization_id),
            "school_id": str(cls.school_id),
            "teacher_id": str(cls.teacher_id),
            "name": cls.name,
            "grade_level": cls.grade_level,
            "academic_year": cls.academic_year,
            "created_at": cls.created_at.isoformat()
        },
        "error": None,
        "meta": {}
    }

@router.get("/{class_id}", response_model=dict)
async def get_class(
    class_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    class_uuid = uuid.UUID(class_id)
    try:
        # Enforces teacher class assignment check & IDOR protection
        cls = await SecurityService.verify_class_access(session, current_user, class_uuid)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return {
        "data": {
            "id": str(cls.id),
            "organization_id": str(cls.organization_id),
            "school_id": str(cls.school_id),
            "teacher_id": str(cls.teacher_id),
            "name": cls.name,
            "grade_level": cls.grade_level,
            "academic_year": cls.academic_year
        },
        "error": None,
        "meta": {}
    }

@router.post("/{class_id}/enroll", response_model=dict, dependencies=[Depends(require_roles(["OrgAdmin", "SchoolAdmin", "Teacher", "SuperAdmin"]))])
async def enroll_student(
    class_id: str,
    req: EnrollStudentRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    class_uuid = uuid.UUID(class_id)
    try:
        cls = await SecurityService.verify_class_access(session, current_user, class_uuid)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    enrollment = await ClassService.enroll_student(
        session=session,
        organization_id=current_user.organization_id,
        class_id=class_uuid,
        student_id=uuid.UUID(req.student_id)
    )

    await AuditService.log_event(
        session=session,
        action="STUDENT_ENROLLED",
        resource_type="enrollment",
        actor_id=current_user.id,
        organization_id=current_user.organization_id,
        resource_id=str(enrollment.id),
        details={"class_id": str(class_uuid), "student_id": req.student_id}
    )

    return {
        "data": {
            "id": str(enrollment.id),
            "organization_id": str(enrollment.organization_id),
            "class_id": str(enrollment.class_id),
            "student_id": str(enrollment.student_id),
            "enrolled_at": enrollment.enrolled_at.isoformat()
        },
        "error": None,
        "meta": {}
    }

@router.get("", response_model=dict)
async def list_classes(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    classes = await ClassService.get_classes_for_user(session, current_user)
    return {
        "data": [
            {
                "id": str(c.id),
                "organization_id": str(c.organization_id),
                "school_id": str(c.school_id),
                "teacher_id": str(c.teacher_id),
                "name": c.name,
                "grade_level": c.grade_level,
                "academic_year": c.academic_year
            } for c in classes
        ],
        "error": None,
        "meta": {"count": len(classes)}
    }

@router.get("/{class_id}/students", response_model=dict)
async def list_class_students(
    class_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    class_uuid = uuid.UUID(class_id)
    try:
        await SecurityService.verify_class_access(session, current_user, class_uuid)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    students = await ClassService.get_class_students(session, class_uuid)
    return {
        "data": [
            {
                "id": str(s.id),
                "email": s.email,
                "full_name": s.full_name,
                "created_at": s.created_at.isoformat() if hasattr(s, 'created_at') and s.created_at else None
            } for s in students
        ],
        "error": None,
        "meta": {"count": len(students)}
    }

