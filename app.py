import streamlit as st
import pandas as pd
import numpy as np
import faiss
from openai import OpenAI

# Initiera OpenAI client
client = OpenAI()

# Cacha inläsning av data
@st.cache_data
def load_data():
    df = pd.read_excel("Träningsdata Ragnarsson.xlsx", sheet_name="Ny träningsdata")
    return df

# Cacha embeddings och FAISS-index
@st.cache_resource
def build_index(df):
    roles = df["Roll"].unique().tolist()

    def get_embedding(text: str) -> list:
        emb = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return emb.data[0].embedding

    role_embeddings = [get_embedding(role) for role in roles]

    # Använd cosine similarity istället för L2
    d = len(role_embeddings[0])
    index = faiss.IndexFlatIP(d)  # Inner Product för cosine similarity
    # Normalisera embeddings för cosine similarity
    normalized_embeddings = []
    for emb in role_embeddings:
        emb_array = np.array(emb).astype("float32")
        norm = np.linalg.norm(emb_array)
        normalized_embeddings.append(emb_array / norm)
    
    index.add(np.array(normalized_embeddings))

    return roles, index, get_embedding

# Hjälpfunktion för att hitta ordstammar
def find_word_stem_matches(job_title: str, roles: list) -> list:
    """Hittar roller som delar ordstammar med input-jobbet"""
    job_lower = job_title.lower()
    stem_matches = []
    
    # Vanliga svenska yrkessuffix och ordstammar
    common_stems = ['ekonom', 'ingenjör', 'sköterska', 'läkare', 'tekniker', 'specialist', 'assistent']
    
    for stem in common_stems:
        if stem in job_lower:
            for role in roles:
                if stem in role.lower() and role.lower() != job_lower:
                    stem_matches.append((role, stem))
    
    return stem_matches

# AI-baserad branschkategorisering
def categorize_job_by_industry(job_title: str) -> str:
    """Använder AI för att kategorisera jobbroller efter bransch"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """Du är en expert på att kategorisera jobbroller efter bransch. 
                Svara endast med EN av följande kategorier:
                - Sjukvård
                - IT & Teknik  
                - Ekonomi & Finans
                - Försäljning & Marknadsföring
                - Utbildning
                - Juridik
                - Bygg & Hantverk
                - Transport & Logistik
                - Hotell & Restaurang
                - Retail & Handel
                - Offentlig sektor
                - Industri & Tillverkning
                - Media & Kreativt
                - Övrigt"""},
                {"role": "user", "content": f"Kategorisera denna jobbroll: {job_title}"}
            ],
            max_tokens=50,
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except:
        return "Övrigt"

# Funktion för att spara ny träningsdata
def save_new_training_data(job_title: str, senioritet: str, stad_storlek: str, 
                          paket: str, kanaler: list, budget: str, df):
    """Sparar ny träningsdata till Excel-filen"""
    try:
        # Skapa ny rad
        new_row = {
            "Roll": job_title,
            "Category": "Manuell input",  # Default category
            "Storlek på Stad": stad_storlek,
            "Senioritet": senioritet,
            "Antalet positioner": 1,  # Default
            "Produkt": paket,
            "Meta": "Meta" in kanaler,
            "LinkedIn": "LinkedIn" in kanaler,
            "Snapchat": "Snapchat" in kanaler,
            "Reddit": "Reddit" in kanaler,
            "TikTok": "TikTok" in kanaler,
            "Budget": budget
        }
        
        # Lägg till ny rad till DataFrame
        new_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        
        # Spara tillbaka till Excel
        new_df.to_excel("Träningsdata Ragnarsson.xlsx", sheet_name="Ny träningsdata", index=False)
        
        return True, "Data sparad framgångsrikt!"
    except Exception as e:
        return False, f"Fel vid sparning: {str(e)}"

# Rekommendationsfunktion
def recommend_package(job_title: str, senioritet: str, stad_storlek: str, roles, index, get_embedding, df):
    query_emb = np.array([get_embedding(job_title)]).astype("float32")
    # Normalisera query embedding för cosine similarity
    query_emb = query_emb / np.linalg.norm(query_emb)
    D, I = index.search(query_emb, k=10)  # D är nu cosine similarity scores
    
    # Filter matches based on seniority and city size
    best_match = None
    best_score = 0
    best_rec = None
    
    for i in range(len(I[0])):
        role_idx = I[0][i]
        matched_role = roles[role_idx]
        # D[0][i] är nu direkt cosine similarity (0-1)
        score = float(D[0][i])
        
        # Find matching records with role, seniority, and city size
        matching_records = df[
            (df["Roll"] == matched_role) & 
            (df["Senioritet"] == senioritet) & 
            (df["Storlek på Stad"] == stad_storlek)
        ]
        
        if not matching_records.empty:
            best_match = matched_role
            best_score = float(score)
            best_rec = matching_records.iloc[0]
            break
    
    # Förbättrad fallback med ordstammar och AI-branschkategorisering
    if best_match is None or best_score < 0.7:
        # Först: Kolla ordstammar (snabbare och mer exakt)
        stem_matches = find_word_stem_matches(job_title, roles)
        
        if stem_matches:
            # Hitta bästa ordstammatchning
            for role, stem in stem_matches:
                role_records = df[df["Roll"] == role]
                if not role_records.empty:
                    best_match = role
                    best_score = 0.85  # Hög score för ordstammatchning
                    best_rec = role_records.iloc[0]
                    break
        
        # Sedan: AI-branschkategorisering om ingen ordstam hittades
        if best_match is None:
            input_category = categorize_job_by_industry(job_title)
            
            # Hitta roller inom samma bransch
            same_industry_roles = []
            for role in roles:
                role_category = categorize_job_by_industry(role)
                if role_category == input_category:
                    same_industry_roles.append(role)
            
            # Sök bland roller i samma bransch först
            if same_industry_roles:
                industry_embeddings = [get_embedding(role) for role in same_industry_roles]
                industry_index = faiss.IndexFlatIP(len(industry_embeddings[0]))
                # Normalisera industry embeddings
                normalized_industry = []
                for emb in industry_embeddings:
                    emb_array = np.array(emb).astype("float32")
                    normalized_industry.append(emb_array / np.linalg.norm(emb_array))
                industry_index.add(np.array(normalized_industry))
                
                D_industry, I_industry = industry_index.search(query_emb, k=3)
                
                for i in range(len(I_industry[0])):
                    role_idx = I_industry[0][i]
                    matched_role = same_industry_roles[role_idx]
                    # D_industry[0][i] är nu cosine similarity
                    score = float(D_industry[0][i])
                    
                    # Hitta bästa matchning för denna roll (oavsett senioritet/stad)
                    role_records = df[df["Roll"] == matched_role]
                    if not role_records.empty:
                        best_match = matched_role
                        best_score = float(score)
                        best_rec = role_records.iloc[0]
                        break
    
    # Sista fallback: använd bästa embedding-matchning
    if best_match is None:
        best_match = roles[I[0][0]]
        best_score = float(D[0][0])  # Direkt cosine similarity
        best_rec = df[df["Roll"] == best_match].iloc[0]
    
    # Lägg till branschinfo för debugging
    input_branch = categorize_job_by_industry(job_title)
    matched_branch = categorize_job_by_industry(best_match)
    
    return {
        "input_title": job_title,
        "senioritet": senioritet,
        "stad_storlek": stad_storlek,
        "matched_role": best_match,
        "score": best_score,
        "input_branch": input_branch,
        "matched_branch": matched_branch,
        "produkt": best_rec["Produkt"],
        "kanaler": [k for k in ["Meta", "LinkedIn", "Snapchat", "Reddit", "TikTok"] if best_rec[k]],
        "budget": best_rec["Budget"]
    }

# ---------------------------
# Language Support
# ---------------------------

TRANSLATIONS = {
    "sv": {
        "title": "Jobbtitel → Rekommenderat annons-paket",
        "job_title": "Jobbtitel:",
        "job_title_placeholder": "t.ex. 'Narkossköterska'",
        "seniority": "Senioritetsnivå:",
        "city_size": "Stadsstorlek:",
        "recommendation": "Rekommendation",
        "input": "Input:",
        "matched_role": "Matchad roll:",
        "input_branch": "Input-bransch:",
        "matched_branch": "Matchad bransch:",
        "branches_no_match": "⚠️ Branscherna matchar inte!",
        "package": "Paket:",
        "channels": "Kanaler:",
        "budget": "Budget:",
        "good_match": "✅ Bra matchning!",
        "low_score_warning": "⚠️ Låg matchningsscore ({score:.2f}). Vill du förbättra systemet genom att ange korrekt rekommendation?",
        "manual_training": "🔧 Manuell träningsdata",
        "manual_training_info": "Ange korrekt rekommendation för denna kombination av jobbtitel, senioritet och stadsstorlek:",
        "correct_package": "Korrekt paket:",
        "correct_channels": "Korrekta kanaler:",
        "correct_budget": "Korrekt budget:",
        "save_training": "💾 Spara träningsdata",
        "select_channels": "Välj minst en kanal!",
        "data_saved": "Data sparad framgångsrikt!",
        "click_update": "🔄 Klicka på 'Uppdatera system' nedan för att använda den nya träningsdatan.",
        "update_system": "🔄 Uppdatera system",
        "update_help": "Laddar om träningsdata och bygger om AI-modellen",
        "language": "Språk / Language:"
    },
    "en": {
        "title": "Job Title → Recommended Ad Package",
        "job_title": "Job Title:",
        "job_title_placeholder": "e.g. 'Nurse'",
        "seniority": "Seniority Level:",
        "city_size": "City Size:",
        "recommendation": "Recommendation",
        "input": "Input:",
        "matched_role": "Matched role:",
        "input_branch": "Input industry:",
        "matched_branch": "Matched industry:",
        "branches_no_match": "⚠️ Industries don't match!",
        "package": "Package:",
        "channels": "Channels:",
        "budget": "Budget:",
        "good_match": "✅ Good match!",
        "low_score_warning": "⚠️ Low matching score ({score:.2f}). Do you want to improve the system by providing the correct recommendation?",
        "manual_training": "🔧 Manual Training Data",
        "manual_training_info": "Provide the correct recommendation for this combination of job title, seniority and city size:",
        "correct_package": "Correct package:",
        "correct_channels": "Correct channels:",
        "correct_budget": "Correct budget:",
        "save_training": "💾 Save Training Data",
        "select_channels": "Select at least one channel!",
        "data_saved": "Data saved successfully!",
        "click_update": "🔄 Click 'Update System' below to use the new training data.",
        "update_system": "🔄 Update System",
        "update_help": "Reloads training data and rebuilds AI model",
        "language": "Språk / Language:"
    }
}

SENIORITY_LEVELS = {
    "sv": ["Junior (0-2 år)", "Senior (2-3 år)", "Specialist (3+ år)", "Management"],
    "en": ["Junior (0-2 years)", "Senior (2-3 years)", "Specialist (3+ years)", "Management"]
}

CITY_SIZES = {
    "sv": ["Liten stad", "Mellanstor stad", "Stor stad"],
    "en": ["Small city", "Medium city", "Large city"]
}

PACKAGES = {
    "sv": ["Boost Bild", "Boost Video", "Två-stegare"],
    "en": ["Boost Image", "Boost Video", "Two-step"]
}

BUDGETS = {
    "sv": ["10,000-15,000", "15,000-20,000", "25,000-30,000", "30,000+"],
    "en": ["10,000-15,000", "15,000-20,000", "25,000-30,000", "30,000+"]
}

# Conversion functions to handle Swedish data in database
def convert_to_swedish_values(senioritet, stad_storlek, language):
    """Convert UI values to Swedish database values"""
    if language == "sv":
        return senioritet, stad_storlek
    
    # Convert English to Swedish
    seniority_map = {
        "Junior (0-2 years)": "Junior (0-2 år)",
        "Senior (2-3 years)": "Senior (2-3 år)", 
        "Specialist (3+ years)": "Specialist (3+ år)",
        "Management": "Management"
    }
    
    city_map = {
        "Small city": "Liten stad",
        "Medium city": "Mellanstor stad",
        "Large city": "Stor stad"
    }
    
    return seniority_map.get(senioritet, senioritet), city_map.get(stad_storlek, stad_storlek)

# ---------------------------
# Streamlit UI
# ---------------------------

# Language selector
language = st.selectbox(
    "Språk / Language:",
    ["sv", "en"],
    format_func=lambda x: "🇸🇪 Svenska" if x == "sv" else "🇬🇧 English"
)

t = TRANSLATIONS[language]

st.title(t["title"])

df = load_data()
roles, index, get_embedding = build_index(df)

# Input fields
col1, col2, col3 = st.columns(3)

with col1:
    job_title = st.text_input(t["job_title"], placeholder=t["job_title_placeholder"])

with col2:
    senioritet = st.selectbox(
        t["seniority"],
        SENIORITY_LEVELS[language]
    )

with col3:
    stad_storlek = st.selectbox(
        t["city_size"],
        CITY_SIZES[language]
    )

if job_title:
    # Convert UI values to Swedish database values
    senioritet_sv, stad_storlek_sv = convert_to_swedish_values(senioritet, stad_storlek, language)
    result = recommend_package(job_title, senioritet_sv, stad_storlek_sv, roles, index, get_embedding, df)

    st.subheader(t["recommendation"])
    st.write(f"**{t['input']}** {result['input_title']} | {result['senioritet']} | {result['stad_storlek']}")
    st.write(f"**{t['matched_role']}** {result['matched_role']} (score {result['score']:.2f})")
    
    # Visa branschkategorisering
    col_branch1, col_branch2 = st.columns(2)
    with col_branch1:
        st.write(f"🏢 **{t['input_branch']}** {result['input_branch']}")
    with col_branch2:
        st.write(f"🏢 **{t['matched_branch']}** {result['matched_branch']}")
    
    # Varning om branscherna inte matchar
    if result['input_branch'] != result['matched_branch']:
        st.warning(f"{t['branches_no_match']} ({result['input_branch']} → {result['matched_branch']})")
    
    st.write(f"**{t['package']}** {result['produkt']}")
    st.write(f"**{t['channels']}** {', '.join(result['kanaler'])}")
    st.write(f"**{t['budget']}** {result['budget']}")
    
    # Visa manual input om score är lågt
    if result['score'] < 0.8:  # Threshold för låg score
        st.warning(t["low_score_warning"].format(score=result['score']))
        
        with st.expander(t["manual_training"]):
            st.info(t["manual_training_info"])
            
            # Manual input fields
            manual_col1, manual_col2 = st.columns(2)
            
            with manual_col1:
                manual_paket = st.selectbox(
                    t["correct_package"],
                    PACKAGES[language],
                    key="manual_paket"
                )
                
                manual_kanaler = st.multiselect(
                    t["correct_channels"],
                    ["Meta", "LinkedIn", "Snapchat", "Reddit", "TikTok"],
                    key="manual_kanaler"
                )
            
            with manual_col2:
                manual_budget = st.selectbox(
                    t["correct_budget"],
                    BUDGETS[language],
                    key="manual_budget"
                )
            
            if st.button(t["save_training"], key="save_training"):
                if manual_kanaler:  # Kontrollera att kanaler är valda
                    success, message = save_new_training_data(
                        job_title, senioritet_sv, stad_storlek_sv, 
                        manual_paket, manual_kanaler, manual_budget, df
                    )
                    
                    if success:
                        st.success(t["data_saved"])
                        st.info(t["click_update"])
                        # Clear cache to force reload
                        st.cache_data.clear()
                        st.cache_resource.clear()
                    else:
                        st.error(message)
                else:
                    st.error(t["select_channels"])
    else:
        st.success(t["good_match"].format(score=result['score']))

# Refresh system button
st.divider()
if st.button(t["update_system"], help=t["update_help"]):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()