"""Add curriculum catalog, editorial packs, and lesson progress."""
from alembic import op
import sqlalchemy as sa

from app.database import Base
from app import models  # noqa: F401

revision = "0002_curriculum"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    # The original initial migration builds tables from current metadata.
    # Keep upgrades compatible with both fresh and already-initialized DBs.
    Base.metadata.create_all(bind=bind, checkfirst=True)
    columns = {column["name"] for column in sa.inspect(bind).get_columns("practice_questions")}
    if "course_pack_id" not in columns:
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table("practice_questions", recreate="always") as batch:
                batch.add_column(sa.Column("course_pack_id", sa.Integer(), nullable=True))
                batch.create_foreign_key(
                    "fk_practice_questions_course_pack_id_course_packs",
                    "course_packs", ["course_pack_id"], ["id"], ondelete="CASCADE",
                )
                batch.create_index("ix_practice_questions_course_pack_id", ["course_pack_id"])
        else:
            op.add_column("practice_questions", sa.Column("course_pack_id", sa.Integer(), nullable=True))
            op.create_foreign_key(
                "fk_practice_questions_course_pack_id_course_packs",
                "practice_questions", "course_packs", ["course_pack_id"], ["id"], ondelete="CASCADE",
            )
            op.create_index("ix_practice_questions_course_pack_id", "practice_questions", ["course_pack_id"])


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("practice_questions")}
    if "course_pack_id" in columns:
        with op.batch_alter_table("practice_questions", recreate="always") as batch:
            batch.drop_index("ix_practice_questions_course_pack_id")
            batch.drop_column("course_pack_id")
    for table in (
        "lesson_progress", "course_lessons", "course_packs", "curriculum_requirements",
        "track_courses", "courses", "curriculum_tracks",
    ):
        op.drop_table(table)
