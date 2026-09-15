"""Human-readable report codes, severity normalization and auditable milestones."""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"


def upgrade():
    op.execute("CREATE SEQUENCE report_public_code_seq START WITH 1")
    op.add_column("reports", sa.Column("public_code", sa.String(20), nullable=True))
    op.execute(
        "UPDATE reports SET public_code = 'CQ-MUM-' || "
        "lpad(nextval('report_public_code_seq')::text, 6, '0')"
    )
    op.alter_column(
        "reports",
        "public_code",
        nullable=False,
        server_default=sa.text(
            "'CQ-MUM-' || lpad(nextval('report_public_code_seq')::text, 6, '0')"
        ),
    )
    op.create_index("ix_reports_public_code", "reports", ["public_code"], unique=True)
    op.execute("UPDATE reports SET severity = LEAST(3, GREATEST(1, severity))")
    op.drop_constraint("reports_severity_check", "reports", type_="check")
    op.create_check_constraint("reports_severity_check", "reports", "severity between 1 and 3")
    op.create_table(
        "report_milestones",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("report_id", sa.String(36), sa.ForeignKey("reports.id"), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.UniqueConstraint("report_id", "kind", name="uq_report_milestone_kind"),
    )
    op.create_index("ix_report_milestones_created_at", "report_milestones", ["created_at"])
    op.create_index("ix_report_milestones_report_id", "report_milestones", ["report_id"])
    op.execute(
        "INSERT INTO report_milestones "
        "(id, created_at, report_id, kind, actor_id, details) "
        "SELECT gen_random_uuid()::text, created_at, id, 'reported', reporter_id, '{}'::json "
        "FROM reports"
    )


def downgrade():
    op.drop_table("report_milestones")
    op.drop_index("ix_reports_public_code", table_name="reports")
    op.drop_column("reports", "public_code")
    op.execute("DROP SEQUENCE report_public_code_seq")
