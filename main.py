from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from openai import OpenAI
import os

app = FastAPI()

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

MODEL = "meta-llama/llama-3.3-8b-instruct:free"


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


@app.get("/ping")
def ping():
    return {"status": "healthy"}


@app.get("/capabilities")
def capabilities():
    return {"agent": "Article Writing Agent", "price_usdc": 2}


@app.post("/invocations", response_model=ArticleResponse)
def write_article(req: ArticleRequest):
    length_map = {
        "short": "approximately 300 words",
        "medium": "approximately 600 words",
        "long": "approximately 1200 words",
    }
    word_target = length_map.get(req.length, "approximately 600 words")
    keywords_str = ", ".join(req.keywords) if req.keywords else "none"

    prompt = (
        "Write a complete article.\n"
        "Topic: " + req.topic + "\n"
        "Tone: " + req.tone + "\n"
        "Length: " + word_target + "\n"
        "Audience: " + req.audience + "\n"
        "Keywords: " + keywords_str + "\n"
        "Extra: " + (req.extra_instructions or "none") + "\n\n"
        "Start your response with: TITLE: <your title here>\n"
        "Then a blank line, then the full article body with subheadings."
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
        )
        raw = response.choices[0].message.content.strip()
        lines = raw.split("\n")
        if lines[0].startswith("TITLE:"):
            title = lines[0].replace("TITLE:", "").strip()
            body = "\n".join(lines[2:]).strip()
        else:
            title = req.topic
            body = raw

        return ArticleResponse(
            title=title,
            article=body,
            word_count=len(body.split()),
            topic=req.topic,
            tone=req.tone,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
