# 🚀 Installationsguide - Rekommendationsmotor

## Välj det alternativ som passar dig bäst:

---

## 🌐 Alternativ 1: Streamlit Cloud (ENKLAST - Ingen installation!)

### Fördelar:
- ✅ Ingen installation krävs
- ✅ Fungerar på alla enheter med webbläsare
- ✅ Automatiska uppdateringar
- ✅ Delbar länk till hela teamet

### Steg:
1. Be Sebastian deploya till Streamlit Cloud
2. Få en länk som: `https://your-app.streamlit.app`
3. Öppna i webbläsaren - klart!

---

## 🐳 Alternativ 2: Docker (REKOMMENDERAT för lokal körning)

### Fördelar:
- ✅ Fungerar identiskt på alla datorer
- ✅ Ingen Python-installation krävs
- ✅ Ett kommando för att starta

### Installation:
1. **Installera Docker Desktop:**
   - Mac: https://docs.docker.com/desktop/install/mac-install/
   - Windows: https://docs.docker.com/desktop/install/windows-install/

2. **Ladda ner projektet:**
   ```bash
   git clone https://github.com/xeppen/recommendation-python.git
   cd recommendation-python
   ```

3. **Starta appen:**
   ```bash
   docker-compose up
   ```

4. **Öppna i webbläsaren:**
   http://localhost:8501

### Stoppa appen:
```bash
docker-compose down
```

---

## 💻 Alternativ 3: Direkt Python-installation

### Fördelar:
- ✅ Full kontroll
- ✅ Kan modifiera koden enkelt

### Installation:

#### Mac/Linux:
```bash
# 1. Klona projektet
git clone https://github.com/xeppen/recommendation-python.git
cd recommendation-python

# 2. Skapa virtuell miljö
python3 -m venv venv
source venv/bin/activate

# 3. Installera beroenden
pip install -r requirements.txt

# 4. Starta appen
streamlit run Home.py
```

#### Windows:
```powershell
# 1. Klona projektet
git clone https://github.com/xeppen/recommendation-python.git
cd recommendation-python

# 2. Skapa virtuell miljö
python -m venv venv
venv\Scripts\activate

# 3. Installera beroenden
pip install -r requirements.txt

# 4. Starta appen
streamlit run Home.py
```

---

## 📦 Alternativ 4: Standalone App (Kommer snart)

Vi kan skapa en .exe/.app fil, MEN:
- ⚠️ Blir mycket stor (500MB+)
- ⚠️ Kan trigga antivirus
- ⚠️ Svår att uppdatera
- ⚠️ Streamlit är inte optimerat för detta

Om ni verkligen vill ha detta, kan vi använda:
- **PyInstaller** eller **Nuitka**
- **Electron** wrapper
- **Briefcase** för native apps

---

## 🎯 Snabbstart för kollegor

### Om Docker är installerat:
```bash
# Ett kommando - that's it!
docker run -p 8501:8501 ghcr.io/xeppen/recommendation-python:latest
```

### Om Python finns:
```bash
# Tre kommandon
git clone https://github.com/xeppen/recommendation-python.git
cd recommendation-python
pip install -r requirements.txt && streamlit run Home.py
```

---

## 🆘 Felsökning

### Problem: "Port 8501 redan används"
```bash
# Hitta och stoppa processen
lsof -i :8501  # Mac/Linux
netstat -ano | findstr :8501  # Windows

# Eller använd annan port
streamlit run Home.py --server.port 8502
```

### Problem: "Module not found"
```bash
pip install -r requirements.txt --force-reinstall
```

### Problem: "Permission denied"
```bash
# Mac/Linux
sudo chmod +x run.sh
./run.sh

# Windows - kör som administratör
```

---

## 📱 Mobil/Tablet access

Om appen körs lokalt på din dator:
1. Se till att enheter är på samma nätverk
2. Hitta din IP-adress:
   - Mac: `ifconfig | grep inet`
   - Windows: `ipconfig`
3. På mobilen, gå till: `http://[DIN-IP]:8501`

---

## 🔐 Säkerhet

För känslig data, överväg:
- VPN för fjärråtkomst
- Lösenordsskydd (kan läggas till)
- Kryptering av datafiler
- Privat GitHub-repo ✅ (redan gjort)

---

## 💡 Tips

1. **För icke-tekniska användare:** Använd Streamlit Cloud eller Docker
2. **För utvecklare:** Direkt Python-installation
3. **För företagsmiljö:** Docker eller Kubernetes
4. **För demo:** Streamlit Cloud

---

## 📞 Support

Vid problem, kontakta Sebastian med:
- Screenshot av felmeddelande
- Vilket alternativ du försökte
- Din dator (Mac/Windows/Linux)
