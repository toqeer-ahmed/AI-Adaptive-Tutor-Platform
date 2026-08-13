"""003_curriculum_domain

Revision ID: 003_curriculum_domain
Revises: 002_security_auth_multi_tenancy
Create Date: 2026-08-13 22:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '003_curriculum_domain'
down_revision: Union[str, None] = '002_security_auth_multi_tenancy'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Source Documents
    op.create_table(
        'source_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('uploaded_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(512), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )
    op.create_index('ix_source_documents_org', 'source_documents', ['organization_id'])

    # 2. Curricula
    op.create_table(
        'curricula',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('grade_level', sa.Integer(), nullable=False),
        sa.Column('subject_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )
    op.create_index('ix_curricula_org', 'curricula', ['organization_id'])
    op.create_index('ix_curricula_grade', 'curricula', ['grade_level'])
    op.create_index('ix_curricula_subject', 'curricula', ['subject_name'])

    # 3. Curriculum Versions
    op.create_table(
        'curriculum_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('curriculum_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('curricula.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='DRAFT'),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('approved_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('published_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('change_log', sa.Text(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('curriculum_id', 'version_number', name='uq_curriculum_version_number')
    )
    op.create_index('ix_curriculum_versions_curr', 'curriculum_versions', ['curriculum_id'])
    op.create_index('ix_curriculum_versions_status', 'curriculum_versions', ['status'])

    # 4. Chapters
    op.create_table(
        'chapters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('curriculum_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('curriculum_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sequence_order', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('source_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('source_documents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_page', sa.Integer(), nullable=True),
        sa.Column('source_section', sa.String(255), nullable=True),
        sa.Column('source_chunk_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )
    op.create_index('ix_chapters_version', 'chapters', ['curriculum_version_id'])

    # 5. Topics
    op.create_table(
        'topics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('chapter_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chapters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sequence_order', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('source_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('source_documents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_page', sa.Integer(), nullable=True),
        sa.Column('source_section', sa.String(255), nullable=True),
        sa.Column('source_chunk_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )
    op.create_index('ix_topics_chapter', 'topics', ['chapter_id'])

    # 6. Concepts
    op.create_table(
        'concepts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('topics.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('difficulty_level', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('sequence_order', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('source_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('source_documents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_page', sa.Integer(), nullable=True),
        sa.Column('source_section', sa.String(255), nullable=True),
        sa.Column('source_chunk_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )
    op.create_index('ix_concepts_topic', 'concepts', ['topic_id'])

    # 7. Skills
    op.create_table(
        'skills',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('concept_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('concepts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True)
    )
    op.create_index('ix_skills_concept', 'skills', ['concept_id'])

    # 8. Learning Objectives
    op.create_table(
        'learning_objectives',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('concept_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('concepts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('bloom_taxonomy_level', sa.String(50), nullable=False, server_default='Understand'),
        sa.Column('source_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('source_documents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_page', sa.Integer(), nullable=True),
        sa.Column('source_section', sa.String(255), nullable=True),
        sa.Column('source_chunk_id', sa.String(255), nullable=True)
    )
    op.create_index('ix_learning_objectives_concept', 'learning_objectives', ['concept_id'])

    # 9. Concept Prerequisites
    op.create_table(
        'concept_prerequisites',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('concept_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('concepts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('prerequisite_concept_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('concepts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relationship_type', sa.String(50), nullable=False, server_default='STRICT'),
        sa.UniqueConstraint('concept_id', 'prerequisite_concept_id', name='uq_concept_prerequisite')
    )

    # Enable RLS on top-level tenant entities
    for table in ['source_documents', 'curricula']:
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
    for table in ['source_documents', 'curricula']:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.drop_table('concept_prerequisites')
    op.drop_table('learning_objectives')
    op.drop_table('skills')
    op.drop_table('concepts')
    op.drop_table('topics')
    op.drop_table('chapters')
    op.drop_table('curriculum_versions')
    op.drop_table('curricula')
    op.drop_table('source_documents')
