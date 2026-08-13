"""010_misconceptions

Revision ID: 010_misconceptions
Revises: 009_tutor_sessions
Create Date: 2026-08-14 04:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '010_misconceptions'
down_revision: Union[str, None] = '009_tutor_sessions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Misconception Taxonomies Table
    op.create_table(
        'misconception_taxonomies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('concept_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('concepts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(100), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('remediation_strategy', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )

    op.create_index('ix_misc_tax_org', 'misconception_taxonomies', ['organization_id'])
    op.create_index('ix_misc_tax_concept', 'misconception_taxonomies', ['concept_id'])
    op.create_index('ix_misc_tax_code', 'misconception_taxonomies', ['code'])

    # 2. Student Misconceptions Table
    op.create_table(
        'student_misconceptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('concept_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('concepts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('curriculum_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('curriculum_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('misconception_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('misconception_taxonomies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(50), nullable=False, server_default='DETECTED'),
        sa.Column('evidence', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('resolution_evidence', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('student_id', 'misconception_id', 'curriculum_version_id', name='uq_student_misconception_version')
    )

    op.create_index('ix_stud_misc_org', 'student_misconceptions', ['organization_id'])
    op.create_index('ix_stud_misc_student', 'student_misconceptions', ['student_id'])
    op.create_index('ix_stud_misc_status', 'student_misconceptions', ['status'])

    # Enable RLS
    for table in ['misconception_taxonomies', 'student_misconceptions']:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"""
            CREATE POLICY tenant_isolation_policy ON {table}
            FOR ALL
            USING (
                organization_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
                OR current_setting('app.current_tenant_id', true) = 'ALL'
            );
        """)

def downgrade() -> None:
    for table in ['misconception_taxonomies', 'student_misconceptions']:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.drop_table('student_misconceptions')
    op.drop_table('misconception_taxonomies')
