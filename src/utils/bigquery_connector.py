#!/usr/bin/env python3
"""
BigQuery connector for real-time data access
"""

import pandas as pd
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import json
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BigQueryConnector:
    """Handle BigQuery connections and queries"""
    
    def __init__(self, use_streamlit_secrets: bool = True):
        """
        Initialize BigQuery connection
        
        Args:
            use_streamlit_secrets: If True, use Streamlit secrets for credentials
        """
        self.client = None
        self.project_id = None
        self.dataset_id = "recruitment_demo"  # Demo dataset för test
        self.initialize_connection(use_streamlit_secrets)
    
    def initialize_connection(self, use_streamlit_secrets: bool):
        """Setup BigQuery client with authentication"""
        try:
            # Försök först med miljövariabler
            if os.getenv('GCP_PRIVATE_KEY'):
                # Bygg service account info från miljövariabler
                service_account_info = {
                    "type": os.getenv('GCP_TYPE', 'service_account'),
                    "project_id": os.getenv('GCP_PROJECT_ID'),
                    "private_key_id": os.getenv('GCP_PRIVATE_KEY_ID'),
                    "private_key": os.getenv('GCP_PRIVATE_KEY').replace('\\n', '\n'),
                    "client_email": os.getenv('GCP_CLIENT_EMAIL'),
                    "client_id": os.getenv('GCP_CLIENT_ID'),
                    "auth_uri": os.getenv('GCP_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
                    "token_uri": os.getenv('GCP_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
                    "auth_provider_x509_cert_url": os.getenv('GCP_AUTH_PROVIDER_CERT_URL', 'https://www.googleapis.com/oauth2/v1/certs'),
                    "client_x509_cert_url": os.getenv('GCP_CLIENT_CERT_URL'),
                    "universe_domain": os.getenv('GCP_UNIVERSE_DOMAIN', 'googleapis.com')
                }
                credentials = service_account.Credentials.from_service_account_info(
                    service_account_info
                )
                self.project_id = os.getenv('GCP_PROJECT_ID')
                self.dataset_id = os.getenv('GCP_DATASET_ID', 'recruitment_demo')
            elif use_streamlit_secrets and 'gcp_service_account' in st.secrets:
                # Använd Streamlit secrets för deployment
                credentials = service_account.Credentials.from_service_account_info(
                    st.secrets["gcp_service_account"]
                )
                self.project_id = st.secrets["gcp_service_account"]["project_id"]
            elif os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
                # Använd miljövariabel för lokal utveckling
                credentials = service_account.Credentials.from_service_account_file(
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS']
                )
                with open(os.environ['GOOGLE_APPLICATION_CREDENTIALS']) as f:
                    service_account_info = json.load(f)
                    self.project_id = service_account_info['project_id']
            else:
                # Fallback till default credentials
                from google.auth import default
                credentials, self.project_id = default()
            
            self.client = bigquery.Client(
                credentials=credentials,
                project=self.project_id
            )
            
        except Exception as e:
            st.error(f"❌ Kunde inte ansluta till BigQuery: {str(e)}")
            self.client = None
    
    @st.cache_data(ttl=3600)  # Cache i 1 timme
    def get_campaign_data(_self) -> Optional[pd.DataFrame]:
        """
        Fetch campaign data from BigQuery
        
        Returns:
            DataFrame with campaign data or None if error
        """
        if not _self.client:
            return None
        
        query = f"""
        SELECT 
            Roll,
            Storlek_pa_Stad,
            Location,
            Platform,
            Impressions,
            Clicks,
            Spend_SEK,
            CTR_Percent,
            CPC_SEK,
            Campaign_Days,
            Daily_Spend,
            Meta,
            LinkedIn,
            Snapchat,
            Reddit,
            TikTok,
            Company,
            Campaign_ID,
            Campaign_Name
        FROM `{_self.project_id}.{_self.dataset_id}.campaigns`
        WHERE Campaign_Name NOT LIKE '%Employer Branding%'
        """
        
        try:
            df = _self.client.query(query).to_dataframe()
            return df
        except Exception as e:
            st.error(f"❌ Fel vid hämtning av data: {str(e)}")
            return None
    
    @st.cache_data(ttl=3600)
    def get_training_data(_self) -> Optional[pd.DataFrame]:
        """
        Fetch training data from BigQuery
        
        Returns:
            DataFrame with training data or None if error
        """
        if not _self.client:
            return None
        
        query = f"""
        SELECT 
            Roll,
            Paket,
            Kanaler,
            Budget
        FROM `{_self.project_id}.{_self.dataset_id}.training_data`
        """
        
        try:
            df = _self.client.query(query).to_dataframe()
            return df
        except Exception as e:
            st.error(f"❌ Fel vid hämtning av träningsdata: {str(e)}")
            return None
    
    def upload_campaign_data(self, df: pd.DataFrame, table_name: str = "campaigns"):
        """
        Upload campaign data to BigQuery
        
        Args:
            df: DataFrame to upload
            table_name: Target table name
        """
        if not self.client:
            st.error("❌ Ingen BigQuery-anslutning")
            return False
        
        table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
        
        # BigQuery schema
        job_config = bigquery.LoadJobConfig(
            schema=[
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
            ],
            write_disposition="WRITE_TRUNCATE",  # Ersätt existerande data
        )
        
        try:
            job = self.client.load_table_from_dataframe(
                df, table_id, job_config=job_config
            )
            job.result()  # Vänta på att jobbet är klart
            
            st.success(f"✅ Laddat upp {len(df)} rader till BigQuery")
            return True
            
        except Exception as e:
            st.error(f"❌ Fel vid uppladdning: {str(e)}")
            return False
    
    def upload_training_data(self, df: pd.DataFrame):
        """Upload training data to BigQuery"""
        if not self.client:
            return False
        
        table_id = f"{self.project_id}.{self.dataset_id}.training_data"
        
        job_config = bigquery.LoadJobConfig(
            schema=[
                bigquery.SchemaField("Roll", "STRING"),
                bigquery.SchemaField("Paket", "STRING"),
                bigquery.SchemaField("Kanaler", "STRING"),
                bigquery.SchemaField("Budget", "INTEGER"),
            ],
            write_disposition="WRITE_TRUNCATE",
        )
        
        try:
            job = self.client.load_table_from_dataframe(
                df, table_id, job_config=job_config
            )
            job.result()
            st.success(f"✅ Träningsdata uppladdad till BigQuery")
            return True
        except Exception as e:
            st.error(f"❌ Fel vid uppladdning av träningsdata: {str(e)}")
            return False
    
    def get_role_statistics(self, role: str) -> Dict[str, Any]:
        """Get statistics for a specific role"""
        if not self.client:
            return {}
        
        query = f"""
        SELECT 
            Platform,
            AVG(CTR_Percent) as avg_ctr,
            AVG(CPC_SEK) as avg_cpc,
            COUNT(*) as campaign_count,
            SUM(Clicks) as total_clicks,
            SUM(Spend_SEK) as total_spend
        FROM `{self.project_id}.{self.dataset_id}.campaigns`
        WHERE LOWER(Roll) = LOWER(@role)
        GROUP BY Platform
        ORDER BY campaign_count DESC
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("role", "STRING", role)
            ]
        )
        
        try:
            results = self.client.query(query, job_config=job_config).to_dataframe()
            return results.to_dict('records')
        except Exception as e:
            st.error(f"❌ Fel vid hämtning av rollstatistik: {str(e)}")
            return {}
    
    def test_connection(self) -> bool:
        """Test if BigQuery connection works"""
        if not self.client:
            return False
        
        try:
            # Enkel query för att testa anslutningen
            query = f"SELECT 1 as test FROM `{self.project_id}.{self.dataset_id}.campaigns` LIMIT 1"
            self.client.query(query).result()
            return True
        except:
            return False

# Hjälpfunktion för Streamlit
@st.cache_resource
def get_bigquery_connector():
    """Get or create BigQuery connector instance"""
    return BigQueryConnector()
