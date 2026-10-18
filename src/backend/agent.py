
import json
import re
from pathlib import Path

from backend.critic import review
from backend.llm import ask
from backend.tools import Tools


SYSTEM = """
You are a repository analysis and Docker deployment agent.

Workflow:
1. Use the provided recursive file scan to understand the repository.
2. Select the relevant application manifest and its lockfiles.
3. Read relevant manifests, version files and entry points using read_file.
4. Identify dependencies, runtime version, build process and startup command.
5. Write Dockerfile using write_file.
6. Fix critic feedback before finishing.

Rules:
- Use repository evidence; never invent files or commands.
- Prefer suitable official, minimal base images.
- Respect .python-version and .nvmrc when present.
- Use lockfiles and the correct package manager where possible.
- Copy dependency files first when useful for caching.
- Configure web applications to listen on 0.0.0.0:8080.
- Include ENV PORT=8080 and EXPOSE 8080.
- For static frontends, build and serve output on port 8080.
- Never read .env files or expose secrets.
- Do not use sudo, curl|sh or privileged settings.
- Write only Dockerfile or .dockerignore at repository root.
- Return done only after writing the Dockerfile.

Return exactly one JSON object per turn:
{"tool":"list_files","args":{"path":"."}}
{"tool":"read_file","args":{"path":"pyproject.toml"}}
{"tool":"write_file","args":{"path":"Dockerfile","content":"..."}}
{"done":true,"summary":"Dockerfile generated"}
"""


def parse_action(text):
    decoder = json.JSONDecoder()

    for match in re.finditer(r"\{", text):
        try:
            action, _ = decoder.raw_decode(text[match.start():])
            if isinstance(action, dict):
                return action
        except json.JSONDecodeError:
            continue

    raise ValueError("No valid JSON action returned")


def run(ctx, files, max_steps=12, max_reviews=3):
    ctx = Path(ctx).resolve()
    tools = Tools(ctx)

    history = [
        SYSTEM,
        "Repository root: " + str(ctx),
        "Discovered files:\n" + "\n".join(files),
    ]
    trace = []
    reviews = 0

    if (ctx / "Dockerfile").is_file():
        issues = review(ctx)
        if not issues:
            return "Existing Dockerfile validated", ["critic: passed"]

        history.append(
            "Existing Dockerfile has issues. Read it and fix it:\n- "
            + "\n- ".join(issues)
        )

    for _ in range(max_steps):
        reply = ask(
            "\n\n".join(history)
            + "\n\nChoose your next action as one JSON object."
        )
        history.append("AGENT: " + reply)

        try:
            action = parse_action(reply)
        except ValueError:
            history.append("Return one valid JSON object.")
            continue

        if action.get("done") is True:
            issues = review(ctx)

            if not issues:
                trace.append("critic: passed")
                return action.get("summary", "Dockerfile generated"), trace

            reviews += 1
            trace.append(f"critic: {issues}")

            if reviews >= max_reviews:
                raise RuntimeError(
                    "Dockerfile rejected:\n- " + "\n- ".join(issues)
                )

            history.append(
                "Fix these critic issues using write_file:\n- "
                + "\n- ".join(issues)
            )
            continue

        name = action.get("tool")
        args = action.get("args", {})

        if name not in {"list_files", "read_file", "write_file"}:
            history.append(f"Unknown tool: {name}")
            continue

        if not isinstance(args, dict):
            history.append("Tool arguments must be a JSON object.")
            continue

        try:
            result = getattr(tools, name)(**args)
            trace.append(f"{name}: success")
        except Exception as error:
            result = {"error": str(error)}
            trace.append(f"{name}: failed")

        history.append(
            "TOOL RESULT: " + json.dumps(result, ensure_ascii=False)[:4000]
        )

    raise RuntimeError("Agent exceeded its step limit")
