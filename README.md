# 🎯 Smart Rekryteringsrekommendationer

En AI-driven rekommendationsmotor för rekryteringskampanjer som analyserar över 10,000 historiska kampanjer för att ge träffsäkra rekommendationer om budget, kanalmix och förväntade resultat.

## ✨ Funktioner

### 🏢 Branschmedveten Rekommendationsmotor
- **203 unika roll-bransch kombinationer** för ultra-specifika rekommendationer
- Intelligent matchning med semantisk likhet (sentence-transformers)
- Anpassade strategier per bransch (t.ex. Butikschef inom Dagligvaror vs Mode)

### 💰 Automatiska Budgetrekommendationer
- **Tre nivåer**: Grundläggande, Rekommenderad, Premium
- Data-driven baserat på framgångsrika kampanjer
- Visar förväntade klick och framgångssannolikhet

### 📊 Kanaloptimering
- Rekommenderar optimal mix av sociala medier
- Performance score för varje kanal
- Historisk CTR och CPC per plattform

### 🎨 Modern UI med Dark Theme
- Förbättrad kontrast och läsbarhet
- Interaktiva visualiseringar med Plotly
- Responsiv design

## 🚀 Kom igång

### Installation

```bash
# Klona repot
git clone [repo-url]
cd recommendation-python

# Installera dependencies
pip install -r requirements.txt
```

### Kör applikationen

```bash
streamlit run Home.py
```

Öppna sedan http://localhost:8502 i din webbläsare.

## 📁 Projektstruktur

```
recommendation-python/
├── Home.py                    # Huvudapplikation (Streamlit)
├── pages/                     # Streamlit-sidor
│   └── 1_📋_Alla_Roller.py   # Översikt av alla roller
├── src/
│   └── engines/              # Rekommendationsmotorer
│       ├── recommendation_engine_v3.py  # Branschmedveten motor
│       └── budget_recommender.py        # Budgetrekommendationer
├── data/
│   ├── raw/                  # Rådata från BigQuery
│   └── processed/            # Processad data
│       └── all_platforms_campaigns_complete.csv  # Huvuddataset
├── scripts/                  # Databearbetningsskript
└── requirements.txt          # Python dependencies
```

## 💡 Användning

### Exempel: Butikschef - Dagligvaror

1. Välj **Roll**: Butikschef
2. Välj **Bransch**: Dagligvaror
3. Välj **Kampanjlängd**: 30 dagar
4. Välj **Budgetnivå**: Rekommenderad

**Resultat:**
- Budget: 1,110 SEK
- Förväntade klick: ~1,600
- Rekommenderad kanal: Facebook (4.46% CTR)

### Exempel: Utvecklare - IT & Tech

1. Välj **Roll**: Utvecklare
2. Välj **Bransch**: IT & Tech
3. Välj **Kampanjlängd**: 30 dagar
4. Välj **Budgetnivå**: Premium

**Resultat:**
- Budget: 1,860 SEK
- Förväntade klick: ~135
- Högre CPC men nischad målgrupp

## 📊 Data

Systemet analyserar:
- **10,966 kampanjer** från verklig data
- **4 plattformar**: Facebook, LinkedIn, Snapchat, TikTok
- **50+ olika roller**
- **30+ branscher**

## 🔧 Teknisk Stack

- **Python 3.9+**
- **Streamlit** - Web framework
- **Pandas** - Databearbetning
- **Sentence-Transformers** - Semantisk likhet
- **Plotly** - Visualiseringar
- **scikit-learn** - ML utilities

## 📈 Framtida Förbättringar

- [ ] Integration med BigQuery för realtidsdata
- [ ] A/B-test rekommendationer
- [ ] Export av kampanjrapporter
- [ ] API för programmatisk access
- [ ] Fler ML-modeller (XGBoost, Neural Networks)

## 📝 License

[Din license här]

## 👥 Kontakt

För frågor eller feedback, kontakta [din kontaktinfo]