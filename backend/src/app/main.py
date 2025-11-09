# backend/src/app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os
import requests
import json

from src.app.routes import goals, programs, recommendations
from backend.src.app.util.files import load_json, load_csv

app = FastAPI(title="ElevatePath API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://mdc-career-path-planner.vercel.app",
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
def ping():
    return {"message": "pong"}

# Load env + data dir
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print("GEMINI_API_KEY:", bool(GEMINI_API_KEY))

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data" / "seed"
print("DATA_DIR:", DATA_DIR)

@app.post("/api/invoke_llm")
async def invoke_llm(request: Request):
    try:
        body = await request.json()
        prompt = body.get("prompt", "").strip()
        if not prompt:
            return {"error": "Empty prompt"}

        # Load data
        goals = load_json(str(DATA_DIR / "career_goals.json"))
        programs = load_csv(str(DATA_DIR / "programs_mdc.csv"))
        cost_model = load_json(str(DATA_DIR / "cost_model.json"))
        transfer_pathways = load_json(str(DATA_DIR / "transfer_pathways.json"))

        sample_programs = programs[:6]

        context = f"""
        You are ElevatePath, AI advisor for Miami Dade College.
        Respond in JSON only. Use real data.

        Goals: {[g['name'] for g in goals[:8]]}
        Programs: {[p['name'] for p in sample_programs]}
        Transfers: {list(transfer_pathways.get("by_program", {}).keys())[:5]}
        Cost: {cost_model.get('average_tuition', 'N/A')}

        User: "{prompt}"
        """

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": context}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }

        r = requests.post(url, json=payload, timeout=30)
        if r.status_code != 200:
            return {"error": r.text}

        output = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(output)

    except Exception as e:
        return {"error": str(e)}

# Include routers
app.include_router(goals.router)
app.include_router(programs.router)
app.include_router(recommendations.router)