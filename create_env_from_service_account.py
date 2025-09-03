#!/usr/bin/env python3
"""
Script to create .env file from service account JSON
"""

import json
import os

def create_env_from_json():
    """Create .env file from service-account-demo.json"""
    
    json_file = "service-account-demo.json"
    env_file = ".env"
    
    if not os.path.exists(json_file):
        print(f"❌ {json_file} not found. Run ./setup_bigquery_demo.sh first")
        return
    
    try:
        with open(json_file, 'r') as f:
            service_account = json.load(f)
        
        env_content = f"""# Google Cloud Service Account Configuration
# Generated from {json_file}

# Project settings
GCP_PROJECT_ID={service_account['project_id']}
GCP_DATASET_ID=recruitment_demo

# Service Account Credentials
GCP_TYPE={service_account['type']}
GCP_PRIVATE_KEY_ID={service_account['private_key_id']}
GCP_PRIVATE_KEY="{service_account['private_key']}"
GCP_CLIENT_EMAIL={service_account['client_email']}
GCP_CLIENT_ID={service_account['client_id']}
GCP_AUTH_URI={service_account['auth_uri']}
GCP_TOKEN_URI={service_account['token_uri']}
GCP_AUTH_PROVIDER_CERT_URL={service_account['auth_provider_x509_cert_url']}
GCP_CLIENT_CERT_URL={service_account['client_x509_cert_url']}
GCP_UNIVERSE_DOMAIN={service_account.get('universe_domain', 'googleapis.com')}

# Optional: OpenAI API Key for enhanced insights
# OPENAI_API_KEY=sk-your_openai_key_here
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Created {env_file} from {json_file}")
        print(f"🔒 {env_file} is gitignored for security")
        print(f"📝 Edit {env_file} to add OpenAI API key if needed")
        
        # Clean up JSON file
        os.remove(json_file)
        print(f"🗑️  Removed {json_file} for security")
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")

if __name__ == "__main__":
    create_env_from_json()
