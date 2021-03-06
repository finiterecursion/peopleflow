"""Participant.speaker

Revision ID: 12ad11a99786
Revises: 176920b5f38b
Create Date: 2014-02-09 03:28:14.110763

"""

# revision identifiers, used by Alembic.
revision = '12ad11a99786'
down_revision = '176920b5f38b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('participant', sa.Column('speaker', sa.Boolean(), server_default='False', nullable=False))
    op.alter_column('participant', 'speaker', server_default=None)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('participant', 'speaker')
    ### end Alembic commands ###
