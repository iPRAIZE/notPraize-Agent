import os
from fastapi import FastAPI, Request
import google.generativeai as genai

app = FastAPI()

# Configure your Gemini API Key (Get one for free at AI Studio)
genai.configure(api_key="AIzaSyB8KRHClKnP_sX6mZr5vlucV9RR0A9gIjY")
model = genai.GenerativeModel('gemini-pro')

@app.post("/write")
async def write_article(request: Request):
    # Receive data from the Covenant platform
    data = await request.json()
    topic = data.get("topic", "General Technology")
    
    # Prompt logic for your agent
    prompt = f"Write a professional, SEO-optimized article about: {topic}. Include headings and a conclusion."
    
    try:
        response = model.generate_content(prompt)
        return {
            "status": "success",
            "article": response.text
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# For local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
