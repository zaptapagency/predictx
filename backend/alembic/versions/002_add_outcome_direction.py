"""Add Model.outcome_direction

Direction (does a high score mean risk or opportunity?) used to be inferred
at read time from model_type: CHURN and NPS were treated as risk, everything
else as opportunity. That broke once training accepted any label column --
a model trained on e.g. "profitable" defaulted to model_type=churn and so
was read backwards, inverting Heatmap health scores and firing Actions on
the best customers instead of the worst.

This repo's Alembic chain is already behind app/main.py's create_all fallback
-- migration 001 never created the models table at all, only SaaS tables, so
on any environment where alembic runs before that table exists this migration
fails and is swallowed (main.py logs it as a warning, does not crash the boot),
then create_all builds the table with this column already on it. That gap
predates this change; this migration only matters where models already
exists, which is the real production database.

This migration adds the column with a default so existing rows do not error,
then backfills it to reproduce the exact old risk/opportunity split -- so no
already-trained production model changes behaviour from this migration alone.

Enum labels are the Python member NAMES ('RISK', 'OPPORTUNITY'), matching
SQLAlchemy's default Enum(SomeEnum) storage -- verified against how
model_type is actually written ('CHURN', not 'churn'), not assumed.

Revision ID: 002
Revises: 001
Create Date: 2026-08-29 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

outcome_direction_enum = postgresql.ENUM(
    'RISK', 'OPPORTUNITY', name='outcomedirection', create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    outcome_direction_enum.create(bind, checkfirst=True)

    op.add_column(
        'models',
        sa.Column(
            'outcome_direction', outcome_direction_enum,
            nullable=False, server_default='RISK',
        ),
    )

    # Reproduce the old model_type -> direction mapping exactly (member names,
    # matching how model_type is actually stored), so existing rows keep
    # behaving the way they already did.
    op.execute(
        "UPDATE models SET outcome_direction = 'OPPORTUNITY' "
        "WHERE model_type IN ('OPPORTUNITY', 'EXPANSION', 'HEALTH')"
    )


def downgrade() -> None:
    op.drop_column('models', 'outcome_direction')
    outcome_direction_enum.drop(op.get_bind(), checkfirst=True)
