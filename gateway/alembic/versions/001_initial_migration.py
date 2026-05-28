"""initial_migration

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('workflow_runs',
                    sa.Column('id', sa.String(), nullable=False),
                    sa.Column('workflow_name', sa.String(), nullable=False),
                    sa.Column('status', sa.String(), server_default='PENDING'),
                    sa.Column('input_data', sa.JSON(), nullable=False),
                    sa.Column('output_data', sa.JSON(), nullable=True),
                    sa.Column('error_msg', sa.Text(), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('started_at', sa.DateTime(), nullable=True),
                    sa.Column('finished_at', sa.DateTime(), nullable=True),
                    sa.Column('total_cost_usd', sa.Float(), server_default='0.0'),
                    sa.Column('progress', sa.Integer(), server_default='0'),
                    sa.PrimaryKeyConstraint('id')
                    )

    op.create_table('llm_call_logs',
                    sa.Column('id', sa.String(), nullable=False),
                    sa.Column('run_id', sa.String(), nullable=True),
                    sa.Column('model', sa.String(), nullable=False),
                    sa.Column('prompt_tokens', sa.Integer(), server_default='0'),
                    sa.Column('completion_tokens', sa.Integer(), server_default='0'),
                    sa.Column('total_tokens', sa.Integer(), server_default='0'),
                    sa.Column('cost_usd', sa.Float(), server_default='0.0'),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )


def downgrade() -> None:
    op.drop_table('llm_call_logs')
    op.drop_table('workflow_runs')