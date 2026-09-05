"""Add queue position to bookings.

Revision ID: 0002_add_booking_queue_position
Revises: 0001_initial_schema
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_add_booking_queue_position"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bookings", sa.Column("queue_position", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("bookings", "queue_position")
