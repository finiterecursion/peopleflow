"""Activity Checkins

Revision ID: 28e66d8c063f
Revises: 4071a0ce67ef
Create Date: 2014-02-11 02:48:32.297489

"""

# revision identifiers, used by Alembic.
revision = '28e66d8c063f'
down_revision = '4071a0ce67ef'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('activity_checkins',
    sa.Column('activity_id', sa.Integer(), nullable=True),
    sa.Column('participant_id', sa.Integer(), nullable=True),
    sa.Column('time', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['activity_id'], ['activity.id'], ),
    sa.ForeignKeyConstraint(['participant_id'], ['participant.id'], ),
    sa.PrimaryKeyConstraint()
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('activity_checkins')
    ### end Alembic commands ###
