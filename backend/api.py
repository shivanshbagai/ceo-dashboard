# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import psycopg2.extras
import pandas as pd
import os
import re
import json
import urllib.request
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

DATABASE_URL = os.getenv("DATABASE_URL")

# --- Database Helpers ---
def run_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not set in .env")
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Avoid pandas read_sql warning by just executing and converting
        cur.execute(sql, params)
        if cur.description is None: # For non-SELECT statements
            conn.commit()
            conn.close()
            return pd.DataFrame()
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
    conn.close()
    return pd.DataFrame([dict(row) for row in rows], columns=columns) if rows else pd.DataFrame(columns=columns)

# --- LLM Helpers ---
def _call_llm(prompt: str, system: str = "", max_tokens: int = 600) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("API Key missing.")
        
    model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "CEO Dashboard"
    }
    
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": max_tokens
    }
    
    req = urllib.request.Request(
        url, 
        data=json.dumps(payload).encode('utf-8'), 
        headers=headers, 
        method='POST'
    )
    with urllib.request.urlopen(req) as response:
        res_data = json.loads(response.read().decode('utf-8'))
        if 'choices' in res_data and len(res_data['choices']) > 0:
            return res_data['choices'][0]['message']['content'].strip()
        elif 'error' in res_data:
            raise RuntimeError(f"OpenRouter API error: {res_data['error'].get('message')}")
        else:
            raise RuntimeError(f"Unexpected response format: {res_data}")


def clean_sql(sql: str) -> str:
    """Cleans up and auto-corrects table names in the generated SQL statement."""
    # 1. Normalize spaces
    cleaned = re.sub(r'\s+', ' ', sql).strip()
    
    # Remove trailing semicolons or punctuation for regex matching
    cleaned = cleaned.rstrip(';')
    
    project_cols = ['client_name', 'project_name', 'partner_lead', 'deal_stage', 'pipeline_value', 'billable_hours', 'milestone_status', 'blockers_flag', 'csat_score', 'renewal_intent']
    employee_cols = ['department', 'current_headcount', 'active_hirings', 'attrition_count']
    finance_cols = ['target_revenue', 'actual_revenue', 'mrr', 'arr']

    if re.search(r'\bfrom\s*$', cleaned, flags=re.IGNORECASE):
        if any(col in cleaned.lower() for col in finance_cols):
            cleaned = re.sub(r'\bfrom\s*$', 'FROM finance_sheets', cleaned, flags=re.IGNORECASE)
        elif any(col in cleaned.lower() for col in project_cols):
            cleaned = re.sub(r'\bfrom\s*$', 'FROM crm_pipeline_and_projects', cleaned, flags=re.IGNORECASE)
        elif any(col in cleaned.lower() for col in employee_cols):
            cleaned = re.sub(r'\bfrom\s*$', 'FROM hrms_data', cleaned, flags=re.IGNORECASE)
            
    # Add back the semicolon
    return cleaned + ";"


# --- API Data Models ---
class ChatRequest(BaseModel):
    question: str

# --- Endpoints ---

@app.get("/api/kpis/latest")
def get_latest_kpis():
    """Returns the top-level KPI strip data."""
    try:
        fin_df = run_query("SELECT * FROM finance_sheets ORDER BY month DESC LIMIT 1")
        if fin_df.empty:
            return {"error": "No financial data"}
        row = fin_df.iloc[0]
        delta_pct = ((row["actual_revenue"] - row["target_revenue"]) / row["target_revenue"] * 100) if row["target_revenue"] else 0
        
        # Calculate Average CSAT and total pipeline
        csat_df = run_query("SELECT AVG(csat_score) as avg_csat FROM crm_pipeline_and_projects WHERE csat_score > 0")
        avg_csat = csat_df.iloc[0]["avg_csat"] if not csat_df.empty else 0.0
        if avg_csat is None:
            avg_csat = 0.0
            
        pipe_df = run_query("SELECT SUM(pipeline_value) as total_pipeline FROM crm_pipeline_and_projects")
        pipeline = pipe_df.iloc[0]["total_pipeline"] if not pipe_df.empty else 0.0
        if pipeline is None:
            pipeline = 0.0
        
        return {
            "month": row["month"],
            "actual_revenue": float(row["actual_revenue"]),
            "revenue_delta_pct": float(round(delta_pct, 1)),
            "mrr": float(row["mrr"]),
            "pipeline": float(pipeline),
            "avg_csat": float(round(avg_csat, 1))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/kpis/history")
def get_kpi_history():
    """Returns the full time-series for the charts."""
    try:
        df = run_query("SELECT month, target_revenue, actual_revenue, mrr FROM finance_sheets ORDER BY month ASC")
        # convert numeric types to float for JSON serialization
        df['target_revenue'] = df['target_revenue'].astype(float)
        df['actual_revenue'] = df['actual_revenue'].astype(float)
        df['mrr'] = df['mrr'].astype(float)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def fallback_sql_generator(question: str) -> str:
    """Keyword-based query parser to act as a fallback when the Gemini API is rate-limited."""
    q = question.lower()
    
    # 1. Projects and billable hours / CSAT / blockers
    if 'billable' in q or 'hours' in q:
        return "SELECT project_name, billable_hours, partner_lead FROM crm_pipeline_and_projects ORDER BY billable_hours DESC;"
    if 'csat' in q or 'score' in q or 'satisfied' in q:
        return "SELECT project_name, csat_score, client_name FROM crm_pipeline_and_projects ORDER BY csat_score DESC;"
    if 'blocker' in q or 'blocked' in q:
        return "SELECT project_name, client_name, partner_lead FROM crm_pipeline_and_projects WHERE blockers_flag = 'Yes';"
    if 'delayed' in q or 'milestone' in q or 'delay' in q:
        return "SELECT project_name, client_name, milestone_status FROM crm_pipeline_and_projects WHERE milestone_status = 'Delayed';"
    if 'project' in q:
        return "SELECT project_name, client_name, partner_lead, milestone_status FROM crm_pipeline_and_projects;"
        
    # 2. Employees and headcounts
    if 'headcount' in q or 'employee' in q or 'staff' in q or 'people' in q:
        if 'highest' in q or 'max' in q or 'most' in q or 'top' in q:
            return "SELECT department, current_headcount FROM hrms_data ORDER BY current_headcount DESC LIMIT 1;"
        return "SELECT department, current_headcount, active_hirings, attrition_count FROM hrms_data ORDER BY current_headcount DESC;"
    if 'department' in q:
        return "SELECT department, current_headcount FROM hrms_data;"
        
    # 3. Revenue / MRR / Pipeline / financial performance
    if 'revenue' in q or 'mrr' in q or 'financial' in q or 'performance' in q:
        return "SELECT month, target_revenue, actual_revenue, mrr FROM finance_sheets ORDER BY month DESC;"
    if 'pipeline' in q:
        return "SELECT client_name, project_name, pipeline_value FROM crm_pipeline_and_projects ORDER BY pipeline_value DESC;"
        
    return None


@app.post("/api/chat")
def ask_data_warehouse(req: ChatRequest):
    """Handles the Natural Language to SQL logic."""
    schema_doc = """
    TABLE finance_sheets (month TEXT, target_revenue NUMERIC, actual_revenue NUMERIC, mrr NUMERIC, arr NUMERIC)
    TABLE hrms_data (department TEXT, current_headcount INTEGER, active_hirings INTEGER, attrition_count INTEGER, month TEXT)
    TABLE crm_pipeline_and_projects (client_name TEXT, project_name TEXT, partner_lead TEXT, deal_stage TEXT, pipeline_value NUMERIC, billable_hours NUMERIC, milestone_status TEXT, blockers_flag TEXT, csat_score NUMERIC, renewal_intent TEXT)
    """
    
    # 1. Generate SQL (Now with Two-Shot Prompting and Stronger System Prompt)
    system = (
        "You are a PostgreSQL expert. You must return ONLY a single, valid, single-line "
        "PostgreSQL SELECT statement. Never include markdown, backticks, or explanations. "
        "Only query tables that are defined in the schema: finance_sheets, hrms_data, crm_pipeline_and_projects. "
    )
    
    prompt = f"""DATABASE SCHEMA:
{schema_doc}

USER QUESTION: Which department has the highest headcount?
SQL: SELECT department FROM hrms_data ORDER BY current_headcount DESC LIMIT 1;

USER QUESTION: Which project has the highest billable hours?
SQL: SELECT project_name FROM crm_pipeline_and_projects ORDER BY billable_hours DESC LIMIT 1;

USER QUESTION: {req.question}
SQL:"""

    try:
        raw_sql = _call_llm(prompt, system=system, max_tokens=200).strip()
        
        # Clean up just in case it still tries to add markdown
        raw_sql = raw_sql.replace("```sql", "").replace("```", "").replace("\n", " ").strip()
        
        # Auto-correct and clean SQL (handles truncation like dim_ to dim_projects)
        raw_sql = clean_sql(raw_sql)
        
        print(f"\n--- DEBUG: RAW LLM OUTPUT (CLEANED) ---\n{raw_sql}\n---------------------------------------\n")
    except Exception as e:
        # Check if we have a keyword-based fallback SQL query
        fallback_sql = fallback_sql_generator(req.question)
        if fallback_sql:
            raw_sql = fallback_sql
            print(f"\n--- DEBUG: LLM FAILED. USING KEYWORD FALLBACK SQL ---\n{raw_sql}\n----------------------------------------------------\n")
        else:
            return {"sql": None, "answer": f"LLM Generation failed: {str(e)}", "data": []}
    
    if "INVALID" in raw_sql.upper() or not raw_sql.upper().startswith("SELECT"):
        return {"sql": None, "answer": "Could not map question to database schema.", "data": []}


    # 2. Execute SQL
    try:
        result_df = run_query(raw_sql)
        data_json = result_df.to_dict(orient="records")
    except Exception as e:
        return {"sql": raw_sql, "answer": f"Query execution failed: {str(e)}", "data": []}

    # 3. Synthesize Answer (with robust error recovery if LLM synthesis fails / rate-limited)
    try:
        preview = result_df.head(10).to_string(index=False)
        synth_prompt = f"QUESTION: {req.question}\nQUERY RESULTS:\n{preview}\n\nSummarise the answer in one clear, executive-level sentence. No markdown."
        answer = _call_llm(synth_prompt, max_tokens=120)
        
        if not answer or answer.startswith("Error:"):
            raise Exception(answer or "Empty response")
    except Exception as e:
        # Smart fallback: build a data-driven summary from the actual results
        if len(data_json) == 0:
            answer = "No matching records found."
        elif len(data_json) == 1:
            # For a single row, enumerate all key-value pairs
            row = data_json[0]
            pairs = [f"{k.replace('_', ' ').title()}: {v}" for k, v in row.items() if v is not None]
            answer = " | ".join(pairs)
        else:
            # For multiple rows, summarize based on column type
            cols = list(data_json[0].keys())
            # Find the first text column to use as label
            label_col = next((c for c in cols if result_df[c].dtype == object), cols[0])
            # Find numeric columns for aggregation
            num_cols = [c for c in cols if result_df[c].dtype != object]
            
            top_label = data_json[0].get(label_col, '')
            
            if num_cols:
                top_num_col = num_cols[0]
                top_val = data_json[0].get(top_num_col, '')
                answer = (
                    f"{len(data_json)} records found. "
                    f"Top result: {label_col.replace('_', ' ').title()} = '{top_label}' "
                    f"with {top_num_col.replace('_', ' ')} = {top_val}."
                )
            else:
                labels = [str(row.get(label_col, '')) for row in data_json[:5]]
                answer = f"{len(data_json)} records found: {', '.join(labels)}" + (" and more." if len(data_json) > 5 else ".")

    return {
        "sql": raw_sql,
        "answer": answer,
        "data": data_json
    }



@app.get("/api/briefing")
def get_executive_briefing():
    """Generates the AI Chief of Staff weekly briefing."""
    try:
        # 1. Gather the latest data snapshot
        fin_df = run_query("SELECT * FROM finance_sheets ORDER BY month DESC LIMIT 1")
        hc_df = run_query("SELECT SUM(current_headcount) as total, SUM(active_hirings) as hirings, SUM(attrition_count) as attrition FROM hrms_data")
        csat_df = run_query("SELECT AVG(csat_score) as avg_csat, COUNT(*) as active_projects FROM crm_pipeline_and_projects WHERE csat_score > 0")
        projects_df = run_query("SELECT * FROM crm_pipeline_and_projects")
        pipe_df = run_query("SELECT SUM(pipeline_value) as total_pipeline FROM crm_pipeline_and_projects")

        fin = fin_df.iloc[0].to_dict() if not fin_df.empty else {}
        hc = hc_df.iloc[0].to_dict() if not hc_df.empty else {}
        csat = csat_df.iloc[0].to_dict() if not csat_df.empty else {}
        pipeline = pipe_df.iloc[0]["total_pipeline"] if not pipe_df.empty else 0.0
        
        blockers = projects_df[projects_df["blockers_flag"] == "Yes"]["project_name"].tolist() if not projects_df.empty else []
        delayed = projects_df[projects_df["milestone_status"] == "Delayed"]["project_name"].tolist() if not projects_df.empty else []

        # 2. Build the snapshot text
        snapshot = f"""
        FINANCIAL SNAPSHOT (latest month: {fin.get('month','N/A')})
        - Actual Revenue : ${float(fin.get('actual_revenue', 0) or 0):,.0f}
        - MRR            : ${float(fin.get('mrr', 0) or 0):,.0f}
        - Weighted Pipeline: ${float(pipeline or 0):,.0f}

        PEOPLE
        - Total Headcount : {hc.get('total', 0)} employees
        - Open Reqs       : {hc.get('hirings', 0)}
        - Attrition       : {hc.get('attrition', 0)} this period

        DELIVERY
        - Average CSAT  : {float(csat.get('avg_csat', 0) or 0):.2f}/5.0
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