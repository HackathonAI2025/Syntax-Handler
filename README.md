# AI-Powered Code Reviewer with Customized Ollama LLM

## Overview
This project automates code reviews by integrating a **customized Ollama LLM** with GitHub. When a Pull Request is opened or updated, the service fetches the diff, generates real-time AI feedback, and posts comments directly on the PR.  

### What Problem It Solves
- **Slow code reviews**: Developers often wait hours or days for PR feedback.  
- **Inconsistent feedback**: Manual reviews can vary between reviewers.  
- **Knowledge capture**: Important insights from reviews are often lost.  

This solution delivers **instant, consistent, and contextual code feedback**, reducing turnaround time and improving overall code quality.  

---

## Features
- Automated Pull Request review with AI-generated suggestions.  
- Custom Ollama LLM fine-tuned for software engineering tasks.  
- Streaming feedback for fast, responsive results.  
- Runs locally or on GPU cloud instances.  
- Minimal setup — works with a single `app.py` file.  

---

## Requirements
- Python 3.10+  
- GitHub Personal Access Token with `repo` permissions  
- (Optional) Ollama installed locally for private/offline use  
- Python packages listed in `requirements.txt` (if available)  

---

## Running the App
1. docker pull leratot/code-review-bot:latest
2. docker run leratot/code-review-bot:latest

3. docker pull leratot/ollama:latest
4. docker run leratot/ollama:latest

5. Use ngrok to serve HTTPS (Temporary fix)
6. Invite syntaxhandler as a contributor to your repo and give it Write role access

7. Create a Webhook:
    Payload URL -> ngrok url/webook/github
    Content type -> application/json
    Which events would you like to trigger this webhook -> Enable Pull requests, Commit comments and Pushes only

8. Create a pull request/merge request wait approximately 5 minutes depending on how big your file is

9. Syntax handler will produce a clean polished version of your commit and display what was improved