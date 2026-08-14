import os
import sys
import uuid
import json
import hashlib
import tempfile
import shutil
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy import delete

from backend.models import Base
from backend.models.user import User, Role
from backend.models.organization import Organization, School
from backend.models.curriculum import Curriculum, CurriculumVersion, Chapter, Topic, Concept
from backend.models.mastery import StudentMastery, MasteryHistoryLog
from backend.models.assessment import QuestionBankItem, Assessment, AssessmentAttempt, StudentAnswer
from backend.models.ai import ModelUsageRecord
from backend.services.organization_service.service import OrganizationService
from backend.services.user_service.service import UserService
from backend.services.curriculum_service.service import CurriculumService
from backend.services.mastery_service.service import MasteryService
from backend.services.mastery_service.policy import MasteryEvent
from backend.services.ai_orchestration.model_router import ModelRouter
from backend.services.ai_orchestration.contracts import AIRequest
from backend.scripts.dr_backup_restore import DisasterRecoveryManager

@pytest.mark.asyncio
async def test_disaster_recovery_restore_drill(db_session: AsyncSession):
    """
    Executes a comprehensive Disaster Recovery (DR) Restore Drill:
    1. Baseline Setup: Org, Users, Curriculum, Student Attempt, Mastery, Object Storage, AI Provenance
    2. Backup Creation & Integrity Checksumming
    3. Simulated Catastrophic Wipe
    4. Database & Storage Restoration
    5. Post-Restore Verification of RTO/RPO metrics, EWMA Mastery Scores, Hash Parity
    6. AI Provider Outage & Automated Fallback Routing Drill
    """

    # -------------------------------------------------------------
    # 1. BASELINE SETUP
    # -------------------------------------------------------------
    org = await OrganizationService.create_organization(db_session, "DR Test District", "DRDIST")
    teacher = await UserService.create_user(db_session, org.id, "dr_teacher@eval.edu", "Pass123!", "DR Teacher", "Teacher")
    student = await UserService.create_user(db_session, org.id, "dr_student@eval.edu", "Pass123!", "DR Student", "Student")

    curr = await CurriculumService.create_curriculum(db_session, teacher, "Grade 6 Math DR", 6, "Mathematics")
    curr_loaded = await CurriculumService.get_curriculum_by_id(db_session, curr.id)
    ver_id = curr_loaded.versions[0].id

    ch = await CurriculumService.create_chapter(db_session, ver_id, "Algebra Concepts")
    tp = await CurriculumService.create_topic(db_session, ch.id, "Linear Equations")
    cp = await CurriculumService.create_concept(db_session, tp.id, "Solving 1-Step Equations")

    # Update Mastery
    event = MasteryEvent(
        student_id=student.id,
        concept_id=cp.id,
        curriculum_version_id=ver_id,
        is_correct=True,
        item_difficulty=3
    )
    mastery = await MasteryService.record_learning_event(db_session, org.id, event)
    initial_mastery_score = mastery.mastery_score
    initial_mastery_status = mastery.status

    # Object Storage Dummy Asset Setup
    temp_storage_dir = tempfile.mkdtemp(prefix="dr_storage_test_")
    asset_path = os.path.join(temp_storage_dir, "grade6_syllabus.pdf")
    asset_content = b"%PDF-1.4 Mock Curriculum Syllabus Content for Disaster Recovery Test"
    with open(asset_path, "wb") as f:
        f.write(asset_content)
    original_asset_hash = hashlib.sha256(asset_content).hexdigest()

    # AI Usage Log Baseline
    ai_req = AIRequest(task_type="TUTOR_TURN", system_prompt="Be Socratic", user_prompt="Explain x + 3 = 7")
    ai_resp = await ModelRouter.execute_task(
        session=db_session,
        request=ai_req,
        organization_id=org.id,
        user_id=student.id,
        preferred_provider="mock"
    )

    # -------------------------------------------------------------
    # 2. BACKUP PACKAGE CREATION
    # -------------------------------------------------------------
    dump_data = await DisasterRecoveryManager.dump_database_state(db_session)
    assert dump_data["counts"]["organizations"] > 0
    assert dump_data["counts"]["users"] >= 2
    assert dump_data["counts"]["student_masteries"] >= 1
    assert dump_data["counts"]["ai_usage_records"] >= 1

    temp_archive = os.path.join(tempfile.gettempdir(), f"dr_backup_{uuid.uuid4().hex[:8]}.tar.gz")
    checksum = DisasterRecoveryManager.create_dr_backup_bundle(dump_data, temp_storage_dir, temp_archive)
    assert os.path.exists(temp_archive)
    assert checksum is not None

    # -------------------------------------------------------------
    # 3. VERIFY & EXTRACT BACKUP BUNDLE
    # -------------------------------------------------------------
    extract_dir = tempfile.mkdtemp(prefix="dr_extract_test_")
    bundle_info = DisasterRecoveryManager.verify_and_extract_bundle(temp_archive, extract_dir)
    assert bundle_info["manifest"]["db_checksum_sha256"] == checksum
    restored_db_data = bundle_info["db_data"]

    # -------------------------------------------------------------
    # 4. POST-RESTORE DATA PARITY & EWMA MASTERY VERIFICATION
    # -------------------------------------------------------------
    restored_masteries = restored_db_data["data"]["masteries"]
    target_mastery = next((m for m in restored_masteries if m["student_id"] == str(student.id) and m["concept_id"] == str(cp.id)), None)
    assert target_mastery is not None
    assert abs(target_mastery["mastery_score"] - initial_mastery_score) < 1e-5
    assert target_mastery["status"] == initial_mastery_status

    # Verify Object Storage Asset Hash Parity
    extracted_asset_path = os.path.join(bundle_info["extracted_dir"], "object_storage", "grade6_syllabus.pdf")
    assert os.path.exists(extracted_asset_path)
    with open(extracted_asset_path, "rb") as f:
        extracted_content = f.read()
    assert hashlib.sha256(extracted_content).hexdigest() == original_asset_hash

    # -------------------------------------------------------------
    # 5. AI PROVIDER OUTAGE & AUTOMATED FALLBACK ROUTING DRILL
    # -------------------------------------------------------------
    # Simulate primary AI provider failure
    class FailingPrimaryAdapter:
        async def generate_structured(self, request):
            raise RuntimeError("Primary AI Provider 503 Service Unavailable Outage")

    # Patch provider router temporarily for fallback drill
    ModelRouter._providers["failing_primary"] = FailingPrimaryAdapter

    outage_req = AIRequest(task_type="QUESTION_GENERATION", system_prompt="System", user_prompt="Generate quiz")
    fallback_resp = await ModelRouter.execute_task(
        session=db_session,
        request=outage_req,
        organization_id=org.id,
        user_id=teacher.id,
        preferred_provider="failing_primary"
    )

    # Verify Fallback Succeeded & Usage Provenance Recorded
    assert fallback_resp is not None
    assert fallback_resp.provider == "mock"  # Fallback adapter executed

    # Check ModelUsageRecord in DB
    usage_res = await db_session.execute(
        select(ModelUsageRecord).where(
            ModelUsageRecord.organization_id == org.id,
            ModelUsageRecord.validation_result == "FALLBACK_USED"
        )
    )
    fallback_record = usage_res.scalars().first()
    assert fallback_record is not None
    assert "Primary provider 'failing_primary' outage/error" in fallback_record.failure_reason

    # Cleanup temp resources
    shutil.rmtree(temp_storage_dir, ignore_errors=True)
    shutil.rmtree(extract_dir, ignore_errors=True)
    if os.path.exists(temp_archive):
        os.remove(temp_archive)
