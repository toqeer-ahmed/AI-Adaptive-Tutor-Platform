import pytest
import uuid
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.routers.mastery import get_qualitative_band, get_student_knowledge_map
from backend.services.organization_service.service import OrganizationService
from backend.services.user_service.service import UserService

def test_qualitative_band_mapping():
    assert get_qualitative_band(0.10) == "Getting there 💡"
    assert get_qualitative_band(0.39) == "Getting there 💡"
    assert get_qualitative_band(0.40) == "On track 📈"
    assert get_qualitative_band(0.74) == "On track 📈"
    assert get_qualitative_band(0.75) == "Strong 🌟"
    assert get_qualitative_band(0.95) == "Strong 🌟"

@pytest.mark.asyncio
async def test_student_data_isolation_enforcement(db_session: AsyncSession):
    org = await OrganizationService.create_organization(db_session, "Isolation District", "ISOLDIST")
    student1 = await UserService.create_user(db_session, org.id, "stud1@school.edu", "Pass123!", "Student One", "Student")
    student2 = await UserService.create_user(db_session, org.id, "stud2@school.edu", "Pass123!", "Student Two", "Student")

    # Student 1 attempts to access Student 2's knowledge map -> Must raise HTTP 403 Forbidden
    with pytest.raises(HTTPException) as exc_info:
        await get_student_knowledge_map(
            student_id=str(student2.id),
            current_user=student1,
            session=db_session
        )

    assert exc_info.value.status_code == 403
    assert "Access denied" in exc_info.value.detail
