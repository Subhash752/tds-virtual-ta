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
        body_bytes = await request.body()
        raw_text = body_bytes.decode("utf-8")

        # Decode even if it's a stringified string
        try:
            data = json.loads(raw_text)
            if isinstance(data, str):  # Promptfoo bug workaround
                data = json.loads(data)
        except:
            return {"answer": "Invalid request JSON", "links": []}

        question = data.get("question", "")
        image = data.get("image", None)

        # Context lookup
        context = "\n\n".join(
            f"{p['title']}\n{p['content']}"
            for p in discourse_data
            if question.lower() in p.get("title", "").lower() or question.lower() in p.get("content", "").lower()
        )[:15000]

        payload = {
            "model": "gpt-4",  # Supported model in AIPipe
            "input": f"Context:\n{context}\n\nQuestion:\n{question}"  # Must use 'input', not 'messages'
        }

        headers = {
            "Authorization": f"Bearer {AIPIPE_TOKEN}",
            "Content-Type": "application/json"
        }

        # Send to AIPipe
        response = requests.post(AIPIPE_URL, headers=headers, json=payload)
        if response.status_code == 200:
            res = response.json()
            output = res.get("output", [])
            answer = output[0]["content"] if isinstance(output, list) and "content" in output[0] else str(res)
        else:
            answer = f"Error: {response.status_code}, {response.text}"

        # Return final JSON
        return {
            "answer": answer,
            "links": [
                {"url": p["url"], "text": p["title"]}
                for p in discourse_data
                if question.lower() in p.get("title", "").lower() or question.lower() in p.get("content", "").lower()
            ][:3]
        }

    except Exception as e:
        return {"answer": f"Internal server error: {str(e)}", "links": []}

