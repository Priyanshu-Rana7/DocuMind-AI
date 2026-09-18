"""create initial invoice schema

Revision ID: 0001_initial_invoice_schema
Revises:
Create Date: 2026-09-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial_invoice_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    invoice_status = sa.Enum(
        "PENDING",
        "UPLOADED",
        "OCR_COMPLETED",
        "EXTRACTED",
        "FAILED",
        name="invoicestatus",
    )
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        invoice_status.create(bind, checkfirst=True)

    op.create_table(
        "invoices",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            invoice_status,
            nullable=False,
            server_default="UPLOADED",
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("raw_ocr_text", sa.Text(), nullable=True),
        sa.Column("ocr_metadata", sa.JSON(), nullable=True),
        sa.Column("extracted_data", sa.JSON(), nullable=True),
        sa.Column("overall_confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_invoices_id", "invoices", ["id"], unique=False)
    op.create_index("ix_invoices_status", "invoices", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_invoices_status", table_name="invoices")
    op.drop_index("ix_invoices_id", table_name="invoices")
    op.drop_table("invoices")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        sa.Enum(name="invoicestatus").drop(bind, checkfirst=True)
