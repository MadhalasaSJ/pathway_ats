# AI-Powered ATS Checker

## Overview
This project is an AI-powered Applicant Tracking System (ATS) checker built with **Streamlit** and **Python**. It analyzes how well a candidate’s resume matches a specific job description by extracting text from both, processing them with an LLM (**OpenAI**, **Grok**, or **Groq**), and producing a structured compatibility report.

The app returns an ATS score, matched and missing keywords, skill gaps, strengths, experience relevance, and improvement suggestions. It can also save each evaluation to **Back4App (Parse)** using REST or an MCP endpoint.

---

## What the App Does
- Extracts text from:
  - Resumes (PDF / DOCX)
  - Job descriptions (PDF / DOCX / TXT / pasted text)
- Uses an LLM to compare the resume and job description.
- Generates a structured JSON analysis containing:
  - **ATS match score (0–100)**
  - **Matched vs. missing keywords**
  - **Skill gaps and strengths**
  - **Experience relevance**
  - **Actionable improvement suggestions**
- Renders results in a clean, responsive Streamlit UI.
- Saves evaluation results (resume text, JD text, score, keywords, timestamp) to **Back4App** when credentials are provided.

---

## Key Files
- `app/main.py` — Streamlit UI and main workflow  
- `app/utils/text_extract.py` — PDF/DOCX/TXT text extraction  
- `app/utils/openai_ats.py` — LLM comparison and ATS scoring  
- `app/utils/back4app_mcp.py` — Save evaluation payloads to Back4App  
- `app/assets/styles.css` — App styling  
- `requirements.txt` — Python dependencies  

---

## Required Environment Variables
Configure these in your shell or Streamlit Cloud Secrets:

```bash
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4

USE_GROQ=false
GROQ_API_KEY=
GROQ_MODEL=mixtral-8x7b-32768

USE_GROK=false
GROK_API_KEY=

BACK4APP_APP_ID=
BACK4APP_REST_KEY=
BACK4APP_MCP_URL=
```

## Running Locally

### 1. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .\.venv\Scripts\Activate.ps1  # Windows PowerShell
pip install -r requirements.txt
```

### 2. Set required environment variables:
```bash

export USE_GROQ=true
export GROQ_API_KEY="<your-groq-key>"
export GROQ_MODEL="llama-3.3-70b-versatile"
export BACK4APP_APP_ID="<your-back4app-appid>"
export BACK4APP_REST_KEY="<your-back4app-restkey>"
(Use $env:VARIABLE="value" on Windows.)
```
### 3. Run the app:
```bash
streamlit run app/main.py
```
Once launched, the app UI lets you upload a resume and job description, run the AI analysis, and optionally save results to Back4App.
