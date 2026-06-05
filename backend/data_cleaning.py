import pandas as pd
import sqlite3
import os

def clean_and_transform_data():
    
    # Check if raw files exist
    if not (os.path.exists("company_data/finance_sheets.csv") and 
            os.path.exists("company_data/hrms_data.csv") and 
            os.path.exists("company_data/crm_pipeline_and_projects.csv")):
        print("Error: Missing raw CSV files in directory!")
        return

    # ----------------------------------------------------
    # 1. CLEANING: HRMS Data (Employee Headcount)
    # ----------------------------------------------------
    df_hrms = pd.read_csv("company_data/hrms_data.csv")
    
    # Trim whitespace from text columns and standardize casing
    df_hrms['department'] = df_hrms['department'].str.strip().str.title()
    
    # Handle negative numbers or anomalies if they happen
    df_hrms['current_headcount'] = df_hrms['current_headcount'].clip(lower=0)
    df_hrms['active_hirings'] = df_hrms['active_hirings'].fillna(0).astype(int)
    df_hrms['attrition_count'] = df_hrms['attrition_count'].fillna(0).astype(int)
    
    print("HRMS data cleaned.")

    # ----------------------------------------------------
    # 2. CLEANING: CRM & Project Management Data
    # ----------------------------------------------------
    df_crm = pd.read_csv("company_data/crm_pipeline_and_projects.csv")
    
    # Text sanitization
    df_crm['client_name'] = df_crm['client_name'].str.strip()
    df_crm['project_name'] = df_crm['project_name'].str.strip()
    df_crm['deal_stage'] = df_crm['deal_stage'].str.strip().str.title()
    df_crm['milestone_status'] = df_crm['milestone_status'].str.strip().str.title()
    df_crm['blockers_flag'] = df_crm['blockers_flag'].str.strip().str.title()
    
    # Fill structural missing numerical values safely
    df_crm['billable_hours'] = df_crm['billable_hours'].fillna(0.0)
    df_crm['csat_score'] = df_crm['csat_score'].fillna(0.0)
    df_crm['pipeline_value'] = df_crm['pipeline_value'].fillna(0.0)
    
    # ADVANCED RULE: Calculate weighted partner pipeline using business logic mapping
    stage_weights = {
        "Closed Won": 1.0,
        "Negotiation": 0.7,
        "Proposal": 0.5,
        "Qualification": 0.1,
        "Not Started": 0.0
    }
    
    # Map probabilities and compute individual weighted values
    df_crm['weighted_value'] = df_crm['pipeline_value'] * df_crm['deal_stage'].map(stage_weights).fillna(0.0)
    
    # Aggregate total weighted pipeline across all active deals
    total_weighted_pipeline = df_crm['weighted_value'].sum()
    
    print("CRM & Project Pipeline data cleaned and weighted values calculated.")

    # ----------------------------------------------------
    # 3. CLEANING: Finance Sheets (Revenue)
    # ----------------------------------------------------
    df_finance = pd.read_csv("company_data/finance_sheets.csv")
    
    # Ensure dates match standard ISO YYYY-MM formatting
    df_finance['month'] = df_finance['month'].str.strip()
    
    # Force float formatting on currency metrics
    for col in ['target_revenue', 'actual_revenue', 'mrr', 'arr']:
        df_finance[col] = pd.to_numeric(df_finance[col], errors='coerce').fillna(0.0)
        
    # Inject our newly calculated operational CRM metric into the Finance Fact record
    df_finance['total_weighted_pipeline'] = total_weighted_pipeline
    
    print("Finance sheets cleaned and integrated with CRM pipeline.")

    # ----------------------------------------------------
    # 4. LOADING: Push Pristine Data into Star Schema Warehouse
    # ----------------------------------------------------
    conn = sqlite3.connect("company_kpis.db")
    
    # Overwrite data tables with perfectly clean, typed structures
    df_hrms[['department', 'current_headcount', 'active_hirings', 'attrition_count']].to_sql(
        'dim_employees', conn, if_exists='replace', index=False
    )
    
    df_crm[['client_name', 'project_name', 'partner_lead', 'billable_hours', 'milestone_status', 'blockers_flag', 'csat_score', 'renewal_intent']].to_sql(
        'dim_projects', conn, if_exists='replace', index=False
    )
    
    df_finance[['month', 'target_revenue', 'actual_revenue', 'mrr', 'arr', 'total_weighted_pipeline']].to_sql(
        'fact_business_performance', conn, if_exists='replace', index=False
    )
    
    conn.commit()
    conn.close()
    print(" Data Warehouse 'company_kpis.db' refreshed with 100% clean data.")

if __name__ == "__main__":
    clean_and_transform_data()