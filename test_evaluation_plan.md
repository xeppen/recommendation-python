# Utvärderingsplan för Rekommendationsmotorn

## 🎯 Syfte
Jämföra AI-rekommendationernas träffsäkerhet mot operationsteamets erfarenhet och faktiska kampanjresultat.

## 📊 Testscenarier

### 1. **A/B-testning med historisk data**
- Välj 10-20 lyckade kampanjer från databasen
- Låt teamet gissa vilka kanaler som användes baserat på roll/bransch/budget
- Jämför med AI:ns rekommendationer
- Jämför båda mot faktiska resultat

### 2. **Blindtest**
- Presentera 5 nya rekryteringsbehov (roller som finns i systemet)
- Låt både AI och teamet rekommendera kanalmix
- Dokumentera och jämför förslagen
- Följ upp med faktiska resultat när kampanjerna körs

### 3. **Edge Cases**
Testa systemet med:
- Ovanliga roller (t.ex. "Kärnfysiker", "Sommelier")
- Små budgetar (<5000 SEK)
- Mycket stora budgetar (>100 000 SEK)
- Olika branscher för samma roll

## 🔍 Utvärderingsmetriker

### Kvantitativa mått:
1. **Träffsäkerhet på kanalmix** - % rätt kanaler jämfört med historisk data
2. **CTR-prediktion** - Avvikelse från faktisk CTR
3. **Budget-effektivitet** - Föreslagen vs faktisk CPC
4. **Similarity Score** - Hur väl systemet matchar liknande roller

### Kvalitativa mått:
1. **Relevans** - Känns rekommendationerna rimliga?
2. **Förklarbarhet** - Förstår teamet varför vissa kanaler rekommenderas?
3. **Tillit** - Skulle teamet våga följa rekommendationerna?
4. **Insikter** - Upptäcker systemet mönster teamet missat?

## 🧪 Testprotokoll

### Steg 1: Baseline-test
```
Roll: [Välj från systemet]
Bransch: [Om tillgänglig]
Budget: [Välj tier]
Kampanjlängd: [Antal dagar]

Teamets gissning:
- Kanaler: ___________
- Förväntad CTR: _____
- Förväntad CPC: _____

AI:s rekommendation:
- Kanaler: ___________
- Förväntad CTR: _____
- Förväntad CPC: _____

Faktiskt resultat (om tillgängligt):
- Kanaler: ___________
- CTR: _____
- CPC: _____
```

### Steg 2: Dokumentera avvikelser
- Där AI och team är oense
- Där båda har fel jämfört med historisk data
- Överraskande insikter

## 🐛 Kända begränsningar att testa

1. **Datakvalitet**
   - Roller med få datapunkter (<5 kampanjer)
   - Branscher som saknas i träningsdata
   - Säsongsvariationer (sommar vs vinter)

2. **Systemets antaganden**
   - Antar att historisk prestanda = framtida prestanda
   - Viktar alla kampanjer lika (oavsett ålder)
   - Ignorerar externa faktorer (konkurrens, marknadstrender)

3. **Edge cases**
   - Nya plattformar (t.ex. Threads, BeReal)
   - Hybridroller (t.ex. "IT-sjuksköterska")
   - Extremt nischade roller

## 📈 Förbättringsförslag att utvärdera

1. **Viktning av data**
   - Ge nyare kampanjer högre vikt
   - Justera för säsong
   - Vikta baserat på kampanjstorlek

2. **Fler features**
   - Inkludera företagsstorlek
   - Lägg till tidpunkt på året
   - Konkurrensnivå i branschen

3. **Feedback-loop**
   - Låt teamet rätta AI:ns rekommendationer
   - Spara justeringar som ny träningsdata
   - Kontinuerlig förbättring

## 🎬 Hur du testar appen

1. **Öppna appen** (bör köra på http://localhost:8501)

2. **Grundtest:**
   - Sök på vanliga roller: "Sjuksköterska", "Utvecklare", "Säljare"
   - Notera similarity score - över 0.7 är bra, under 0.5 är tveksamt

3. **Jämförelsetest:**
   - Ta en kampanj från `all_platforms_campaigns_complete.csv`
   - Mata in samma roll/budget i appen
   - Jämför rekommendation med faktisk kanalmix

4. **Stresstest:**
   - Testa med felstavningar: "Sjuksköterksa"
   - Testa med engelska: "Nurse", "Developer"
   - Testa med komplexa titlar: "Senior DevOps Engineer med AWS-certifiering"

5. **Branschtest:**
   - Samma roll, olika branscher
   - Se hur rekommendationerna ändras

## 📝 Rapportmall

```markdown
### Testdatum: [DATUM]
### Testare: [NAMN]

#### Test #1
- Input: Roll: ___, Bransch: ___, Budget: ___
- AI Rekommendation: ___
- Team Rekommendation: ___
- Faktiskt resultat: ___
- Kommentar: ___

#### Sammanfattning:
- AI träffsäkerhet: ___%
- Team träffsäkerhet: ___%
- Överraskande insikter: ___
- Förbättringsförslag: ___
```

## 🚀 Nästa steg

1. Kör 10 tester enligt protokollet
2. Dokumentera resultat
3. Identifiera mönster där AI/team har fel
4. Justera modellen baserat på feedback
5. Upprepa tester
