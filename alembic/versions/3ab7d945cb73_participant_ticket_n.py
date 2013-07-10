"""Participant ticket number reintroduced

Revision ID: 3ab7d945cb73
Revises: 2514e39b5eaa
Create Date: 2013-07-10 18:31:32.771470

"""

# revision identifiers, used by Alembic.
revision = '3ab7d945cb73'
down_revision = '2514e39b5eaa'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('participant', sa.Column('ticket_number', sa.Unicode(length=15), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('participant', 'ticket_number')
    ### end Alembic commands ###