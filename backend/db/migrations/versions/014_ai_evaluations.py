"""014_ai_evaluations

Revision ID: 014_ai_evaluations
Revises: 013_notifications
Create Date: 2026-08-14 08:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '014_ai_evaluations'
down_revision: Union[str, None] = '013_notifications'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. AI Evaluation Datasets Table
    op.create_table(
        'ai_eval_datasets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('dataset_name', sa.String(100), nullable=False),
        sa.Column('version', sa.String(50), nullable=False, server_default='v1.0'),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('items_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )

    op.create_index('ix_ai_eval_ds_org', 'ai_eval_datasets', ['organization_id'])
    op.create_index('ix_ai_eval_ds_name', 'ai_eval_datasets', ['dataset_name'])
    op.create_index('ix_ai_eval_ds_cat', 'ai_eval_datasets', ['category'])

    # 2. AI Evaluation Runs Table
    op.create_table(
        'ai_eval_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('prompt_version', sa.String(50), nullable=False),
        sa.Column('dataset_version', sa.String(50), nullable=False, server_default='v1.0'),
        sa.Column('overall_accuracy', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('category_scores_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('failures_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('passed_release_gate', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )

    op.create_index('ix_ai_eval_runs_org', 'ai_eval_runs', ['organization_id'])
    op.create_index('ix_ai_eval_runs_model', 'ai_eval_runs', ['model_name'])
    op.create_index('ix_ai_eval_runs_passed', 'ai_eval_runs', ['passed_release_gate'])

    # Enable RLS
    for table in ['ai_eval_datasets', 'ai_eval_runs']:
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
    for table in ['ai_eval_datasets', 'ai_eval_runs']:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.drop_table('ai_eval_runs')
    op.drop_table('ai_eval_datasets')
