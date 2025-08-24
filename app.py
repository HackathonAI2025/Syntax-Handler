from fastapi import FastAPI, Request, Header, BackgroundTasks
import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = FastAPI()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")


# ---------------------------
# Helper: Call Ollama model
# ---------------------------
def review_with_ollama(diff: str) -> str:
    payload = {
        "model": "code-reviewer",
        "prompt": f"Review this code diff and suggest improvements:\n{diff}"
    }
    r = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload, stream=True)
    output = ""
    for line in r.iter_lines():
        if line:
            try:
                data = json.loads(line.decode("utf-8"))
                token = data.get("response", "")
                print(token, end="", flush=True)
                output += token
            except Exception as e:
                print(f"\n[Error parsing Ollama response line: {e}] {line}")
    print("\n--- End of Ollama output ---\n")
    return output


# ---------------------------
# GitHub Webhook
# ---------------------------
@app.post("/webhook/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: str = Header(None)
):
    payload = await request.json()
    print("Received GitHub event:", x_github_event)

    if x_github_event == "pull_request" and payload.get("action") in ["opened", "synchronize"]:
        background_tasks.add_task(process_pr, payload)
        return {"status": "ok"}


def process_pr(payload):
    pr = payload["pull_request"]
    repo = payload["repository"]["full_name"]
    pr_number = pr["number"]
    print(f"Processing PR #{pr_number} in repo {repo}")

    # Fetch commits
    pr_commits_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/commits"
    commits_resp = requests.get(pr_commits_url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    if commits_resp.status_code != 200:
        print("Failed to fetch commits:", commits_resp.status_code, commits_resp.text)
        return {"status": "failed to fetch commits"}

    commits = commits_resp.json()
    latest_commit_sha = commits[-1]["sha"]

    # Fetch diff
    diff_url = f"https://github.com/{repo}/pull/{pr_number}.diff"
    diff_resp = requests.get(diff_url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    diff = diff_resp.text
    if not diff.strip():
        print("Empty diff, skipping review")
        return {"status": "empty diff"}

    # Generate review via Ollama
    review = review_with_ollama(diff)

    # Post review as a comment
    reviews_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
    resp = requests.post(
        reviews_url,
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        },
        json={
            "body": f"Code Review Bot says:\n\n{review}",
            "event": "COMMENT",
            "commit_id": latest_commit_sha
        }
    )

    # Friendly log instead of raw GitHub response
    if resp.status_code in [200, 201]:
        print(f"Comment was posted on PR #{pr_number}, please take a look at it.")
    else:
        print(f"Failed to post comment on PR #{pr_number}. Status code: {resp.status_code}")

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
            mr_iid = mr["iid"]

            # Fetch changes
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