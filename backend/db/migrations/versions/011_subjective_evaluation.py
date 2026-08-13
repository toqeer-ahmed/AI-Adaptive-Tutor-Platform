"""011_subjective_evaluation

Revision ID: 011_subjective_evaluation
Revises: 010_misconceptions
Create Date: 2026-08-14 05:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '011_subjective_evaluation'
down_revision: Union[str, None] = '010_misconceptions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Add columns to student_answers
    op.add_column('student_answers', sa.Column('ai_evaluation_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('student_answers', sa.Column('evaluation_status', sa.String(50), nullable=False, server_default='AUTOGRADED'))
    op.create_index('ix_stud_ans_eval_status', 'student_answers', ['evaluation_status'])

    # 2. Subjective Evaluation Logs Table
    op.create_table(
        'subjective_evaluation_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('answer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('student_answers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('evaluator_type', sa.String(50), nullable=False, server_default='AI_PROPOSAL'),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('score_proposed', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('score_final', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('rubric_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()'))
    )

    op.create_index('ix_subj_eval_ans', 'subjective_evaluation_logs', ['answer_id'])

def downgrade() -> None:
    op.drop_table('subjective_evaluation_logs')
    op.drop_index('ix_stud_ans_eval_status', table_name='student_answers')
    op.drop_column('student_answers', 'evaluation_status')
    op.drop_column('student_answers', 'ai_evaluation_json')
