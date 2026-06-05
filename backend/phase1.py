import pandas as pd
import sqlite3

def build_central_warehouse():
    # 1. Connect to local database engine
    conn = sqlite3.connect("company_kpis.db")
    cursor = conn.cursor()
    
    # 2. Read your raw mock data csv files
    df_finance = pd.read_csv("company_data/finance_sheets.csv")
    df_hrms = pd.read_csv("company_data/hrms_data.csv")
    df_crm = pd.read_csv("company_data/crm_pipeline_and_projects.csv")
    
    # 3. Create the target Dimension tables (Descriptive Entities)
    # Dimension: Employees
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_employees (
            department TEXT PRIMARY KEY,
            current_headcount INTEGER,
            active_hirings INTEGER,
            attrition_count INTEGER
        )
    """)
    
    # Dimension: Project & Client Tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_projects (
            client_name TEXT PRIMARY KEY,
            project_name TEXT,
            partner_lead TEXT,
            billable_hours REAL,
            milestone_status TEXT,
            blockers_flag TEXT,
            csat_score REAL,
            renewal_intent TEXT
        )
    """)
    
    # 4. Create the central Fact table (Quantifiable Metrics)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fact_business_performance (
            month TEXT PRIMARY KEY,
            target_revenue REAL,
            actual_revenue REAL,
            mrr REAL,
            arr REAL,
            total_weighted_pipeline REAL
        )
    """)
    
    # 5. Transform and map Pandas dataframes cleanly into your SQL tables
    # Load dimensions
    df_hrms[['department', 'current_headcount', 'active_hirings', 'attrition_count']].to_sql('dim_employees', conn, if_exists='replace', index=False)
    df_crm[['client_name', 'project_name', 'partner_lead', 'billable_hours', 'milestone_status', 'blockers_flag', 'csat_score', 'renewal_intent']].to_sql('dim_projects', conn, if_exists='replace', index=False)
    
    # Calculate weighted partner pipeline value from CRM to pass to Fact table
    # Standard weighting pipeline rule: Negotiation/Proposal pipeline is worth roughly 50%
    total_pipeline = (df_crm['pipeline_value'].sum()) * 0.50
    df_finance['total_weighted_pipeline'] = total_pipeline
    
    # Load central fact performance table
    df_finance.to_sql('fact_business_performance', conn, if_exists='replace', index=False)
    
    conn.commit()
    print("Database built successfully! 'company_kpis.db' is ready for Gemini queries.")
    conn.close()

if __name__ == "__main__":
    build_central_warehouse()