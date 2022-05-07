"""empty message

Revision ID: 0b75c7627164
Revises: 63232a07f69e
Create Date: 2022-04-16 22:44:28.018332

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0b75c7627164'
down_revision = '63232a07f69e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user')
    op.drop_constraint(None, 'ports', type_='foreignkey')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key(None, 'ports', 'user', ['reserved_by'], ['id'])
    op.create_table('user',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=128), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###