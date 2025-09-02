#!/usr/bin/env python3
"""
Script för att ladda upp existerande data till BigQuery
"""

import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import os
import sys
from pathlib import Path

def create_dataset_and_tables(client, project_id, dataset_id="recruitment_demo"):
    """Skapa dataset och tabeller i BigQuery"""
    
    # Skapa dataset om det inte finns
    dataset_id_full = f"{project_id}.{dataset_id}"
    dataset = bigquery.Dataset(dataset_id_full)
    dataset.location = "EU"  # Ändra till din region
    dataset.description = "Recruitment campaign data and training data"
    
    try:
        dataset = client.create_dataset(dataset, timeout=30)
        print(f"✅ Skapade dataset {dataset_id}")
    except Exception as e:
        if "Already Exists" in str(e):
            print(f"ℹ️ Dataset {dataset_id} finns redan")
        else:
            print(f"❌ Fel vid skapande av dataset: {e}")
            return False
    
    # Definiera tabellscheman
    campaigns_schema = [
        bigquery.SchemaField("Roll", "STRING"),
        bigquery.SchemaField("Storlek_pa_Stad", "STRING"),
        bigquery.SchemaField("Location", "STRING"),
        bigquery.SchemaField("Platform", "STRING"),
        bigquery.SchemaField("Impressions", "INTEGER"),
        bigquery.SchemaField("Clicks", "INTEGER"),
        bigquery.SchemaField("Spend_SEK", "FLOAT"),
        bigquery.SchemaField("CTR_Percent", "FLOAT"),
        bigquery.SchemaField("CPC_SEK", "FLOAT"),
        bigquery.SchemaField("Campaign_Days", "INTEGER"),
        bigquery.SchemaField("Daily_Spend", "FLOAT"),
        bigquery.SchemaField("Meta", "BOOLEAN"),
        bigquery.SchemaField("LinkedIn", "BOOLEAN"),
        bigquery.SchemaField("Snapchat", "BOOLEAN"),
        bigquery.SchemaField("Reddit", "BOOLEAN"),
        bigquery.SchemaField("TikTok", "BOOLEAN"),
        bigquery.SchemaField("Company", "STRING"),
        bigquery.SchemaField("Campaign_ID", "STRING"),
        bigquery.SchemaField("Campaign_Name", "STRING"),
    ]
    
    training_schema = [
        bigquery.SchemaField("Roll", "STRING"),
        bigquery.SchemaField("Paket", "STRING"),
        bigquery.SchemaField("Kanaler", "STRING"),
        bigquery.SchemaField("Budget", "INTEGER"),
    ]
    
    # Skapa campaigns-tabell
    table_id = f"{project_id}.{dataset_id}.campaigns"
    table = bigquery.Table(table_id, schema=campaigns_schema)
    table.description = "Campaign performance data"
    
    try:
        table = client.create_table(table)
        print(f"✅ Skapade tabell campaigns")
    except Exception as e:
        if "Already Exists" in str(e):
            print(f"ℹ️ Tabell campaigns finns redan")
        else:
            print(f"❌ Fel vid skapande av campaigns-tabell: {e}")
    
    # Skapa training_data-tabell
    table_id = f"{project_id}.{dataset_id}.training_data"
    table = bigquery.Table(table_id, schema=training_schema)
    table.description = "Training data for recommendations"
    
    try:
        table = client.create_table(table)
        print(f"✅ Skapade tabell training_data")
    except Exception as e:
        if "Already Exists" in str(e):
            print(f"ℹ️ Tabell training_data finns redan")
        else:
            print(f"❌ Fel vid skapande av training_data-tabell: {e}")
    
    return True

def upload_campaigns_data(client, project_id, dataset_id="recruitment_demo"):
    """Ladda upp kampanjdata till BigQuery"""
    
    # Leta efter kampanjdata
    campaign_file = Path("data/processed/campaigns_clean_for_bigquery.csv")
    if not campaign_file.exists():
        print(f"❌ Hittar inte {campaign_file}")
        return False
    
    print(f"📊 Läser {campaign_file}...")
    df = pd.read_csv(campaign_file)
    print(f"  - {len(df)} rader")
    
    # Data är redan rensad
    print(f"  - Data redan rensad och klar")
    
    # Ladda upp till BigQuery
    table_id = f"{project_id}.{dataset_id}.campaigns"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",  # Ersätt existerande data
    )
    
    try:
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        print(f"✅ Laddade upp {len(df)} kampanjer till BigQuery")
        return True
    except Exception as e:
        print(f"❌ Fel vid uppladdning av kampanjdata: {e}")
        return False

def upload_training_data(client, project_id, dataset_id="recruitment_demo"):
    """Ladda upp träningsdata till BigQuery"""
    
    # Leta efter träningsdata
    training_file = Path("Träningsdata Ragnarsson.xlsx")
    if not training_file.exists():
        print(f"⚠️ Hittar inte {training_file}, hoppar över träningsdata")
        return True  # Inte kritiskt fel
    
    print(f"📊 Läser {training_file}...")
    df = pd.read_excel(training_file)
    print(f"  - {len(df)} rader")
    
    # Ladda upp till BigQuery
    table_id = f"{project_id}.{dataset_id}.training_data"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
    )
    
    try:
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        print(f"✅ Laddade upp {len(df)} träningsrader till BigQuery")
        return True
    except Exception as e:
        print(f"❌ Fel vid uppladdning av träningsdata: {e}")
        return False

def main():
    """Huvudfunktion"""
    
    print("🚀 BigQuery Upload Script")
    print("=" * 50)
    
    # Kontrollera autentisering
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        print("\n❌ GOOGLE_APPLICATION_CREDENTIALS är inte satt!")
        print("\nGör så här:")
        print("1. Skapa en service account i Google Cloud Console")
        print("2. Ladda ner JSON-nyckeln")
        print("3. Kör: export GOOGLE_APPLICATION_CREDENTIALS='path/to/key.json'")
        sys.exit(1)
    
    # Initiera BigQuery client
    try:
        credentials = service_account.Credentials.from_service_account_file(
            os.environ['GOOGLE_APPLICATION_CREDENTIALS']
        )
        
        with open(os.environ['GOOGLE_APPLICATION_CREDENTIALS']) as f:
            import json
            service_account_info = json.load(f)
            project_id = service_account_info['project_id']
        
        client = bigquery.Client(credentials=credentials, project=project_id)
        print(f"✅ Ansluten till projekt: {project_id}")
        
    except Exception as e:
        print(f"❌ Kunde inte ansluta till BigQuery: {e}")
        sys.exit(1)
    
    # Skapa dataset och tabeller
    print("\n📦 Skapar dataset och tabeller...")
    if not create_dataset_and_tables(client, project_id):
        print("❌ Kunde inte skapa dataset/tabeller")
        sys.exit(1)
    
    # Ladda upp data
    print("\n📤 Laddar upp data...")
    
    if upload_campaigns_data(client, project_id):
        print("✅ Kampanjdata uppladdad")
    else:
        print("❌ Misslyckades med kampanjdata")
        sys.exit(1)
    
    if upload_training_data(client, project_id):
        print("✅ Träningsdata uppladdad")
    
    print("\n🎉 Klart! Data finns nu i BigQuery")
    print(f"\nDu kan nu:")
    print(f"1. Deploya appen till Streamlit Cloud")
    print(f"2. Lägg till service account JSON i Streamlit secrets")
    print(f"3. Appen hämtar data direkt från BigQuery")

if __name__ == "__main__":
    main()
