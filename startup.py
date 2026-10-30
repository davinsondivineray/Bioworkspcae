"""Apply database migrations and seed content before starting the web app."""
import os
import subprocess
import sys


def main() -> None:
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    subprocess.run([sys.executable, "seed.py"], check=True)
    os.execvp(sys.executable, [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", os.getenv("PORT", "8000")])


if __name__ == "__main__":
    main()
