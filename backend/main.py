# backend/main.py
import os
import smtplib
from email.message import EmailMessage
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

# Gemini client
import google.generativeai as genai

# Load environment variables from backend/.env
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set (put it in backend/.env)")

genai.configure(api_key=GEMINI_API_KEY)

# Model name (configurable in .env)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# SMTP settings
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)

SYSTEM_PROMPT = (
    "You are a professional meeting minutes assistant. "
    "Your job is to extract and clearly present the most important information from meeting transcripts. "
    "Always use concise and unambiguous language. "
    "\n\nRequired Output Format (in clean Markdown):\n"
    "### Overview\n"
    "- One or two sentences summarizing the overall purpose of the meeting.\n\n"
    "### Key Points\n"
    "- Bullet list of the most relevant discussion items (short, factual, no repetition).\n\n"
    "### Decisions\n"
    "- List decisions made, including *who* made the decision.\n\n"
    "### Action Items\n"
    "- Format each action item as: **[Owner]:** [Task] *(Due: [date if mentioned, otherwise 'TBD'])*\n\n"
    "### Risks/Dependencies\n"
    "- Mention potential risks, blockers, or dependencies (if none, write 'None identified').\n\n"
    "### Next Steps\n"
    "- List follow-up actions or upcoming events.\n\n"
    "If the user provides a custom instruction, strictly follow it while keeping output structured and precise."
)


app = FastAPI(title="Meeting Summarizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change in production to explicit origin(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SummarizeIn(BaseModel):
    transcript: str
    prompt: str


class EmailIn(BaseModel):
    summary: str
    recipients: List[EmailStr]
    subject: Optional[str] = "Meeting Summary"


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/summarize")
async def summarize(body: SummarizeIn):
    """
    Summarize the provided transcript using Gemini.
    """
    # Build user prompt
    user_content = f"Instruction: {body.prompt}\n\nTranscript:\n{body.transcript}"

    # Use the GenerativeModel API
    model = genai.GenerativeModel(GEMINI_MODEL)
    # generate_content returns an object with .text
    response = model.generate_content(user_content)

    # response.text contains the string output
    summary_text = response.text.strip() if getattr(response, "text", None) else "[no summary returned]"
    return {"summary": summary_text}


@app.post("/upload_and_summarize")
async def upload_and_summarize(
    file: UploadFile = File(...),
    prompt: str = Form("Summarize the meeting and extract action items.")
):
    """
    Accepts a .txt transcript file upload (multipart/form-data) and a prompt.
    Returns the generated summary.
    """
    # read as text
    content_bytes = await file.read()
    transcript = content_bytes.decode("utf-8", errors="ignore")

    user_content = f"Instruction: {prompt}\n\nTranscript:\n{transcript}"
    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content(user_content)
    summary_text = response.text.strip() if getattr(response, "text", None) else "[no summary returned]"
    return {"summary": summary_text}


@app.post("/email")
async def send_email(body: EmailIn):
    """
    Send the (edited) summary to the recipients via SMTP.
    """
    if not all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FROM_EMAIL]):
        return {"ok": False, "error": "SMTP not configured on server."}

    msg = EmailMessage()
    msg["Subject"] = body.subject
    msg["From"] = FROM_EMAIL
    msg["To"] = ", ".join(body.recipients)
    msg.set_content(body.summary)
    # HTML alternative (preformatted)
    msg.add_alternative(
        f"""<html><body><pre style="font-family: ui-monospace, monospace;">{body.summary}</pre></body></html>""",
        subtype="html",
    )

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
    except Exception as e:
        return {"ok": False, "error": str(e)}

    return {"ok": True}
