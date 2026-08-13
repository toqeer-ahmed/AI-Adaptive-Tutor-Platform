"""004_document_ingestion

Revision ID: 004_document_ingestion
Revises: 003_curriculum_domain
Create Date: 2026-08-13 23:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '004_document_ingestion'
down_revision: Union[str, None] = '003_curriculum_domain'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Update source_documents table with new association & status columns
    op.add_column('source_documents', sa.Column('school_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('schools.id', ondelete='SET NULL'), nullable=True))
    op.add_column('source_documents', sa.Column('curriculum_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('curricula.id', ondelete='SET NULL'), nullable=True))
    op.add_column('source_documents', sa.Column('curriculum_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('curriculum_versions.id', ondelete='SET NULL'), nullable=True))
    op.add_column('source_documents', sa.Column('status', sa.String(50), nullable=False, server_default='UPLOADED'))
    op.add_column('source_documents', sa.Column('error_message', sa.Text(), nullable=True))
    op.add_column('source_documents', sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'))

    op.create_index('ix_source_documents_status', 'source_documents', ['status'])

    # 2. Document Chunks Table
    op.create_table(
        'document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('source_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('curriculum_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('curricula.id', ondelete='SET NULL'), nullable=True),
        sa.Column('curriculum_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('curriculum_versions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('section', sa.String(255), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('document_id', 'chunk_index', name='uq_document_chunk_index')
    )
    op.create_index('ix_document_chunks_doc', 'document_chunks', ['document_id'])
    op.create_index('ix_document_chunks_org', 'document_chunks', ['organization_id'])

    # Enable RLS on document_chunks
    op.execute("ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON document_chunks
        FOR ALL
        USING (
            organization_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
            OR current_setting('app.current_tenant_id', true) = 'ALL'
        );
    """)

def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON document_chunks;")
    op.execute("ALTER TABLE document_chunks DISABLE ROW LEVEL SECURITY;")

    op.drop_table('document_chunks')
    op.drop_column('source_documents', 'metadata_json')
    op.drop_column('source_documents', 'error_message')
    op.drop_column('source_documents', 'status')
    op.drop_column('source_documents', 'curriculum_version_id')
    op.drop_column('source_documents', 'curriculum_id')
    op.drop_column('source_documents', 'school_id')
