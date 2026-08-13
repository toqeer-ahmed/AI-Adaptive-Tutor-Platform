"""012_analytics_provenance

Revision ID: 012_analytics_provenance
Revises: 011_subjective_evaluation
Create Date: 2026-08-14 06:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '012_analytics_provenance'
down_revision: Union[str, None] = '011_subjective_evaluation'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'analytics_summary_provenance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('summary_type', sa.String(100), nullable=False),
        sa.Column('source_metric_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('generated_summary_text', sa.Text(), nullable=False),
        sa.Column('ai_model_name', sa.String(100), nullable=False, server_default='gpt-4o-mini'),
        sa.Column('prompt_hash', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )

    op.create_index('ix_analytics_prov_org', 'analytics_summary_provenance', ['organization_id'])
    op.create_index('ix_analytics_prov_type', 'analytics_summary_provenance', ['summary_type'])

    # Enable RLS
    op.execute("ALTER TABLE analytics_summary_provenance ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON analytics_summary_provenance
        FOR ALL
        USING (
            organization_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
            OR current_setting('app.current_tenant_id', true) = 'ALL'
        );
    """)

def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON analytics_summary_provenance;")
    op.execute("ALTER TABLE analytics_summary_provenance DISABLE ROW LEVEL SECURITY;")
    op.drop_table('analytics_summary_provenance')
