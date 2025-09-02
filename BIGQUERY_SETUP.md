# 🚀 BigQuery Setup Guide

## Arkitektur

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Streamlit  │────▶│   BigQuery   │◀────│   Admin     │
│     App     │     │   Database   │     │   Upload    │
└─────────────┘     └──────────────┘     └─────────────┘
      ▲                     │                     ▲
      │                     │                     │
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Users     │     │ Service Acc. │     │  CSV/Excel  │
└─────────────┘     └──────────────┘     └─────────────┘
```

## Steg 1: Skapa Service Account i Google Cloud

1. **Gå till Google Cloud Console:**
   https://console.cloud.google.com

2. **Välj eller skapa projekt:**
   - Använd befintligt projekt: `ga4-test-385808`
   - Eller skapa nytt projekt för detta

3. **Aktivera BigQuery API:**
   ```bash
   gcloud services enable bigquery.googleapis.com
   ```

4. **Skapa Service Account:**
   ```bash
   # Skapa service account
   gcloud iam service-accounts create recruitment-app \
     --display-name="Recruitment App Service Account"
   
   # Ge nödvändiga rättigheter
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:recruitment-app@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/bigquery.dataEditor"
   
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:recruitment-app@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/bigquery.jobUser"
   ```

5. **Ladda ner Service Account nyckel:**
   ```bash
   gcloud iam service-accounts keys create service-account-key.json \
     --iam-account=recruitment-app@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

## Steg 2: Ladda upp data till BigQuery

1. **Sätt miljövariabel:**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="service-account-key.json"
   ```

2. **Kör upload-script:**
   ```bash
   python3 upload_to_bigquery.py
   ```

Detta skapar:
- Dataset: `recruitment_data`
- Tabell: `campaigns` (med all kampanjdata)
- Tabell: `training_data` (med träningsdata)

## Steg 3: Uppdatera appen för BigQuery

Appen behöver modifieras för att använda BigQuery istället för lokala filer:

```python
# I Home.py, ersätt filläsning med:
from src.utils.bigquery_connector import get_bigquery_connector

# Hämta data från BigQuery
bq = get_bigquery_connector()
campaigns_df = bq.get_campaign_data()
training_df = bq.get_training_data()
```

## Steg 4: Deploy till Streamlit Cloud

### 4.1 Förbered secrets

Skapa `.streamlit/secrets.toml` lokalt (lägg INTE i Git!):

```toml
[gcp_service_account]
type = "service_account"
project_id = "YOUR_PROJECT_ID"
private_key_id = "YOUR_KEY_ID"
private_key = "YOUR_PRIVATE_KEY"
client_email = "recruitment-app@YOUR_PROJECT_ID.iam.gserviceaccount.com"
client_id = "YOUR_CLIENT_ID"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "YOUR_CERT_URL"
```

### 4.2 Deploy appen

1. Push kod till GitHub (utan data!)
2. Gå till https://streamlit.io/cloud
3. Deploy från GitHub
4. Lägg till secrets i Streamlit Cloud settings

## Steg 5: Testa anslutningen

```python
# test_bigquery.py
from src.utils.bigquery_connector import BigQueryConnector

# Testa anslutning
bq = BigQueryConnector(use_streamlit_secrets=False)
if bq.test_connection():
    print("✅ BigQuery fungerar!")
    
    # Hämta data
    df = bq.get_campaign_data()
    print(f"Hämtade {len(df)} kampanjer")
else:
    print("❌ Kunde inte ansluta")
```

## Fördelar med BigQuery

✅ **Säkerhet:** Data ligger säkert i Google Cloud
✅ **Skalbarhet:** Hanterar miljontals rader utan problem
✅ **Realtid:** Alltid senaste data
✅ **Delning:** Flera användare samtidigt
✅ **Backup:** Automatisk backup i Google Cloud
✅ **Kostnadseffektivt:** Gratis upp till 10GB/månad

## Kostnader

### Gratis nivå:
- 10 GB lagring per månad
- 1 TB queries per månad
- Perfekt för er användning!

### Om ni överskrider:
- Lagring: $0.02 per GB/månad
- Queries: $5 per TB

## Säkerhet

### Best practices:
1. **Använd alltid Service Accounts** (inte personliga konton)
2. **Minimal rättigheter** (endast läs/skriv till specifikt dataset)
3. **Rotera nycklar** regelbundet
4. **Använd Streamlit Secrets** för känslig info
5. **Logga access** via Cloud Audit Logs

## Alternativ arkitektur

### Option A: Read-only web app
- Web-appen kan bara läsa från BigQuery
- Admin laddar upp data via separat script

### Option B: Full CRUD
- Web-appen kan både läsa och skriva
- Användare kan ladda upp nya kampanjer direkt

### Option C: Hybrid
- Läsning för alla användare
- Skrivning endast för admin (lösenordsskyddat)

## Felsökning

### "Permission denied"
```bash
# Kontrollera rättigheter
gcloud projects get-iam-policy YOUR_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:recruitment-app@"
```

### "Table not found"
```bash
# Lista tabeller
bq ls recruitment_data
```

### "Quota exceeded"
- Kontrollera användning i Cloud Console
- Överväg att cacha queries längre

## SQL Queries för analys

När data finns i BigQuery kan ni köra avancerade analyser:

```sql
-- Top-performing kanaler per roll
SELECT 
  Roll,
  Platform,
  AVG(CTR_Percent) as avg_ctr,
  AVG(CPC_SEK) as avg_cpc,
  COUNT(*) as campaigns
FROM `project.recruitment_data.campaigns`
GROUP BY Roll, Platform
HAVING campaigns > 5
ORDER BY avg_ctr DESC;

-- Trend över tid
SELECT 
  DATE_TRUNC(PARSE_DATE('%Y%m%d', SUBSTR(Campaign_ID, 1, 8)), MONTH) as month,
  AVG(CTR_Percent) as avg_ctr
FROM `project.recruitment_data.campaigns`
GROUP BY month
ORDER BY month;
```
