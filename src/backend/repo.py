
import os
import tempfile
import shutil

from backend.shell import sh

WORK = os.path.join(tempfile.gettempdir(), "deploy-repo-agent")
REPO_PATH = os.path.join(WORK, "repo")

SKIP = {".git", "node_modules", ".venv", "venv", "__pycache__"}
MARKERS = ["Dockerfile", "package.json", "pyproject.toml", "requirements.txt", "go.mod"]


def clone(url):
    os.makedirs(WORK, exist_ok=True)

    if os.path.exists(REPO_PATH):
        shutil.rmtree(REPO_PATH)

    sh(["git", "clone", "--depth", "1", "--", url, REPO_PATH], timeout=120)

    return REPO_PATH


def scan(path):
    found = {}

    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP]

        for marker in MARKERS:
            if marker in files:
                found.setdefault(marker, root)

    return found
