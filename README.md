# 🤖 AI Code Review Bot (Ollama + FastAPI)

This project is a lightweight backend service that listens to **GitHub Pull Request events** (via Webhooks) and uses a **local Ollama model** to provide AI-powered code reviews.

Whenever a PR is opened or updated, the bot automatically analyzes the changes and posts review comments.

---

## ⚙️ Features
- Listens to GitHub Webhooks for **PR opened / updated** events.
- Forwards the code diff to a local Ollama model (e.g., `code-reviewer`).
- Posts review comments back to the GitHub PR.
- Runs entirely **locally** (no external API calls, except GitHub).

---

## 🛠️ Requirements
- Python **3.10+**
- [Ollama](https://ollama.ai) installed and running
- GitHub account + repository where you have admin rights
- [ngrok](https://ngrok.com) (or another tunnel) to expose your local server to GitHub

---