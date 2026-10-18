from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import subprocess 
import os 

app = FastAPI()

class Deploy(BaseModel):
    url: str

@app.post("/deploy")
def deploy(body: Deploy):
    cloneRepo(body.url)
    checkFilesinRpo()
    return {
        "url": body.url
    }

def cloneRepo(url):
    subprocess.run(["git", "clone", url, "abc"])

files = ["pyproject.toml" , "package.json", "requirements.txt" , "go.mod" , "Dockerfile" , "docker-compose.yml" ]

def checkFilesinRpo():
    for f in files:
        matches = [
            os.path.join(root, name)
            for root, _, names in os.walk("abc")
            for name in names
            if name == f
        ]
        if matches:
            print(f"{f} exists: {matches}")
        else:
            print(f"{f} not found")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
