"""009_tutor_sessions

Revision ID: 009_tutor_sessions
Revises: 008_student_mastery
Create Date: 2026-08-14 03:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '009_tutor_sessions'
down_revision: Union[str, None] = '008_student_mastery'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Tutor Sessions Table
    op.create_table(
        'tutor_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('concept_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('concepts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('curriculum_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('curriculum_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('current_mode', sa.String(50), nullable=False, server_default='explanation'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )

    op.create_index('ix_tutor_sess_org', 'tutor_sessions', ['organization_id'])
    op.create_index('ix_tutor_sess_student', 'tutor_sessions', ['student_id'])
    op.create_index('ix_tutor_sess_concept', 'tutor_sessions', ['concept_id'])

    # 2. Tutor Turns Table
    op.create_table(
        'tutor_turns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tutor_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_message', sa.Text(), nullable=False),
        sa.Column('tutor_response', sa.Text(), nullable=False),
        sa.Column('mode', sa.String(50), nullable=False),
        sa.Column('sources_cited', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('token_usage', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )

    op.create_index('ix_tutor_turns_sess', 'tutor_turns', ['session_id'])

    # Enable RLS
    op.execute("ALTER TABLE tutor_sessions ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON tutor_sessions
        FOR ALL
        USING (
            organization_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
            OR current_setting('app.current_tenant_id', true) = 'ALL'
        );
    """)

def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON tutor_sessions;")
    op.execute("ALTER TABLE tutor_sessions DISABLE ROW LEVEL SECURITY;")
    op.drop_table('tutor_turns')
    op.drop_table('tutor_sessions')
