# backend/src/app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
from pathlib import Path

# Import your existing route modules
from src.app.routes import goals, programs, recommendations

# Initialize FastAPI app
app = FastAPI(title="ElevatePath API")

@app.get("/ping")
def ping():
    return {"message": "pong"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://mdc-career-path-planner.vercel.app",
        "https://*.vercel.app",  # allow all vercel subdomains
        "http://localhost:5173",  # your local dev
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print("✅ Loaded GEMINI_API_KEY:", bool(GEMINI_API_KEY))

# Dynamically locate your data folder
BASE_DIR = Path(__file__).resolve().parents[3]  # goes up from backend/src/app/main.py → backend/src → backend → project root
DATA_DIR = BASE_DIR / "data" / "seed"
print(f"📂 Using data directory: {DATA_DIR}")

@app.post("/api/invoke_llm")
async def invoke_llm(request: Request):
    from backend.src.app.util.files import load_json, load_csv
    import json

    body = await request.json()
    prompt = body.get("prompt", "").strip()
    if not prompt:
        return {"error": "Empty prompt"}

    data_dir = os.path.abspath("data/seed")
    print("📂 Using data directory:", data_dir)


    try:
        goals = load_json(f"{data_dir}/career_goals.json")
        programs = load_csv(f"{data_dir}/programs_mdc.csv")
        cost_model = load_json(f"{data_dir}/cost_model.json")
        transfer_pathways = load_json(f"{data_dir}/transfer_pathways.json")
    except Exception as e:
        print("❌ Error loading data files:", e)
        return {"error": f"Error loading data files: {e}"}

    sample_programs = programs[:6]

    # 🧠 Structured system prompt
    context = f"""
    You are ElevatePath, an AI academic advisor for Miami Dade College.

    Your goal is to respond in JSON that follows this schema:

    {{
      "career_goal": "string",
      "pathway_data": {{
        "mdc_phase": {{
          "degree_name": "string",
          "courses": [{{"code": "string", "name": "string", "credits": number}}],
          "duration_semesters": number,
          "total_cost": number,
          "total_credits": number
        }},
        "fiu_phase": {{
          "degree_name": "string",
          "transfer_credits": number,
          "required_courses": [{{"code": "string", "name": "string", "credits": number}}],
          "duration_semesters": number,
          "total_cost": number,
          "remaining_credits": number
        }},
        "advanced_phase": {{
          "masters": {{
            "degree_name": "string",
            "duration_years": number,
            "total_cost": number,
            "total_credits": number
          }},
          "phd": {{
            "degree_name": "string",
            "duration_years": number,
            "funding_available": boolean
          }}
        }},
        "total_summary": {{
          "total_years": number,
          "total_cost": number,
          "career_outlook": "string"
        }}
      }}
    }}

    Generate realistic data using these examples:
    - Career Goals: {[g['name'] for g in goals[:8]]}
    - Programs: {[p['name'] for p in sample_programs]}
    - Transfer Options: {list(transfer_pathways.get("by_program", {}).keys())[:5]}
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
        "generationConfig": {"responseMimeType": "application/json"}
    }

    try:
        print("\n🚀 Sending structured request to Gemini...")
        r = requests.post(gemini_url, json=payload, headers={"Content-Type": "application/json"})
        print("Gemini status code:", r.status_code)

        if r.status_code != 200:
            return {"error": f"Gemini API error: {r.text}"}

        data = r.json()
        output_text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        try:
            structured_output = json.loads(output_text)
            return structured_output
        except Exception as e:
            print("⚠️ Could not parse JSON:", e)
            return {"output": output_text}

    except Exception as e:
        print("❌ Gemini request failed:", e)
        return {"error": f"Gemini request failed: {e}"}

    from backend.src.app.util.files import load_json, load_csv

    body = await request.json()
    prompt = body.get("prompt", "").strip()
    if not prompt:
        return {"error": "Empty prompt"}

    try:
        goals = load_json(str(DATA_DIR / "career_goals.json"))
        programs = load_csv(str(DATA_DIR / "programs_mdc.csv"))
        mappings = load_json(str(DATA_DIR / "goal_program_map_mdc.json"))
        transfer_pathways = load_json(str(DATA_DIR / "transfer_pathways.json"))
        print("✅ Data files loaded successfully")
    except Exception as e:
        print("❌ Error loading data files:", e)
        return {"error": f"Error loading data files: {e}"}

    # Use smaller subset for prompt size
    sample_programs = programs[:8]

    # Build AI prompt context
    context = f"""
    You are ElevatePath, an AI academic advisor for Miami Dade College.

    Based on the following institutional data, recommend suitable academic or career paths
    that align with what the user describes. Be concise and practical.

    Career Goals (examples): {[g['name'] for g in goals[:8]]}
    Example Programs: {[p['name'] for p in sample_programs]}
    Transfer Pathways Examples: {list(transfer_pathways.get("by_program", {}).keys())[:5]}

    The user says: "{prompt}"
    """

    # Gemini endpoint
    gemini_url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"  # Changed from /v1/ to /v1beta/
        "gemini-2.5-flash:generateContent"  # Changed model from gemini-1.5-flash to gemini-2.5-flash
        f"?key={GEMINI_API_KEY}"
    )


    payload = {"contents": [{"role": "user", "parts": [{"text": context}]}]}

    try:
        print("\n🚀 Sending request to Gemini...")
        print("Payload preview:", payload["contents"][0]["parts"][0]["text"][:250], "...\n")

        r = requests.post(gemini_url, json=payload, headers={"Content-Type": "application/json"})
        print("Gemini status code:", r.status_code)
        print("Gemini response text:", r.text[:800], "\n")

        if r.status_code != 200:
            return {"error": f"Gemini API error: {r.text}"}

        data = r.json()
        output = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        if not output:
            return {"error": "Gemini returned an empty response"}

        print("✅ Gemini output preview:", output[:300])
        return {"output": output.strip()}

    except Exception as e:
        print("❌ Gemini request failed:", e)
        return {"error": f"Gemini request failed: {e}"}

# Include your backend’s existing routes
app.include_router(goals.router)
app.include_router(programs.router)
app.include_router(recommendations.router)
