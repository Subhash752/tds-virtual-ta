from fastapi import FastAPI, Request
from pydantic import BaseModel
import json
import requests

app = FastAPI()

# Load Discourse data
with open("scraper/discourse_data.json", "r", encoding="utf-8") as f:
    discourse_data = json.load(f)

# Perplexity API config
PERPLEXITY_API_KEY = "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"
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

# Define input schema
class QuestionRequest(BaseModel):
    question: str
    image: str = None  # Base64-encoded image (optional)

@app.post("/")
def answer_question(request: QuestionRequest):
    question = request.question
    image = request.image

    # Match relevant Discourse posts
    matched = []
    for post in discourse_data:
        title = post.get("title", "")
        content = post.get("content", "")
        if question.lower() in title.lower() or question.lower() in content.lower():
            matched.append(post)
        if len(matched) >= 3:
            break

    # Prepare context for LLM
    context_text = "\n\n".join([f"{p['title']}\n{p['content']}" for p in matched])

    # Construct message payload
    user_content = []

    # Add text part
    user_content.append({
        "type": "text",
        "text": f"Question: {question}\n\nContext:\n{context_text}"
    })

    # Add image part if provided
    if image:
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{image}"
            }
        })

    payload = {
        "model": "sonar",  # or pplx-7b-chat if you prefer
        "messages": [
            {"role": "system", "content": "You are a helpful TA for the IITM TDS course."},
            {"role": "user", "content": user_content}
        ]
    }

    # API headers
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    # Send request to Perplexity
    response = requests.post(PERPLEXITY_API_URL, json=payload, headers=headers)

    if response.status_code == 200:
        result = response.json()
        answer = result["choices"][0]["message"]["content"]
    else:
        answer = "Sorry, I couldn't get a response from Perplexity."

    # Build links list
    links = [{"url": post["url"], "text": post["title"]} for post in matched]

    return {
        "answer": answer,
        "links": links
    }
