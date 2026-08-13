"""008_student_mastery

Revision ID: 008_student_mastery
Revises: 007_assessment_engine
Create Date: 2026-08-14 02:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '008_student_mastery'
down_revision: Union[str, None] = '007_assessment_engine'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Student Mastery Table
    op.create_table(
        'student_mastery',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('concept_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('concepts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('curriculum_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('curriculum_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('mastery_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('correct_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('incorrect_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('recent_performance', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('historical_performance', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('average_response_time', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('last_difficulty', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('status', sa.String(50), nullable=False, server_default='NOT_STARTED'),
        sa.Column('misconception_tags', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('last_practiced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_review_due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('student_id', 'concept_id', 'curriculum_version_id', name='uq_student_concept_version')
    )

    op.create_index('ix_sm_org', 'student_mastery', ['organization_id'])
    op.create_index('ix_sm_student', 'student_mastery', ['student_id'])
    op.create_index('ix_sm_concept', 'student_mastery', ['concept_id'])
    op.create_index('ix_sm_status', 'student_mastery', ['status'])

    # 2. Mastery History Logs Table
    op.create_table(
        'mastery_history_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('student_mastery_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('student_mastery.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('concept_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('concepts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('curriculum_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('curriculum_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('policy_version', sa.String(50), nullable=False, server_default='v1.0'),
        sa.Column('event_type', sa.String(50), nullable=False, server_default='ASSESSMENT_ATTEMPT'),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('item_difficulty', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('previous_mastery', sa.Float(), nullable=False),
        sa.Column('new_mastery', sa.Float(), nullable=False),
        sa.Column('previous_status', sa.String(50), nullable=False),
        sa.Column('new_status', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )

    op.create_index('ix_mhl_student', 'mastery_history_logs', ['student_id'])

    # Enable RLS
    op.execute("ALTER TABLE student_mastery ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON student_mastery
        FOR ALL
        USING (
            organization_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
            OR current_setting('app.current_tenant_id', true) = 'ALL'
        );
    """)

def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON student_mastery;")
    op.execute("ALTER TABLE student_mastery DISABLE ROW LEVEL SECURITY;")
    op.drop_table('mastery_history_logs')
    op.drop_table('student_mastery')
