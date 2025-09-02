# 🚀 Snabbguide - Testa Rekommendationsmotorn

## Starta appen
```bash
python3 -m streamlit run Home.py
```
Öppna sedan: http://localhost:8501

## 5 Snabba tester att köra direkt

### Test 1: Vanlig roll ✅
1. Sök: "Sjuksköterska"
2. Välj bransch: "Vård"
3. Kampanjlängd: 30 dagar
4. **Förväntat:** 
   - Similarity score > 0.8
   - Facebook som huvudkanal
   - CTR ~3.11%

### Test 2: Liknande roll 🔄
1. Sök: "Ambulanssjuksköterska"
2. **Förväntat:**
   - Hittar "Sjuksköterska" som match
   - Similarity score 0.7-0.9
   - Liknande rekommendationer som Test 1

### Test 3: IT-roll 💻
1. Sök: "Utvecklare"
2. Välj bransch: "IT"
3. **Förväntat:**
   - LinkedIn som huvudkanal
   - Lägre CTR än vård
   - Högre CPC

### Test 4: Felstavning 🔤
1. Sök: "Sjuksköterksa" (felstavat)
2. **Förväntat:**
   - Hittar ändå "Sjuksköterska"
   - Similarity score ~0.8

### Test 5: Okänd roll ❓
1. Sök: "Astronaut"
2. **Förväntat:**
   - Låg similarity score (<0.5)
   - Generiska rekommendationer
   - Möjlighet att lägga till manuell data

## Vad ska du kolla efter?

### 🟢 BRA tecken:
- Similarity score > 0.7 för kända roller
- Rekommendationer matchar er erfarenhet
- Budget-tiers känns rimliga
- CTR/CPC stämmer med era kampanjer

### 🔴 VARNINGSSIGNALER:
- Similarity score < 0.5 för vanliga roller
- Orimliga budgetrekommendationer
- CTR som verkar för hög/låg
- Samma rekommendation för helt olika roller

## Jämför med verklig data

1. Öppna `data/processed/all_platforms_campaigns_complete.csv`
2. Filtrera på en roll (t.ex. "Sjuksköterska")
3. Kolla genomsnittlig CTR och CPC
4. Jämför med appens rekommendationer

### Exempel-jämförelse:
```
VERKLIG DATA (Sjuksköterska, Facebook):
- CTR: 2.5-3.5%
- CPC: 15-25 SEK
- Budget: 10,000-20,000 SEK

APPENS REKOMMENDATION:
- CTR: ____%
- CPC: ____ SEK
- Budget: _____ SEK

Avvikelse: ____%
```

## Rapportera issues

Om något verkar fel:
1. Ta screenshot
2. Notera:
   - Exakt input
   - Förväntad output
   - Faktisk output
3. Spara i `feedback/` mappen

## Tips för teamutvärdering

1. **Blindtest:** Låt teamet gissa kanalmix för en roll, jämför sedan med AI
2. **Historisk validering:** Ta 5 gamla lyckade kampanjer, se om AI hade rekommenderat samma
3. **Edge cases:** Testa med udda roller eller extrema budgetar
4. **Branschvariation:** Samma roll i olika branscher

## Snabbkoll - Fungerar allt?

- [ ] Appen startar utan fel
- [ ] Sökfunktionen hittar roller
- [ ] Similarity scores visas
- [ ] Budgetrekommendationer visas
- [ ] Kanalrekommendationer är rimliga
- [ ] Språkbyte fungerar (SE/EN)
- [ ] "Alla Roller" sidan laddas

## Kontakt vid problem
Om appen kraschar eller ger konstiga resultat, kör:
```bash
# Visa felmeddelanden
cat streamlit.log

# Kontrollera data
python3 -c "import pandas as pd; df = pd.read_csv('data/processed/all_platforms_campaigns_complete.csv'); print(df.info())"
```
