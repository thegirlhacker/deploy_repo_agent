
import re
from pathlib import Path


def review(ctx):
    path = Path(ctx) / "Dockerfile"
    if not path.is_file():
        return ["Dockerfile missing"]

    text = path.read_text(encoding="utf-8", errors="replace")
    lines = [
        line.strip() for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    issues = []

    if not lines or not lines[0].upper().startswith("FROM"):
        issues.append("Dockerfile must start with FROM")

    if not any(x.upper().startswith(("CMD ", "ENTRYPOINT ")) for x in lines):
        issues.append("Missing CMD or ENTRYPOINT")

    if not re.search(r"(?im)^EXPOSE\s+8080(?:\s|$)", text):
        issues.append("Expected EXPOSE 8080")

    if not re.search(r"(?im)^ENV\s+PORT=8080(?:\s|$)", text):
        issues.append("Expected ENV PORT=8080")

    if any(x in text.lower() for x in ("| sh", "| bash", "sudo ", "--privileged")):
        issues.append("Suspicious command or setting")

    return issues
