# 🚀 Demo Setup Guide - we-select-data-dev

## Snabbstart (5 minuter)

Vi använder **we-select-data-dev-422614** projektet för demo!

### Steg 1: Kör setup-script
```bash
# Kör automatisk setup
./setup_bigquery_demo.sh
```

Detta skapar automatiskt:
- ✅ Service account: `recruitment-app-demo`
- ✅ BigQuery dataset: `recruitment_demo`
- ✅ Nödvändiga rättigheter
- ✅ Service account nyckel: `service-account-demo.json`

### Steg 2: Ladda upp data
```bash
# Sätt miljövariabel
export GOOGLE_APPLICATION_CREDENTIALS="service-account-demo.json"

# Ladda upp data till BigQuery
python3 upload_to_bigquery.py
```

### Steg 3: Testa lokalt
```bash
# Testa att allt fungerar
python3 -c "
from src.utils.bigquery_connector import BigQueryConnector
bq = BigQueryConnector(use_streamlit_secrets=False)
if bq.test_connection():
    print('✅ BigQuery fungerar!')
    df = bq.get_campaign_data()
    print(f'Hämtade {len(df)} kampanjer')
"
```

## Deploy till Streamlit Cloud

### 1. Förbered secrets

Kopiera innehållet från `service-account-demo.json` till Streamlit secrets:

```toml
# .streamlit/secrets.toml (lokalt test)
# ELLER i Streamlit Cloud Settings

[gcp_service_account]
type = "service_account"
project_id = "we-select-data-dev-422614"
private_key_id = "COPY_FROM_JSON"
private_key = "COPY_FROM_JSON"
client_email = "recruitment-app-demo@we-select-data-dev-422614.iam.gserviceaccount.com"
client_id = "COPY_FROM_JSON"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "COPY_FROM_JSON"
```

### 2. Deploy

1. Push kod till GitHub
2. På Streamlit Cloud:
   - New app → Välj ditt repo
   - Advanced settings → Secrets
   - Klistra in service account JSON
3. Deploy!

## Vad finns i BigQuery?

Efter uppladdning har du:

```
we-select-data-dev-422614
└── recruitment_demo (dataset)
    ├── campaigns (tabell)
    │   └── 10,966 kampanjer
    └── training_data (tabell)
        └── Träningsdata från Excel
```

## Testa i BigQuery Console

```sql
-- Se första 10 kampanjerna
SELECT * 
FROM `we-select-data-dev-422614.recruitment_demo.campaigns`
LIMIT 10;

-- Top roller
SELECT Roll, COUNT(*) as antal
FROM `we-select-data-dev-422614.recruitment_demo.campaigns`
GROUP BY Roll
ORDER BY antal DESC
LIMIT 10;

-- Bästa plattform per roll
SELECT 
  Roll,
  Platform,
  AVG(CTR_Percent) as avg_ctr,
  COUNT(*) as campaigns
FROM `we-select-data-dev-422614.recruitment_demo.campaigns`
GROUP BY Roll, Platform
HAVING campaigns > 5
ORDER BY Roll, avg_ctr DESC;
```

## Kostnader

**we-select-data-dev** är ett utvecklingsprojekt, så:
- ✅ Gratis BigQuery-kvot räcker gott
- ✅ 10GB lagring gratis/månad
- ✅ 1TB queries gratis/månad
- ✅ Er data: ~5MB = 0.05% av gratis kvot

## Säkerhet

För demo:
- ⚠️ Använd INTE produktionsdata
- ✅ Service account har bara tillgång till `recruitment_demo`
- ✅ Ingen känslig data i Git
- ✅ Rotera nycklar efter demo

## Felsökning

### "Permission denied"
```bash
# Kontrollera att du är i rätt projekt
gcloud config get-value project
# Ska visa: we-select-data-dev-422614
```

### "Dataset not found"
```bash
# Lista datasets
bq ls --project_id=we-select-data-dev-422614
```

### "API not enabled"
```bash
gcloud services enable bigquery.googleapis.com \
  --project=we-select-data-dev-422614
```

## Nästa steg

1. **Modifiera appen** för att använda BigQuery:
   ```python
   # I Home.py
   from src.utils.bigquery_connector import get_bigquery_connector
   
   @st.cache_resource
   def load_data():
       bq = get_bigquery_connector()
       return bq.get_campaign_data()
   ```

2. **Lägg till fil-uppladdning** (valfritt):
   - Låt användare ladda upp ny data
   - Spara direkt till BigQuery

3. **Produktionsmiljö**:
   - Skapa separat dataset för produktion
   - Striktare säkerhet
   - Backup-rutiner

## Support

Vid problem:
1. Kolla att `PROJECT_ID` är rätt: `we-select-data-dev-422614`
2. Verifiera att du har tillgång till projektet
3. Kontrollera service account permissions
