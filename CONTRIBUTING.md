# Contributing Guidelines: AI Adaptive Education Platform

Thank you for contributing to the AI Adaptive Education Platform. This repository enforces strict architectural boundaries and security controls.

---

## 🔒 Mandatory Architectural Principles

1. **Modular Monolith**: Code MUST stay inside defined service modules (`backend/services/<module_name>`). Do not create cross-module circular imports.
2. **Deterministic Adaptation**: Deterministic mastery and adaptive learning logic (`student_model_service` and `adaptive_engine`) MUST NOT import or depend on LLM / AI Orchestration modules.
3. **No Hardcoded Secrets**: Secrets and provider keys MUST be retrieved via `backend.config.settings`.
4. **Tenant Isolation**: All tenant-scoped database queries MUST use `backend/api/deps.py` or execute `SET LOCAL app.current_tenant_id` to enforce PostgreSQL Row-Level Security (RLS).
5. **Typed Contracts**: All API endpoints MUST specify Pydantic request/response schemas.

---

## 🛠 Pull Request Checklist

Before submitting a Pull Request:
- [ ] Run `pytest` and verify all unit, integration, and security tests pass.
- [ ] Ensure cross-tenant isolation test `tests/security/test_tenant_isolation.py` passes 100%.
- [ ] Run `ruff check .` and fix all linting errors.
- [ ] Ensure database migrations are reversible (`upgrade` and `downgrade` both implemented).
- [ ] Verify no proprietary keys or `.env` files are committed.
