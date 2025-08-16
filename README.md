# AI Meeting Notes Summarizer

Minimal full-stack app: upload a transcript, give a custom instruction, generate an editable AI summary, and email it.

## Quickstart (local)

1. Clone / create project and files as in the repo structure.

### Backend
```bash
cd backend
python -m venv .venv
# mac/linux
source .venv/bin/activate
# windows (powershell)
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env
# edit .env with your OPENAI_API_KEY and SMTP creds
uvicorn main:app --reload --port 8000
