from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json, requests, os

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

with open("scraper/discourse_data.json", "r", encoding="utf-8") as f:
    discourse_data = json.load(f)

AIPIPE_URL = "https://aipipe.org/openai/v1/responses"
AIPIPE_TOKEN = os.getenv("AIPIPE_TOKEN") or "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6ImdlbnRsZXdpbmQwMDZAZ21haWwuY29tIn0.x6g4K-hefdH6QX7q19swXQjUK_F0MvDx4YMFaxRvLNE"

class QuestionRequest(BaseModel):
    question: str
    image: str = None

@app.post("/api/")
def answer_question(req: QuestionRequest):
    q = req.question
    context = "\n\n".join(
        f"{p['title']}\n{p['content']}"
        for p in discourse_data
        if q.lower() in p.get("title","").lower() or q.lower() in p.get("content","").lower()
    )[:15000]  # limit length

    payload = {
        "model": "gpt-4",  # supported by AIPipe
        "input": f"Context:\n{context}\n\nQuestion:\n{q}"
    }
    headers = {"Authorization": f"Bearer {AIPIPE_TOKEN}", "Content-Type": "application/json"}
    resp = requests.post(AIPIPE_URL, headers=headers, json=payload)

    if resp.status_code == 200:
        res = resp.json()
        if "output" in res and isinstance(res["output"], list):
            answer = res["output"][0].get("content") or str(res["output"])
        else:
            answer = f"Unexpected format in response: {res}"
    else:
        answer = f"Error {resp.status_code}: {resp.text}"

    return {
        "answer": answer,
        "links": [
            {"url": p["url"], "text": p["title"]} for p in discourse_data
            if q.lower() in p.get("title","").lower() or q.lower() in p.get("content","").lower()
        ][:3]
    }
