import os
import sys
import asyncio
import time
import math
import uuid
import statistics
from typing import List, Dict, Any
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.future import select

# Set up SQLite in-memory engine for performance load test
@compiles(JSONB, 'sqlite')
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

TEST_DATABASE_URL = "sqlite+aiosqlite:///file:memdb_perf?mode=memory&cache=shared"
engine_test = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
AsyncSessionTest = async_sessionmaker(engine_test, class_=AsyncSession, expire_on_commit=False)

from backend.models import Base, Role, Organization
from backend.api.main import app
from backend.api.deps import get_db
from backend.services.organization_service.service import OrganizationService, SchoolService
from backend.services.user_service.service import UserService, ClassService
from backend.services.curriculum_service.service import CurriculumService
from backend.services.assessment_service.service import AssessmentService
from backend.services.mastery_service.service import MasteryService
from backend.services.mastery_service.policy import MasteryEvent
from backend.services.tutor_service.service import TutorService
from backend.services.analytics_service.service import AnalyticsAggregationService
from backend.services.notification_service.service import NotificationService
from backend.models.assessment import QuestionBankItem

async def override_get_db():
    async with AsyncSessionTest() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

def calculate_percentiles(latencies: List[float]) -> Dict[str, float]:
    if not latencies:
        return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "avg": 0.0}
    sorted_lat = sorted(latencies)
    n = len(sorted_lat)
    return {
        "p50": round(sorted_lat[int(n * 0.50)], 2),
        "p95": round(sorted_lat[min(int(n * 0.95), n - 1)], 2),
        "p99": round(sorted_lat[min(int(n * 0.99), n - 1)], 2),
        "avg": round(statistics.mean(sorted_lat), 2)
    }

async def benchmark_workload(
    name: str,
    coro_func,
    concurrency: int = 20,
    iterations: int = 100
) -> Dict[str, Any]:
    latencies = []
    errors = 0
    start_total = time.perf_counter()

    async def worker(num_ops: int):
        nonlocal errors
        for _ in range(num_ops):
            t0 = time.perf_counter()
            try:
                await coro_func()
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                latencies.append(elapsed_ms)
            except Exception as e:
                errors += 1

    ops_per_worker = max(1, iterations // concurrency)
    tasks = [asyncio.create_task(worker(ops_per_worker)) for _ in range(concurrency)]
    await asyncio.gather(*tasks)

    total_time = time.perf_counter() - start_total
    rps = round(len(latencies) / total_time, 2) if total_time > 0 else 0.0
    err_rate = round((errors / (iterations or 1)) * 100, 2)
    pcts = calculate_percentiles(latencies)

    return {
        "workload": name,
        "total_requests": len(latencies) + errors,
        "successful_requests": len(latencies),
        "errors": errors,
        "error_rate_pct": err_rate,
        "rps": rps,
        "p50_ms": pcts["p50"],
        "p95_ms": pcts["p95"],
        "p99_ms": pcts["p99"],
        "avg_ms": pcts["avg"]
    }

async def run_production_load_tests():
    print("\n=======================================================")
    print("      PRODUCTION PERFORMANCE BENCHMARK SUITE          ")
    print("=======================================================\n")

    # Initialize tables and roles safely
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionTest() as session:
        roles = ["SuperAdmin", "OrgAdmin", "SchoolAdmin", "Teacher", "Student", "Parent", "Support"]
        for r_name in roles:
            r_exist = (await session.execute(select(Role).where(Role.name == r_name))).scalars().first()
            if not r_exist:
                session.add(Role(id=uuid.uuid4(), name=r_name, description=r_name))
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Seed test data safely with dynamic suffix
        perf_code = f"PERF{uuid.uuid4().hex[:4].upper()}"
        async with AsyncSessionTest() as session:
            org = await OrganizationService.create_organization(session, "Perf Org", perf_code)
            teacher = await UserService.create_user(session, org.id, f"teacher_{perf_code.lower()}@perf.edu", "Pass123!", "Perf Teacher", "Teacher")
            student = await UserService.create_user(session, org.id, f"student_{perf_code.lower()}@perf.edu", "Pass123!", "Perf Student", "Student")
            school = await SchoolService.create_school(session, org.id, "Perf School", f"SCH{perf_code}")
            cls = await ClassService.create_class(session, org.id, school.id, teacher.id, "Perf Math 6", 6, "2026")
            await ClassService.enroll_student(session, org.id, cls.id, student.id)

            created_curr = await CurriculumService.create_curriculum(session, teacher, "Perf Curriculum", 6, "Math")
            curr = await CurriculumService.get_curriculum_by_id(session, created_curr.id)
            ver_id = curr.versions[0].id

            ch = await CurriculumService.create_chapter(session, ver_id, "Perf Chapter")
            tp = await CurriculumService.create_topic(session, ch.id, "Perf Topic")
            cp = await CurriculumService.create_concept(session, tp.id, "Perf Concept")

            item = QuestionBankItem(
                id=uuid.uuid4(),
                organization_id=org.id,
                concept_id=cp.id,
                curriculum_version_id=ver_id,
                created_by_id=teacher.id,
                question_text="What is 2+2?",
                question_type="MULTIPLE_CHOICE",
                correct_answer_json="4",
                options_json=["2", "3", "4", "5"],
                difficulty=1,
                validation_status="APPROVED"
            )
            session.add(item)
            await session.commit()

            ass = await AssessmentService.create_assessment(
                session=session,
                creator=teacher,
                title="Perf Assessment",
                class_id=cls.id,
                question_ids=[item.id]
            )

        # Login to get JWT header
        login_res = await client.post("/api/v1/auth/login", json={"email": teacher.email, "password": "Pass123!"})
        t_token = login_res.json()["data"]["access_token"]
        t_headers = {"Authorization": f"Bearer {t_token}"}

        s_login = await client.post("/api/v1/auth/login", json={"email": student.email, "password": "Pass123!"})
        s_token = s_login.json()["data"]["access_token"]
        s_headers = {"Authorization": f"Bearer {s_token}"}

        # 1. Authentication Workload
        async def auth_task():
            res = await client.get("/api/v1/auth/me", headers=t_headers)
            assert res.status_code == 200

        res_auth = await benchmark_workload("1. Authentication", auth_task, concurrency=10, iterations=50)

        # 2. Curriculum Retrieval Workload
        async def curr_task():
            res = await client.get("/api/v1/curricula", headers=t_headers)
            assert res.status_code == 200

        res_curr = await benchmark_workload("2. Curriculum Retrieval", curr_task, concurrency=10, iterations=50)

        # 3. RAG Retrieval Workload
        async def rag_task():
            res = await client.post("/api/v1/rag/query", json={"query": "Perf Chapter", "grade": 6, "subject": "Math"}, headers=s_headers)
            assert res.status_code == 200

        res_rag = await benchmark_workload("3. RAG Retrieval", rag_task, concurrency=10, iterations=50)

        # 4. Assessment Submission Workload
        async def assess_task():
            async with AsyncSessionTest() as sess:
                st = await UserService.create_user(sess, org.id, f"s_{uuid.uuid4().hex[:6]}@perf.edu", "Pass123!", "Stud", "Student")
                attempt = await AssessmentService.start_attempt(sess, ass.id, st)
                await AssessmentService.submit_answer(sess, attempt.id, item.id, "4")
                graded = await AssessmentService.submit_attempt(sess, attempt.id)
                assert graded.status == "GRADED"

        res_assess = await benchmark_workload("4. Assessment Submission", assess_task, concurrency=5, iterations=20)

        # 5. Mastery Updates Workload
        async def mastery_task():
            async with AsyncSessionTest() as sess:
                ev = MasteryEvent(student_id=student.id, concept_id=cp.id, curriculum_version_id=ver_id, is_correct=True, item_difficulty=3)
                m = await MasteryService.record_learning_event(sess, org.id, ev)
                assert m.mastery_score > 0.0

        res_mastery = await benchmark_workload("5. Mastery Updates", mastery_task, concurrency=10, iterations=50)

        # 6. Teacher Dashboard Analytics Workload
        async def teacher_dash_task():
            res = await client.get(f"/api/v1/analytics/class/{cls.id}", headers=t_headers)
            assert res.status_code == 200

        res_tdash = await benchmark_workload("6. Teacher Dashboard", teacher_dash_task, concurrency=10, iterations=50)

        # 7. Student Dashboard Workload
        async def student_dash_task():
            res = await client.get(f"/api/v1/mastery/student/{student.id}", headers=s_headers)
            assert res.status_code == 200

        res_sdash = await benchmark_workload("7. Student Dashboard", student_dash_task, concurrency=10, iterations=50)

        # 8. Concurrent AI Tutor Requests Workload (Session per turn)
        async def tutor_task():
            async with AsyncSessionTest() as sess:
                ts = await TutorService.create_session(sess, student, cp.id, ver_id, "explanation")
                sid = str(ts.id)
            res = await client.post(
                "/api/v1/tutor/turn",
                json={"session_id": sid, "student_message": "Can you explain this step?", "mode": "explanation", "provider": "mock"},
                headers=s_headers
            )
            assert res.status_code == 200

        res_tutor = await benchmark_workload("8. Concurrent AI Tutor", tutor_task, concurrency=10, iterations=50)

        # 9. Celery Background Worker Task Processing Workload
        async def worker_task():
            async with AsyncSessionTest() as sess:
                res = await NotificationService.dispatch_notification(
                    session=sess,
                    recipient_user=student,
                    notification_type="ASSIGNMENT_DUE",
                    channel="in_app",
                    template_params={"title": "Math Quiz Due", "due_date": "Tomorrow"}
                )
                assert res.status in ["SENT", "QUEUED"]

        res_worker = await benchmark_workload("9. Celery Workers", worker_task, concurrency=10, iterations=50)

        # 10. Database Connection Pool Workload
        async def db_pool_task():
            async with AsyncSessionTest() as sess:
                res = await sess.execute(select(Role))
                assert len(res.scalars().all()) > 0

        res_db = await benchmark_workload("10. Database Pool", db_pool_task, concurrency=20, iterations=100)

        all_res = [res_auth, res_curr, res_rag, res_assess, res_mastery, res_tdash, res_sdash, res_tutor, res_worker, res_db]

        print("\n" + "="*85)
        print(f"{'Workload':<25} | {'p50 (ms)':<8} | {'p95 (ms)':<8} | {'p99 (ms)':<8} | {'RPS':<7} | {'Err %':<6}")
        print("="*85)
        for r in all_res:
            print(f"{r['workload']:<25} | {r['p50_ms']:<8} | {r['p95_ms']:<8} | {r['p99_ms']:<8} | {r['rps']:<7} | {r['error_rate_pct']:<6}")
        print("="*85 + "\n")

if __name__ == "__main__":
    asyncio.run(run_production_load_tests())
