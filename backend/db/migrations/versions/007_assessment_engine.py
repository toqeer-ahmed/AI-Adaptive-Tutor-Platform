"""007_assessment_engine

Revision ID: 007_assessment_engine
Revises: 006_vector_embeddings
Create Date: 2026-08-14 01:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '007_assessment_engine'
down_revision: Union[str, None] = '006_vector_embeddings'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Question Bank Items
    op.create_table(
        'question_bank_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('curriculum_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('curriculum_versions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('learning_objective_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('learning_objectives.id', ondelete='SET NULL'), nullable=True),
        sa.Column('concept_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('concepts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('skill_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skills.id', ondelete='SET NULL'), nullable=True),
        sa.Column('difficulty', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('question_type', sa.String(50), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('options_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('correct_answer_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('rubric_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('source_reference', sa.String(255), nullable=True),
        sa.Column('generation_method', sa.String(50), nullable=False, server_default='MANUAL'),
        sa.Column('validation_status', sa.String(50), nullable=False, server_default='PROPOSED'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )
    op.create_index('ix_qbank_org', 'question_bank_items', ['organization_id'])
    op.create_index('ix_qbank_type', 'question_bank_items', ['question_type'])
    op.create_index('ix_qbank_status', 'question_bank_items', ['validation_status'])

    # 2. Assessments
    op.create_table(
        'assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('schools.id', ondelete='SET NULL'), nullable=True),
        sa.Column('class_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classes.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('assessment_type', sa.String(50), nullable=False, server_default='QUIZ'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('time_limit_minutes', sa.Integer(), nullable=True),
        sa.Column('available_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )
    op.create_index('ix_assessments_org', 'assessments', ['organization_id'])
    op.create_index('ix_assessments_class', 'assessments', ['class_id'])

    # 3. Assessment Questions
    op.create_table(
        'assessment_questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assessments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('question_bank_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sequence_order', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('points', sa.Float(), nullable=False, server_default='1.0')
    )
    op.create_index('ix_ass_q_ass', 'assessment_questions', ['assessment_id'])

    # 4. Assessment Attempts
    op.create_table(
        'assessment_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assessments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(50), nullable=False, server_default='IN_PROGRESS'),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('max_score', sa.Float(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index('ix_ass_att_ass', 'assessment_attempts', ['assessment_id'])
    op.create_index('ix_ass_att_student', 'assessment_attempts', ['student_id'])

    # 5. Student Answers
    op.create_table(
        'student_answers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('attempt_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assessment_attempts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('question_bank_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('submitted_answer_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('points_awarded', sa.Float(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('teacher_override', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('answered_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )
    op.create_index('ix_stud_ans_att', 'student_answers', ['attempt_id'])

    # Enable RLS
    for table in ['question_bank_items', 'assessments']:
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
    for table in ['question_bank_items', 'assessments']:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.drop_table('student_answers')
    op.drop_table('assessment_attempts')
    op.drop_table('assessment_questions')
    op.drop_table('assessments')
    op.drop_table('question_bank_items')
