# backend/src/app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import json
from pathlib import Path

# ✅ Correct imports (no `backend.` prefix)
from src.app.routes import goals, programs, recommendations
from src.app.util.files import load_json, load_csv

app = FastAPI(title="ElevatePath API")

# ✅ Apply CORS early
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://mdc-career-path-planner.vercel.app",
        "https://*.vercel.app",
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
def ping():
    return {"status": "ok", "message": "Backend is live and reachable"}

# === GEMINI SETUP ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print("✅ GEMINI_API_KEY loaded:", bool(GEMINI_API_KEY))

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data" / "seed"
print("📂 Data directory:", DATA_DIR)

@app.post("/api/invoke_llm")
async def invoke_llm(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "").strip()
    if not prompt:
        return {"error": "Empty prompt"}

    # ✅ Use correct file loaders
    try:
        goals = load_json(str(DATA_DIR / "career_goals.json"))
        programs = load_csv(str(DATA_DIR / "programs_mdc.csv"))
        cost_model = load_json(str(DATA_DIR / "cost_model.json"))
        transfer_pathways = load_json(str(DATA_DIR / "transfer_pathways.json"))
    except Exception as e:
        print("❌ File loading error:", e)
        return {"error": f"Error loading data files: {e}"}

    sample_programs = programs[:6]
    context = f"""
    You are ElevatePath, an AI academic advisor for Miami Dade College.

    Provide structured JSON with pathway details. Use realistic data examples.

    - Career Goals: {[g['name'] for g in goals[:8]]}
    - Programs: {[p['name'] for p in sample_programs]}
    - Transfer Options: {list(transfer_pathways.get('by_program', {}).keys())[:5]}
    - Average Cost: {cost_model.get('average_tuition', 'N/A')}

    User input: "{prompt}"
    """

    gemini_url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-2.5-flash:generateContent"
        f"?key={GEMINI_API_KEY}"
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": context}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }

    try:
        r = requests.post(gemini_url, json=payload, headers={"Content-Type": "application/json"})
        print("Gemini status:", r.status_code)
        if r.status_code != 200:
            print("❌ Gemini error:", r.text)
            return {"error": f"Gemini API error: {r.text}"}

        data = r.json()
        output_text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        try:
            return json.loads(output_text)
        except json.JSONDecodeError:
            print("⚠️ Output not valid JSON, returning raw text")
            return {"output": output_text}

    except Exception as e:
        print("❌ Request to Gemini failed:", e)
        return {"error": str(e)}

# ✅ Include routes after app definition
app.include_router(goals.router)
app.include_router(programs.router)
app.include_router(recommendations.router)
