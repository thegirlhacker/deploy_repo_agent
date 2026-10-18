
import os
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from backend.shell import sh


SKIP = {
    ".git", "node_modules", ".venv", "venv",
    "__pycache__", ".next", "dist", "build",
}

MANIFESTS = {
    "package.json", "pyproject.toml", "requirements.txt",
    "go.mod", "Cargo.toml", "Pipfile", "Gemfile",
}

IMPORTANT_FILES = MANIFESTS | {
    "Dockerfile", "docker-compose.yml", "compose.yaml",
    "uv.lock", "poetry.lock", "package-lock.json",
    "pnpm-lock.yaml", "yarn.lock", "go.sum", "Cargo.lock",
    ".python-version", ".nvmrc",
    "main.py", "app.py", "server.py", "manage.py",
}


class Tools:
    def __init__(self, root=None):
        self.root = Path(root).resolve() if root else None

    def clone_repo(self, url):
        parsed = urlparse(url)

        if (
            parsed.scheme != "https"
            or parsed.hostname != "github.com"
            or not parsed.path.strip("/")
        ):
            raise ValueError("Provide a valid HTTPS GitHub repository URL")

        work = Path(tempfile.gettempdir()) / "deploy-repo-agent"
        work.mkdir(parents=True, exist_ok=True)

        destination = Path(
            tempfile.mkdtemp(prefix="repo-", dir=work)
        )
        shutil.rmtree(destination)

        try:
            sh(
                ["git", "clone", "--depth", "1", "--", url, str(destination)],
                timeout=120,
            )
        except Exception:
            shutil.rmtree(destination, ignore_errors=True)
            raise

        self.root = destination.resolve()
        return str(self.root)

    def _path(self, name):
        if self.root is None:
            raise RuntimeError("Clone a repository first")

        path = (self.root / name).resolve()

        if path != self.root and self.root not in path.parents:
            raise ValueError("Path outside repository")

        if any(part in SKIP for part in path.relative_to(self.root).parts):
            raise ValueError("Access to excluded directories is not allowed")

        if path.name in {".env", ".env.local", ".env.production"}:
            raise ValueError("Secret files are not accessible")

        return path

    def scan_repository(self):
        """Find relevant project files recursively."""
        found = []

        for current, dirs, files in os.walk(self.root):
            dirs[:] = sorted(d for d in dirs if d not in SKIP)

            for name in files:
                if name in IMPORTANT_FILES:
                    relative = (
                        Path(current) / name
                    ).relative_to(self.root).as_posix()
                    found.append(relative)

        return sorted(found)[:500]

    def list_files(self, path="."):
        folder = self._path(path)

        if not folder.is_dir():
            raise ValueError("Not a directory")

        return sorted(
            p.name + ("/" if p.is_dir() else "")
            for p in folder.iterdir()
            if p.name not in SKIP
            and p.name not in {
                ".env", ".env.local", ".env.production"
            }
        )[:100]

    def read_file(self, path):
        file = self._path(path)

        if not file.is_file() or file.stat().st_size > 100_000:
            raise ValueError("File missing or too large")

        return file.read_text(
            encoding="utf-8",
            errors="replace",
        )[:4000]

    def write_file(self, path, content):
        file = self._path(path)

        allowed = {"Dockerfile", ".dockerignore"}
        if file.relative_to(self.root).as_posix() not in allowed:
            raise ValueError("Only root Dockerfile or .dockerignore can be written")

        if not isinstance(content, str):
            raise ValueError("Content must be a string")

        file.write_text(content, encoding="utf-8", newline="\n")
        return f"Wrote {file.name}"
