import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.models.organization import Organization, School

class OrganizationService:
    @staticmethod
    async def create_organization(
        session: AsyncSession,
        name: str,
        code: str,
        settings_dict: Optional[dict] = None
    ) -> Organization:
        org = Organization(
            id=uuid.uuid4(),
            name=name,
            code=code.upper(),
            settings=settings_dict or {}
        )
        session.add(org)
        await session.commit()
        await session.refresh(org)
        return org

    @staticmethod
    async def get_organization_by_id(session: AsyncSession, org_id: uuid.UUID) -> Optional[Organization]:
        result = await session.execute(select(Organization).where(Organization.id == org_id))
        return result.scalars().first()

    @staticmethod
    async def get_organization_by_code(session: AsyncSession, code: str) -> Optional[Organization]:
        result = await session.execute(select(Organization).where(Organization.code == code.upper()))
        return result.scalars().first()

class SchoolService:
    @staticmethod
    async def create_school(
        session: AsyncSession,
        organization_id: uuid.UUID,
        name: str,
        code: str
    ) -> School:
        school = School(
            id=uuid.uuid4(),
            organization_id=organization_id,
            name=name,
            code=code.upper()
        )
        session.add(school)
        await session.commit()
        await session.refresh(school)
        return school

    @staticmethod
    async def list_schools(session: AsyncSession, organization_id: uuid.UUID) -> List[School]:
        result = await session.execute(
            select(School).where(School.organization_id == organization_id)
        )
        return list(result.scalars().all())
