
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from backend.agent import run
from backend.tools import Tools

app = FastAPI()


class Deploy(BaseModel):
    url: str


@app.post("/deploy")
def deploy(body: Deploy):
    tools = Tools()

    try:
        repo_path = tools.clone_repo(body.url)
        files = tools.scan_repository()

        if not files:
            raise RuntimeError("No supported project files found")

        summary, trace = run(repo_path, files)

        return {
            "repo_url": body.url,
            "files_found": files,
            "summary": summary,
            "trace": trace,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
