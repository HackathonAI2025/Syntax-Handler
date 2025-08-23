# review_pr.py
import os
import sys
import requests
import json

# --- Configuration ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = os.getenv("PR_NUMBER")

# This URL must be accessible from your GitHub Action runner.
# We'll use ngrok to expose our local Ollama instance.
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = "llama3:8b-instruct"

# --- AI Personas Configuration ---
PERSONAS = {
    "Security_Analyst": {
        "icon": "🛡️",
        "system_prompt": "You are a senior cybersecurity analyst. Your sole focus is to find security vulnerabilities in this code diff. Identify potential issues like SQL injection, XSS, insecure direct object references, or improper handling of secrets. Be concise, critical, and provide code examples for fixes. If you find no issues, respond with 'No security issues found.'."
    },
    "Performance_Guru": {
        "icon": "⚡",
        "system_prompt": "You are a principal engineer obsessed with performance and efficiency. Analyze this code diff for performance bottlenecks like N+1 queries, inefficient loops, or blocking I/O. Provide actionable suggestions for optimization. If you find no issues, respond with 'No performance issues found.'."
    },
    "Maintainability_Coach": {
        "icon": " M",
        "system_prompt": "You are a software architect who champions clean, readable, and maintainable code. Review this diff for code clarity, adherence to SOLID principles, and excessive complexity. Suggest refactoring to improve long-term maintainability. If you find no issues, respond with 'No maintainability issues found.'."
    }
}

def get_pr_diff():
    """Fetches the diff of the pull request from the GitHub API."""
    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/pulls/{PR_NUMBER}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.diff"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

def get_ollama_feedback(diff, persona_config):
    """Queries Ollama with a specific persona and the code diff."""
    prompt = f"Please review the following code changes:\n\n```diff\n{diff}\n```"
    
    try:
        print(f"Requesting review from {persona_config['icon']}...")
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "system": persona_config["system_prompt"],
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            },
            timeout=300
        )
        response.raise_for_status()
        
        feedback = response.json().get("response", "").strip()
        
        # Filter out "no issues found" messages to keep the final comment clean
        if "no issues found" in feedback.lower():
            print(f"{persona_config['icon']} found no issues.")
            return None
            
        return feedback
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Ollama: {e}")
        return f"Could not get a review. Error: {e}"

def post_github_comment(comment):
    """Posts a comment to the GitHub pull request."""
    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/issues/{PR_NUMBER}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": comment}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print("Successfully posted comment to GitHub.")
    else:
        print(f"Failed to post comment. Status: {response.status_code}, Response: {response.text}")
        sys.exit(1)


def main():
    if not all([GITHUB_TOKEN, GITHUB_REPOSITORY, PR_NUMBER]):
        print("Error: Missing required environment variables.")
        sys.exit(1)

    print("Fetching PR diff...")
    diff = get_pr_diff()
    
    if not diff:
        print("No diff found. Exiting.")
        return

    full_review_comment = "### 🤖 AI Review Committee Analysis\n\n"
    has_feedback = False

    for persona_name, config in PERSONAS.items():
        feedback = get_ollama_feedback(diff, config)
        if feedback:
            has_feedback = True
            full_review_comment += f"#### {config['icon']} {persona_name}'s Feedback\n{feedback}\n\n"
            
    if has_feedback:
        post_github_comment(full_review_comment)
    else:
        print("All committee members reported no significant issues.")
        # Optional: post a simple "LGTM!" comment
        success_comment = "🤖 AI Review Committee: All checks passed. Looks good to me! 👍"
        post_github_comment(success_comment)

if __name__ == "__main__":
    main()