"""Add local password hashes for JWT authentication."""
from alembic import op
import sqlalchemy as sa

revision = "0003_jwt_auth"
down_revision = "0002_curriculum"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}
    if "password_hash" not in columns:
        op.add_column("users", sa.Column("password_hash", sa.String(length=300), nullable=True))


def downgrade() -> None:
    raise RuntimeError("JWT authentication migration cannot be downgraded without losing password hashes")
