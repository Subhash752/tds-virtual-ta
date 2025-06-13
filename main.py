from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json, requests, os
from fastapi import Request
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
async def answer_question(request: Request):
    try:
        # Promptfoo sends a JSON string as body even when content-type is JSON
        body_bytes = await request.body()
        raw_text = body_bytes.decode("utf-8")

        # Handle Promptfoo-style double-encoded JSON
        try:
            parsed = json.loads(raw_text)
            if isinstance(parsed, str):
                parsed = json.loads(parsed)
        except json.JSONDecodeError:
            return {"answer": "Invalid JSON from request", "links": []}

        q = parsed.get("question", "")
        image = parsed.get("image", None)

        # Search for context
        context = "\n\n".join(
            f"{p['title']}\n{p['content']}"
            for p in discourse_data
            if q.lower() in p.get("title", "").lower() or q.lower() in p.get("content", "").lower()
        )[:15000]

        # AI pipe payload
        payload = {
            "model": "gpt-4",
            "input": f"Context:\n{context}\n\nQuestion:\n{q}"
        }
        headers = {
            "Authorization": f"Bearer {AIPIPE_TOKEN}",
            "Content-Type": "application/json"
        }

        resp = requests.post(AIPIPE_URL, headers=headers, json=payload)
        if resp.status_code == 200:
            res = resp.json()
            answer = res["output"][0].get("content") if isinstance(res.get("output"), list) else str(res)
        else:
            answer = f"Error {resp.status_code}: {resp.text}"

        return {
            "answer": answer,
            "links": [
                {"url": p["url"], "text": p["title"]}
                for p in discourse_data
                if q.lower() in p.get("title", "").lower() or q.lower() in p.get("content", "").lower()
            ][:3]
        }

    except Exception as e:
        return {"answer": f"Exception occurred: {str(e)}", "links": []}

