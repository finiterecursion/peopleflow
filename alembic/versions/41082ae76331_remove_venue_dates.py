"""Remove Venue Dates

Revision ID: 41082ae76331
Revises: 4973d39adcb6
Create Date: 2014-02-10 06:19:54.964040

"""

# revision identifiers, used by Alembic.
revision = '41082ae76331'
down_revision = '4973d39adcb6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('venue', u'from_date')
    op.drop_column('venue', u'to_date')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('venue', sa.Column(u'to_date', sa.DATE(), nullable=True))
    op.add_column('venue', sa.Column(u'from_date', sa.DATE(), nullable=True))
    ### end Alembic commands ###
