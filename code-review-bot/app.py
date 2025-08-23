from fastapi import FastAPI, Request, Header # type: ignore
import requests
import os

app = FastAPI()

# Load env vars
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # personal access token for posting reviews
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")

# ---------------------------
# Helper: Call Ollama model
# ---------------------------
def review_with_ollama(diff: str) -> str:
    payload = {
        "model": "gwen-coder-7b",   # change if you want 3b
        "prompt": f"Review this code diff and suggest improvements:\n{diff}"
    }
    r = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload, stream=True)
    output = ""
    for line in r.iter_lines():
        if line:
            output += line.decode("utf-8")
    return output

# ---------------------------
# GitHub Webhook
# ---------------------------
@app.post("/webhook/github")
async def github_webhook(request: Request, x_github_event: str = Header(None)):
    payload = await request.json()
    if x_github_event == "pull_request" and payload["action"] in ["opened", "synchronize"]:
        pr = payload["pull_request"]
        repo = payload["repository"]["full_name"]
        diff_url = pr["diff_url"]

        # Get diff
        diff_resp = requests.get(diff_url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
        diff = diff_resp.text

        # Send to Ollama
        review = review_with_ollama(diff)

        # Post review comment
        comments_url = pr["_links"]["comments"]["href"]
        requests.post(
            comments_url,
            headers={
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json"
            },
            json={"body": f"🤖 Code Review Bot says:\n\n{review}"}
        )
    return {"status": "ok"}

# ---------------------------
# GitLab Webhook
# ---------------------------
@app.post("/webhook/gitlab")
async def gitlab_webhook(request: Request):
    payload = await request.json()
    object_kind = payload.get("object_kind")

    if object_kind == "merge_request":
        mr = payload["object_attributes"]
        if mr["action"] in ["open", "update"]:
            project_id = payload["project"]["id"]
            diff_url = mr["diff_refs"]["base_sha"]  # may need to fetch via GitLab API
            mr_iid = mr["iid"]

            # Example: fetch changes (requires API call)
            headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
            changes_url = f"{payload['project']['web_url']}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/changes"
            diff_resp = requests.get(changes_url, headers=headers)
            diff_data = diff_resp.json()
            diff = "\n".join([c["diff"] for c in diff_data["changes"]])

            # Send to Ollama
            review = review_with_ollama(diff)

            # Post review comment
            notes_url = f"{payload['project']['web_url']}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/notes"
            requests.post(
                notes_url,
                headers=headers,
                json={"body": f"🤖 Code Review Bot says:\n\n{review}"}
            )
    return {"status": "ok"}
