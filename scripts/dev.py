"""Cross-platform local launcher. Does not install packages or expose the app publicly."""
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
os.chdir(root)
if not (root / ".env").exists():
    subprocess.run([sys.executable, "scripts/init_local.py"], check=True)
subprocess.run([sys.executable, "-m", "uvicorn", "app.main:create_app", "--factory",
                "--host", "127.0.0.1", "--port", "8000", "--no-access-log"], check=True)
