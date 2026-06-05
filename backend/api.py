from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import pandas as pd
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="CEO Dashboard API")

# Allow React (running on a different port) to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "company_kpis.db"

# --- Database Helpers ---
def run_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

# --- LLM Helpers ---
def _call_llm(prompt: str, system: str = "", max_tokens: int = 600) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: API Key missing."
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.2,
            max_output_tokens=max_tokens,
        ),
    )
    return response.text.strip()

# --- API Data Models ---
class ChatRequest(BaseModel):
    question: str

# --- Endpoints ---

@app.get("/api/kpis/latest")
def get_latest_kpis():
    """Returns the top-level KPI strip data."""
    try:
        fin_df = run_query("SELECT * FROM fact_business_performance ORDER BY month DESC LIMIT 1")
        if fin_df.empty:
            return {"error": "No financial data"}
        row = fin_df.iloc[0]
        delta_pct = ((row["actual_revenue"] - row["target_revenue"]) / row["target_revenue"] * 100)
        
        return {
            "month": row["month"],
            "actual_revenue": row["actual_revenue"],
            "revenue_delta_pct": round(delta_pct, 1),
            "mrr": row["mrr"],
            "pipeline": row["total_weighted_pipeline"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/kpis/history")
def get_kpi_history():
    """Returns the full time-series for the charts."""
    try:
        df = run_query("SELECT month, target_revenue, actual_revenue, mrr FROM fact_business_performance ORDER BY month ASC")
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
def ask_data_warehouse(req: ChatRequest):
    """Handles the Natural Language to SQL logic."""
    schema_doc = """
    TABLE fact_business_performance (month TEXT, target_revenue REAL, actual_revenue REAL, mrr REAL, arr REAL, total_weighted_pipeline REAL)
    TABLE dim_employees (department TEXT, current_headcount INTEGER, active_hirings INTEGER, attrition_count INTEGER)
    TABLE dim_projects (client_name TEXT, project_name TEXT, partner_lead TEXT, billable_hours REAL, milestone_status TEXT, blockers_flag TEXT, csat_score REAL, renewal_intent TEXT)
    """
    
    # 1. Generate SQL (Now with One-Shot Prompting)
    system = (
        "You are a SQL expert. You must return ONLY a single, valid, single-line "
        "SQLite SELECT statement. Never include markdown, backticks, or explanations."
    )
    
    prompt = f"""DATABASE SCHEMA:
{schema_doc}

USER QUESTION: Which department has the highest headcount?
SQL: SELECT department FROM dim_employees ORDER BY current_headcount DESC LIMIT 1;

USER QUESTION: {req.question}
SQL:"""

    try:
        raw_sql = _call_llm(prompt, system=system, max_tokens=200).strip()
        
        # Clean up just in case it still tries to add markdown
        raw_sql = raw_sql.replace("```sql", "").replace("```", "").replace("\n", " ").strip()
        
        print(f"\n--- DEBUG: RAW LLM OUTPUT ---\n{raw_sql}\n-----------------------------\n")
    except Exception as e:
        return {"sql": None, "answer": f"LLM Generation failed: {str(e)}", "data": []}
    
    if "INVALID" in raw_sql.upper() or not raw_sql.upper().startswith("SELECT"):
        return {"sql": None, "answer": "Could not map question to database schema.", "data": []}

    # 2. Execute SQL
    try:
        result_df = run_query(raw_sql)
        data_json = result_df.to_dict(orient="records")
        
        # 3. Synthesize Answer
        preview = result_df.head(10).to_string(index=False)
        synth_prompt = f"QUESTION: {req.question}\nQUERY RESULTS:\n{preview}\n\nSummarise the answer in one clear, executive-level sentence. No markdown."
        answer = _call_llm(synth_prompt, max_tokens=120)
        
        return {
            "sql": raw_sql,
            "answer": answer,
            "data": data_json
        }
    except Exception as e:
         return {"sql": raw_sql, "answer": f"Query execution failed: {str(e)}", "data": []}


@app.get("/api/briefing")
def get_executive_briefing():
    """Generates the AI Chief of Staff weekly briefing."""
    try:
        # 1. Gather the latest data snapshot
        fin_df = run_query("SELECT * FROM fact_business_performance ORDER BY month DESC LIMIT 1")
        hc_df = run_query("SELECT SUM(current_headcount) as total, SUM(active_hirings) as hirings, SUM(attrition_count) as attrition FROM dim_employees")
        csat_df = run_query("SELECT AVG(csat_score) as avg_csat, COUNT(*) as active_projects FROM dim_projects WHERE csat_score > 0")
        projects_df = run_query("SELECT * FROM dim_projects")

        fin = fin_df.iloc[0].to_dict() if not fin_df.empty else {}
        hc = hc_df.iloc[0].to_dict() if not hc_df.empty else {}
        csat = csat_df.iloc[0].to_dict() if not csat_df.empty else {}
        
        blockers = projects_df[projects_df["blockers_flag"] == "Yes"]["project_name"].tolist() if not projects_df.empty else []
        delayed = projects_df[projects_df["milestone_status"] == "Delayed"]["project_name"].tolist() if not projects_df.empty else []

        # 2. Build the snapshot text
        snapshot = f"""
        FINANCIAL SNAPSHOT (latest month: {fin.get('month','N/A')})
        - Actual Revenue : ${fin.get('actual_revenue', 0):,.0f}
        - MRR            : ${fin.get('mrr', 0):,.0f}
        - Weighted Pipeline: ${fin.get('total_weighted_pipeline', 0):,.0f}

        PEOPLE
        - Total Headcount : {hc.get('total', 0)} employees
        - Open Reqs       : {hc.get('hirings', 0)}
        - Attrition       : {hc.get('attrition', 0)} this period

        DELIVERY
        - Average CSAT  : {round(csat.get('avg_csat', 0), 2)}/5.0
        - Projects with blockers : {', '.join(blockers) if blockers else 'None'}
        - Delayed milestones     : {', '.join(delayed)  if delayed  else 'None'}
        """

        # 3. Call Gemini
        system = (
            "You are an elite AI Chief of Staff preparing a concise weekly executive briefing "
            "for the CEO. Your tone is direct, data-driven, and action-oriented. "
            "Structure every response with exactly three sections: "
            "🚀 Macro Highlights, ⚠️ Operational Risks, 🎯 Strategic Recommendations. "
            "Each section should be 2-4 sentences. Never use bullet points inside sections."
        )
        
        briefing_text = _call_llm(snapshot, system=system, max_tokens=500)
        return {"briefing": briefing_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))