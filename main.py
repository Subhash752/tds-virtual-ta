from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json
import requests
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Discourse data
with open("scraper/discourse_data.json", "r", encoding="utf-8") as f:
    discourse_data = json.load(f)

# AIPipe Config
AIPIPE_TOKEN = os.getenv("eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6ImdlbnRsZXdpbmQwMDZAZ21haWwuY29tIn0.x6g4K-hefdH6QX7q19swXQjUK_F0MvDx4YMFaxRvLNE")  # or hardcode temporarily
AIPIPE_URL = "https://aipipe.org/openai/v1/chat/completions"

# Input schema
class QuestionRequest(BaseModel):
    question: str
    image: str = None  # optional

@app.post("/api/")
def answer_question(request: QuestionRequest):
    question = request.question
    image = request.image

    # Match relevant posts
    matched = []
    for post in discourse_data:
        if question.lower() in post.get("title", "").lower() or question.lower() in post.get("content", "").lower():
            matched.append(post)
        if len(matched) >= 3:
            break

    context = "\n\n".join([f"{p['title']}\n{p['content']}" for p in matched])

    # Construct payload
    messages = [
        {"role": "system", "content": "You are a helpful TA for the IITM TDS course."},
        {"role": "user", "content": f"Question: {question}\n\nContext:\n{context}"}
    ]

    payload = {
        "model": "openai/gpt-4.1-nano",  # You can adjust model if needed
        "messages": messages
    }

    headers = {
        "Authorization": f"Bearer {AIPIPE_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(AIPIPE_URL, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        answer = result["choices"][0]["message"]["content"]
    else:
        answer = f"Error: {response.status_code}, {response.text}"

    links = [{"url": post["url"], "text": post["title"]} for post in matched]
    return {"answer": answer, "links": links}
