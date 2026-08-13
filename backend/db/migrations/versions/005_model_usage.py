"""005_model_usage

Revision ID: 005_model_usage
Revises: 004_document_ingestion
Create Date: 2026-08-13 23:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '005_model_usage'
down_revision: Union[str, None] = '004_document_ingestion'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'model_usage',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('task_type', sa.String(100), nullable=False),
        sa.Column('prompt_version', sa.String(50), nullable=False, server_default='v1.0'),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completion_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('latency_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cost_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('validation_result', sa.String(50), nullable=False, server_default='PASSED'),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )
    op.create_index('ix_model_usage_org', 'model_usage', ['organization_id'])
    op.create_index('ix_model_usage_task', 'model_usage', ['task_type'])

    # Enable RLS on model_usage
    op.execute("ALTER TABLE model_usage ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON model_usage
        FOR ALL
        USING (
            organization_id IS NULL
            OR organization_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
            OR current_setting('app.current_tenant_id', true) = 'ALL'
        );
    """)

def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON model_usage;")
    op.execute("ALTER TABLE model_usage DISABLE ROW LEVEL SECURITY;")
    op.drop_table('model_usage')
