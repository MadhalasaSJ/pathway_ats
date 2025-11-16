import os
import json
import re
from typing import Dict, Any, Optional

from openai import OpenAI


# Support OpenAI, Groq, and Grok (xAI)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")

GROK_API_KEY = os.getenv("GROK_API_KEY")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-2-1212")

# Determine which provider to use (priority: GROQ > GROK > OPENAI)
USE_GROQ = os.getenv("USE_GROQ", "false").lower() == "true"
USE_GROK = os.getenv("USE_GROK", "false").lower() == "true"

if USE_GROQ:
    if not GROQ_API_KEY:
        raise RuntimeError("USE_GROQ=true but GROQ_API_KEY not set")
    # Groq endpoint
    client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
    ACTIVE_MODEL = GROQ_MODEL
    ACTIVE_PROVIDER = "Groq"
elif USE_GROK:
    if not GROK_API_KEY:
        raise RuntimeError("USE_GROK=true but GROK_API_KEY not set")
    # Grok uses xAI endpoint
    client = OpenAI(api_key=GROK_API_KEY, base_url="https://api.x.ai/v1")
    ACTIVE_MODEL = GROK_MODEL
    ACTIVE_PROVIDER = "Grok (xAI)"
else:
    if not OPENAI_API_KEY:
        raise RuntimeError("Please set OPENAI_API_KEY (or USE_GROQ=true + GROQ_API_KEY, or USE_GROK=true + GROK_API_KEY)")
    client = OpenAI(api_key=OPENAI_API_KEY)
    ACTIVE_MODEL = OPENAI_MODEL
    ACTIVE_PROVIDER = "OpenAI"


def _extract_json(text: str) -> str:
    # Try to find a JSON object in text
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        return m.group(0)
    return text


def analyze_resume(resume_text: str, job_text: str) -> Dict[str, Any]:
    prompt = (
        "You are an assistant that compares a candidate resume against a job description and returns a "
        "single JSON object (only JSON) with the following fields:\n"
        "- ats_score: integer 0-100\n"
        "- matched_keywords: array of strings\n"
        "- missing_keywords: array of strings\n"
        "- skill_gaps: array of short descriptions\n"
        "- strengths: array of short descriptions\n"
        "- suggestions: array of short improvement suggestions\n"
        "- experience_relevance: integer 0-100 (how relevant experience is)\n"
        "- raw_keywords_extracted: array of strings (all keywords extracted)\n"
        "Analyze both the resume and the job description. If the job description is empty, do a general role-based keyword extraction and score conservatively.\n"
        "Provide only the JSON output and nothing else. Ensure numeric fields are numbers (not strings)."
    )

    full_input = f"<RESUME>\n{resume_text}\n</RESUME>\n<JOB>\n{job_text}\n</JOB>"

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": full_input},
    ]

    resp = client.chat.completions.create(model=ACTIVE_MODEL, messages=messages, temperature=0, max_tokens=1200)
    content = resp.choices[0].message.content

    json_text = _extract_json(content)
    try:
        parsed = json.loads(json_text)
    except Exception:
        # As a fallback, try to clean common issues then parse
        cleaned = json_text.strip().strip('"')
        try:
            parsed = json.loads(cleaned)
        except Exception as e:
            raise RuntimeError(f"Failed to parse JSON from OpenAI response: {e}\nResponse was:\n{content}")

    # Normalize some fields
    if "ats_score" in parsed:
        try:
            parsed["ats_score"] = int(parsed["ats_score"])
        except Exception:
            parsed["ats_score"] = 0

    if "experience_relevance" in parsed:
        try:
            parsed["experience_relevance"] = int(parsed["experience_relevance"])
        except Exception:
            parsed["experience_relevance"] = 0

    return parsed
