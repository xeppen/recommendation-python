# 🚀 Deploy till Streamlit Cloud (UTAN känslig data)

## Säker deployment utan att exponera känslig data

### Steg 1: Förbered projektet

1. **All känslig data är redan exkluderad från Git** via `.gitignore`:
   - ✅ Alla CSV-filer
   - ✅ Alla Excel-filer  
   - ✅ All kampanjdata

2. **Verifiera att data INTE är med i Git:**
   ```bash
   git status
   # CSV och Excel filer ska INTE visas
   ```

### Steg 2: Skapa demo-data (valfritt)

Om du vill ha en demo online med fejkad data:

```bash
# Skapa en minimal demo-datafil
python3 create_demo_data.py
```

### Steg 3: Deploy till Streamlit Cloud

1. **Gå till:** https://streamlit.io/cloud
2. **Logga in** med GitHub
3. **Välj:** "New app"
4. **Repository:** `xeppen/recommendation-python`
5. **Branch:** `main`
6. **Main file:** `Home.py`
7. **Klicka:** Deploy!

### Steg 4: Ladda upp data säkert

Efter deployment kan ni:

#### Alternativ A: Manuell uppladdning via UI
- Modifiera appen så användare kan ladda upp CSV/Excel
- Data sparas endast i session, inte permanent

#### Alternativ B: Streamlit Secrets
- Lägg känslig data i Streamlit Cloud secrets
- Endast du har tillgång till dessa

#### Alternativ C: Privat databas
- Anslut till privat databas (t.ex. Google Sheets med API-nyckel)
- Data hämtas on-demand, lagras aldrig publikt

---

## 🔒 Säkerhetsåtgärder

### Vad som INTE pushas till GitHub:
- ❌ `all_platforms_campaigns_complete.csv`
- ❌ `Träningsdata Ragnarsson.xlsx`
- ❌ All kampanjdata
- ❌ Alla CSV/Excel-filer

### Vad som pushas:
- ✅ Python-kod
- ✅ Requirements.txt
- ✅ README och dokumentation
- ✅ Docker-filer

---

## 📤 Implementera fil-uppladdning

Lägg till detta i `Home.py` för att låta användare ladda upp data:

```python
# I sidebar
uploaded_file = st.file_uploader(
    "Ladda upp kampanjdata (CSV)", 
    type=['csv', 'xlsx'],
    help="Data sparas endast under sessionen"
)

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    st.session_state['campaign_data'] = df
    st.success("Data uppladdad!")
```

---

## 🌐 Alternativ: Lokal tunnel (ngrok)

Om ni vill dela appen tillfälligt utan att deploya:

1. **Installera ngrok:**
   ```bash
   brew install ngrok  # Mac
   # eller ladda ner från ngrok.com
   ```

2. **Starta appen lokalt:**
   ```bash
   streamlit run Home.py
   ```

3. **Skapa publik tunnel:**
   ```bash
   ngrok http 8501
   ```

4. **Dela länken** (giltig i 8 timmar gratis)

---

## 🎯 Rekommendation

**För er situation:**

1. **Bäst:** Deploy till Streamlit Cloud UTAN data + lägg till fil-uppladdning
2. **Alternativ:** Använd ngrok för tillfällig delning
3. **Säkrast:** Docker lokalt på varje dator

---

## ⚙️ Streamlit Cloud Inställningar

Efter deployment, gå till app settings:

### Secrets (för API-nycklar etc):
```toml
[general]
# Lägg eventuella API-nycklar här
# OPENAI_API_KEY = "sk-..."

[database]
# Eventuell databas-connection
# url = "postgresql://..."
```

### Advanced settings:
- Python version: 3.9
- Install command: `pip install -r requirements.txt`
- Secrets: Lägg känslig info här, inte i koden

---

## 📝 Checklista innan deployment

- [ ] Kör `git status` - inga datafiler ska visas
- [ ] Kontrollera `.gitignore` innehåller alla känsliga filer
- [ ] Testa appen lokalt först
- [ ] Överväg att lägga till autentisering
- [ ] Dokumentera för användare hur de laddar upp data

---

## 🔐 Lägg till lösenordsskydd (valfritt)

```python
# I Home.py
def check_password():
    """Returns `True` if the user had the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "Password", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Password", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if not check_password():
    st.stop()
```
