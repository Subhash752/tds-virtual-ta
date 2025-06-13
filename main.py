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
        # Try to parse JSON body (raw or stringified)
        body_bytes = await request.body()
        try:
            data = json.loads(body_bytes.decode())
            if isinstance(data, str):
                data = json.loads(data)
        except json.JSONDecodeError:
            return {"answer": "Invalid JSON", "links": []}

        q = data.get("question", "")
        image = data.get("image")

        # CONTEXT MATCHING
        context = "\n\n".join(
            f"{p['title']}\n{p['content']}"
            for p in discourse_data
            if q.lower() in p.get("title", "").lower() or q.lower() in p.get("content", "").lower()
        )[:15000]

        # CALL AI PIPE
        payload = {
            "model": "gpt-4",
            "input": f"Context:\n{context}\n\nQuestion:\n{q}"
        }
        headers = {
            "Authorization": f"Bearer {AIPIPE_TOKEN}",
            "Content-Type": "application/json"
        }
        resp = requests.post(AIPIPE_URL, headers=headers, json=payload)

        # PARSE AI PIPE RESPONSE
        if resp.status_code == 200:
            res = resp.json()
            if "output" in res and isinstance(res["output"], list):
                answer = res["output"][0].get("content") or str(res["output"])
            else:
                answer = f"Unexpected format in response: {res}"
        else:
            answer = f"Error {resp.status_code}: {resp.text}"

        # RETURN FINAL RESPONSE
        return {
            "answer": answer,
            "links": [
                {"url": p["url"], "text": p["title"]}
                for p in discourse_data
                if q.lower() in p.get("title", "").lower() or q.lower() in p.get("content", "").lower()
            ][:3]
        }

    except Exception as e:
        return {"answer": f"Exception: {str(e)}", "links": []}

