"""Create upload table

Revision ID: <new_revision_id>
Revises: None
Create Date: 2025-01-02

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '<new_revision_id>'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create the 'upload' table
    op.create_table(
        'upload',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('total_premium', sa.Float, nullable=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    )


def downgrade():
    # Drop the 'upload' table
    op.drop_table('upload')