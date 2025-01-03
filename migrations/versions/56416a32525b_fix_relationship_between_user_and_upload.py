from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '56416a32525b'
down_revision = 'b653a3ea6ec4'
branch_labels = None
depends_on = None


def upgrade():
    # Create the foreign key if it doesn't already exist
    op.create_foreign_key(
        'fk_user_upload',  # Name of the foreign key constraint
        'upload',          # Table containing the foreign key
        'user',            # Referenced table
        ['user_id'],       # Column(s) in this table
        ['id'],            # Column(s) in the referenced table
        ondelete='CASCADE' # On delete cascade
    )


def downgrade():
    # Drop the foreign key constraint
    op.drop_constraint('fk_user_upload', 'upload', type_='foreignkey')