"""006_vector_embeddings

Revision ID: 006_vector_embeddings
Revises: 005_model_usage
Create Date: 2026-08-14 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '006_vector_embeddings'
down_revision: Union[str, None] = '005_model_usage'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Enable pgvector extension if available
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Vector Table
    op.create_table(
        'curriculum_vector_embeddings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('chunk_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('document_chunks.id', ondelete='CASCADE'), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('schools.id', ondelete='SET NULL'), nullable=True),
        sa.Column('curriculum_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('curricula.id', ondelete='CASCADE'), nullable=False),
        sa.Column('curriculum_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('curriculum_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('grade', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(100), nullable=False),
        sa.Column('chapter', sa.String(255), nullable=True),
        sa.Column('topic', sa.String(255), nullable=True),
        sa.Column('concept', sa.String(255), nullable=True),
        sa.Column('learning_objective', sa.String(255), nullable=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('source_documents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('section', sa.String(255), nullable=True),
        sa.Column('text_content', sa.Text(), nullable=False),
        sa.Column('approval_status', sa.String(50), nullable=False, server_default='PUBLISHED'),
        sa.Column('embedding_model', sa.String(100), nullable=False, server_default='text-embedding-3-small'),
        sa.Column('embedding_dimension', sa.Integer(), nullable=False, server_default='1536'),
        sa.Column('embedding_version', sa.String(50), nullable=False, server_default='v1.0'),
        sa.Column('embedding_vector', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )

    op.create_index('ix_vec_org', 'curriculum_vector_embeddings', ['organization_id'])
    op.create_index('ix_vec_status', 'curriculum_vector_embeddings', ['approval_status'])
    op.create_index('ix_vec_curr', 'curriculum_vector_embeddings', ['curriculum_id'])

    # Enable RLS on curriculum_vector_embeddings
    op.execute("ALTER TABLE curriculum_vector_embeddings ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON curriculum_vector_embeddings
        FOR ALL
        USING (
            organization_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
            OR current_setting('app.current_tenant_id', true) = 'ALL'
        );
    """)

def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON curriculum_vector_embeddings;")
    op.execute("ALTER TABLE curriculum_vector_embeddings DISABLE ROW LEVEL SECURITY;")
    op.drop_table('curriculum_vector_embeddings')
