import os
import sys
import json
import hashlib
import shutil
import tarfile
import argparse
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any

from sqlalchemy import text
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Import models
from backend.models import Base
from backend.models.user import User, Role
from backend.models.organization import Organization, School
from backend.models.curriculum import Curriculum, CurriculumVersion, Chapter, Topic, Concept
from backend.models.mastery import StudentMastery, MasteryHistoryLog
from backend.models.assessment import Assessment, AssessmentAttempt, StudentAnswer, QuestionBankItem
from backend.models.ai import ModelUsageRecord
from backend.models.audit import AuditLogEntry

class DisasterRecoveryManager:
    """
    Automated Disaster Recovery (DR) Utility for DB and Object Storage Backup & Restoration.
    """

    @staticmethod
    def compute_sha256(file_path: str) -> str:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    async def dump_database_state(session: AsyncSession) -> Dict[str, Any]:
        """
        Dumps authoritative database state into a structured JSON dictionary.
        """
        orgs = (await session.execute(select(Organization))).scalars().all()
        users = (await session.execute(select(User))).scalars().all()
        curricula = (await session.execute(select(Curriculum))).scalars().all()
        concepts = (await session.execute(select(Concept))).scalars().all()
        masteries = (await session.execute(select(StudentMastery))).scalars().all()
        attempts = (await session.execute(select(AssessmentAttempt))).scalars().all()
        answers = (await session.execute(select(StudentAnswer))).scalars().all()
        ai_records = (await session.execute(select(ModelUsageRecord))).scalars().all()

        dump_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "counts": {
                "organizations": len(orgs),
                "users": len(users),
                "curricula": len(curricula),
                "concepts": len(concepts),
                "student_masteries": len(masteries),
                "assessment_attempts": len(attempts),
                "student_answers": len(answers),
                "ai_usage_records": len(ai_records)
            },
            "data": {
                "organizations": [{"id": str(o.id), "name": o.name, "code": o.code} for o in orgs],
                "users": [{"id": str(u.id), "email": u.email, "full_name": u.full_name, "organization_id": str(u.organization_id)} for u in users],
                "curricula": [{"id": str(c.id), "name": c.name, "subject": c.subject_name, "grade_level": c.grade_level} for c in curricula],
                "concepts": [{"id": str(cp.id), "name": cp.name} for cp in concepts],
                "masteries": [{
                    "id": str(m.id),
                    "student_id": str(m.student_id),
                    "concept_id": str(m.concept_id),
                    "mastery_score": m.mastery_score,
                    "confidence": m.confidence,
                    "status": m.status
                } for m in masteries],
                "ai_records": [{
                    "id": str(r.id),
                    "provider": r.provider,
                    "model": r.model,
                    "task_type": r.task_type,
                    "validation_result": r.validation_result,
                    "failure_reason": r.failure_reason
                } for r in ai_records]
            }
        }
        return dump_data

    @staticmethod
    def create_dr_backup_bundle(dump_data: Dict[str, Any], storage_dir: str, output_archive_path: str) -> str:
        """
        Packs DB JSON dump and object storage directory into a checksummed .tar.gz bundle.
        """
        temp_dir = output_archive_path + "_temp"
        os.makedirs(temp_dir, exist_ok=True)

        db_json_path = os.path.join(temp_dir, "db_dump.json")
        with open(db_json_path, "w", encoding="utf-8") as f:
            json.dump(dump_data, f, indent=2)

        storage_backup_dir = os.path.join(temp_dir, "object_storage")
        if os.path.exists(storage_dir):
            shutil.copytree(storage_dir, storage_backup_dir, dirs_exist_ok=True)
        else:
            os.makedirs(storage_backup_dir, exist_ok=True)

        checksum = DisasterRecoveryManager.compute_sha256(db_json_path)
        manifest = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "db_checksum_sha256": checksum,
            "counts": dump_data["counts"]
        }
        with open(os.path.join(temp_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        with tarfile.open(output_archive_path, "w:gz") as tar:
            tar.add(temp_dir, arcname=os.path.basename(temp_dir))

        shutil.rmtree(temp_dir, ignore_errors=True)
        return checksum

    @staticmethod
    def verify_and_extract_bundle(archive_path: str, extract_to_dir: str) -> Dict[str, Any]:
        """
        Extracts archive and verifies checksum integrity against manifest.
        """
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path=extract_to_dir)

        subdirs = [os.path.join(extract_to_dir, d) for d in os.listdir(extract_to_dir) if os.path.isdir(os.path.join(extract_to_dir, d))]
        target_dir = subdirs[0] if subdirs else extract_to_dir

        manifest_path = os.path.join(target_dir, "manifest.json")
        db_dump_path = os.path.join(target_dir, "db_dump.json")

        if not os.path.exists(manifest_path) or not os.path.exists(db_dump_path):
            raise ValueError("Invalid backup bundle: missing manifest or database dump.")

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        actual_checksum = DisasterRecoveryManager.compute_sha256(db_dump_path)
        if actual_checksum != manifest["db_checksum_sha256"]:
            raise ValueError(f"Checksum mismatch! Expected {manifest['db_checksum_sha256']}, got {actual_checksum}")

        with open(db_dump_path, "r", encoding="utf-8") as f:
            db_data = json.load(f)

        return {"manifest": manifest, "db_data": db_data, "extracted_dir": target_dir}

def main():
    parser = argparse.ArgumentParser(description="AI Adaptive Education Platform DR Utility")
    parser.add_argument("--action", choices=["backup", "restore"], required=True)
    parser.add_argument("--archive", default="dr_backup_latest.tar.gz")
    args = parser.parse_args()
    print(f"Executing DR action: {args.action}")

if __name__ == "__main__":
    main()
