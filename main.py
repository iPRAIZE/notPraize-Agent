from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from openai import OpenAI
import os
app = FastAPI(title="Article Writing Agent", version="1.0.0")
app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_methods=["*"],
allow_headers=["*"],
)
client = OpenAI(
base_url="https://openrouter.ai/api/v1",
api_key=os.environ.get("OPENROUTER_API_KEY"),
)
FREE_MODEL = "meta-llama/llama-3.3-8b-instruct:free"
# ── Request / Response models ──────────────────────────────────────────────────
class ArticleRequest(BaseModel):
topic: str
tone: Optional[str] = "informative"
length: Optional[str] = "medium"
keywords: Optional[list[str]] = []
audience: Optional[str] = "general"
extra_instructions: Optional[str] = ""
class ArticleResponse(BaseModel):
title: str
article: str
word_count: int
topic: str
tone: str
# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/ping")
def ping():
return {"status": "healthy"}
# ── Main agent endpoint ────────────────────────────────────────────────────────
@app.post("/invocations", response_model=ArticleResponse)
def write_article(req: ArticleRequest):
length_map = {
"short": "approximately 300 words",
"medium": "approximately 600 words",
"long": "approximately 1200 words",
}
word_target = length_map.get(req.length, "approximately 600 words")
keywords_str = ", ".join(req.keywords) if req.keywords else "none specified"
prompt = f"""Write a complete, high-quality article with the following specs:
Topic: {req.topic}
Tone: {req.tone}
Target length: {word_target}
Target audience: {req.audience}
Keywords to include naturally: {keywords_str}
Extra instructions: {req.extra_instructions or 'none'}
Structure the article with:
1. A compelling title (on its own line, prefixed with TITLE:)
2. An engaging introduction
3. Well-structured body paragraphs with subheadings
4. A clear conclusion
Return ONLY the article content. First line must be: TITLE: <your title here>
Then a blank line, then the full article body."""
try:
response = client.chat.completions.create(
model=FREE_MODEL,
messages=[{"role": "user", "content": prompt}],
max_tokens=2000,
)
raw = response.choices[0].message.content.strip()
lines = raw.split("\n")
title = lines[0].replace("TITLE:", "").strip() if lines[0].startswith("TITLE:") else
body = "\n".join(lines[2:]).strip() if len(lines) > 2 else raw
return ArticleResponse(
title=title,
article=body,
word_count=len(body.split()),
topic=req.topic,
tone=req.tone,
)
except Exception as e:
raise HTTPException(status_code=500, detail=str(e))
# ── Capabilities ───────────────────────────────────────────────────────────────
@app.get("/capabilities")
def capabilities():
return {
"agent": "Article Writing Agent",
"capabilities": [
{
"name": "write_article",
"description": "Generate a full article on any topic with custom tone, "endpoint": "/invocations",
"method": "POST",
"price_usdc": 2,
"input_schema": {
"topic": "string (required)",
"tone": "informative | persuasive | casual | professional",
"length": "short | medium | long",
"keywords": "array of strings",
"audience": "string",
"extra_instructions": "string"
length
}
}
]
}
