# 🔐 Environment Variables Setup

## Säker hantering av Google Cloud credentials med miljövariabler

### Steg 1: Skapa .env fil

Skapa en `.env` fil i projektets root-directory:

```bash
# Google Cloud Service Account Configuration

# Project settings
GCP_PROJECT_ID=we-select-data-dev-422614
GCP_DATASET_ID=recruitment_demo

# Service Account Credentials
GCP_TYPE=service_account
GCP_PRIVATE_KEY_ID=3eb96b88fbd9b3ab09ec7067a8ea58c423421d44
GCP_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCduK00vDLNOouU\nUj9BRczvNGubLkXEzl64vYbQ8WXc8XtbQ6raHL64+LUvHavcZphcwgQQawrMkooU\nXcW+IgeK43Zd09vRhMC9peOvrXlhj0wOX1dKpWMrGHOWF8TjlpgvNch2KU6++bt6\nwg8lL1hSAMhedNWuMDFGKACmIIPJWMnxvU14RA6U0gEBDK2eN5AJ8ki36JMbLdkI\nZ18wQeN9p7YkdsGHA77OiX+uNY2E5qyBOsS+ehJ617/KuuoysD68KlwXySXtwV3K\nGGNWOnN1Ahj5tDM8iWWQrDNK7FFl91t1ELPe/udyxpnfKol8HhZYWq5935DI9eLm\ntO58hWGhAgMBAAECggEAEa3LrGeUAjEXyC5X7McYK4/ip+hN5buEHo0P+Ye1dUiU\nHSy+j+g88JrgJEHdK71MQsl0jyqQcVHTrGi+a4uA8O6CLA49S4Tn3dokZWK6glb/\nnXTOYg2byg7Zle9gIGqW8GPE7om+y+VOQHpUHETsT3TLANtzwCyiuUxuljB61Syz\nmQy0n3yaMuv2enV1zGE+iBk0npi0dVkrGdjG+Xq2iCRn8XhlRczB6Gkz4BSD5+bw\n3w9dQerKey4Jdjtf5mcY9cDv1vLQVc1aiS6HSGayLq2hOcAIjzhIPKuZzAt9ZBPg\nvYZCYE0P6Ghwol9X4ekp0DZA8GrwJ2IRIK6r2DPTSQKBgQDLrv4VSJw8fP4c9+Jw\nuD8G7L4wxEObIrDtujhgWtrRfq9BtgMi+0sUbLzzxdTpqL5x1dDo1s9inSnZdfMi\nu+WY06xpZf9lnAajkaWc0gwuy5om76JTOLK9aWVwXhXeNxHqQ6uppztTiy32yPJw\n761NuH6u74/dqwoH9rdWxv+prwKBgQDGO3zg6vXkpjbzxdbM+CApcSD4qhEsLCWk\nUVMAJh+hMfTlsdZsxlYNqSF/hsl3Tv1WjHWgek8o7pkJqJkB4OgVL5ZbPsOStyaJ\nwwpIQt/oVX8WpvxCCT7fvTO3t1WrBrTDvGguBeFDAQYYkaeafcSAFz/VyJU898n2\n3DQT8yWNrwKBgGtjStD75Gu71tp9EyUs7wX+odPiVmafprrf+MNMg5v6d/pkNUkn\nRpFxNzorbrL25dnsymVIhDTQ+fSOTG9es5Gc4IT9Yuc2mQV6T9/bmtK9Q/wNUf8g\noJRe0j2pTUxIqqhhn0smQZAtjEFV9wT2SN/2Ssx+v9I2UGacfFNDPh4/AoGBAKrW\nWaj81S1YkcNEnPnIXO9aL7Ad4O7QnSAfdgiK0nd5NjU+Li1QQJlFSTk+UCIiUPJl\n2nmS7uW3uuw4AKU9zsVzXYEFdkba0Luo+xOLjqwMAprjDkNa9HSd+hQ6S/o4rVCC\n7sW7C4dTOo2x+V+LQ+2gG8OCOhtw8P1uiPMoeRTBAoGBAJaUiB8Ze/tW0FtuE9CO\n06b+hNqiym5NFHYNt2rd9V0de+g5nirUmgprdac36dzVw0aYActFYRHDWID2qzph\nuxjzmYcESHCZAlEr13kK0Ceb8V4e/QtOPgxKs5RkAJAFHXNbQo+r/i/gkHsmw552\nQyv+5QoJ9q3KCyu1rBlZVeuz\n-----END PRIVATE KEY-----\n"
GCP_CLIENT_EMAIL=recruitment-app-demo@we-select-data-dev-422614.iam.gserviceaccount.com
GCP_CLIENT_ID=115115105183822631733
GCP_AUTH_URI=https://accounts.google.com/o/oauth2/auth
GCP_TOKEN_URI=https://oauth2.googleapis.com/token
GCP_AUTH_PROVIDER_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
GCP_CLIENT_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/recruitment-app-demo%40we-select-data-dev-422614.iam.gserviceaccount.com
GCP_UNIVERSE_DOMAIN=googleapis.com

# Optional: OpenAI API Key for enhanced insights
# OPENAI_API_KEY=sk-your_openai_key_here
```

### Steg 2: Säkerhet

- ✅ `.env` är redan i `.gitignore` - pushas INTE till Git
- ✅ Miljövariabler har prioritet över Streamlit Secrets
- ✅ Fungerar både lokalt och i produktion

### Steg 3: Testa lokalt

```bash
# Installera python-dotenv
pip install python-dotenv

# Starta appen
python3 -m streamlit run Home.py
```

Nu kommer BigQuery-anslutningen använda miljövariabler istället för JSON-fil!

### Steg 4: Streamlit Cloud deployment

För Streamlit Cloud kan du antingen:

**Option A: Använd Streamlit Secrets (som tidigare)**
- Lägg till service account JSON i app settings

**Option B: Använd Environment Variables**
- Lägg till miljövariabler i Streamlit Cloud settings:
  - `GCP_PROJECT_ID`
  - `GCP_PRIVATE_KEY`
  - `GCP_CLIENT_EMAIL`
  - etc.

### Fördelar med miljövariabler:

1. **Säkerhet** - Ingen JSON-fil att glömma i Git
2. **Flexibilitet** - Enkelt att byta mellan miljöer
3. **Standard** - Industristandard för secrets
4. **Automation** - Enkelt att sätta i CI/CD

### Automatisk konvertering

För att konvertera från service account JSON till .env:

```bash
python3 create_env_from_service_account.py
```

Detta skapar `.env` från `service-account-demo.json` och tar bort JSON-filen säkert.
