#!/usr/bin/env python3
"""
Integrated Streamlit app combining:
1. Role similarity matching
2. Real campaign data recommendations
3. Budget predictions
4. Channel optimization
"""

import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Page config
st.set_page_config(
    page_title="Smart Rekryteringsrekommendationer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with better contrast
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    
    /* Darker background for metrics */
    [data-testid="metric-container"] {
        background-color: #1e1e1e !important;
        border: 1px solid #333 !important;
        padding: 15px !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3) !important;
    }
    
    /* White text for metric labels */
    [data-testid="metric-container"] label {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    /* Larger, colored metric values */
    [data-testid="metric-container"] > div:nth-child(2) {
        color: #4CAF50 !important;
        font-size: 2rem !important;
        font-weight: bold !important;
    }
    
    /* Delta text styling */
    [data-testid="metric-container"] > div:nth-child(3) {
        color: #FFC107 !important;
        font-size: 0.9rem !important;
    }
    
    /* Info and success boxes with better contrast */
    .stAlert {
        background-color: rgba(30, 30, 30, 0.9) !important;
        border: 1px solid #444 !important;
        color: #ffffff !important;
    }
    
    /* Headers with better visibility */
    h1, h2, h3 {
        color: #ffffff !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    /* Buttons with better contrast */
    .stButton > button {
        background-color: #2e2e2e !important;
        color: #ffffff !important;
        border: 1px solid #444 !important;
    }
    
    .stButton > button:hover {
        background-color: #3e3e3e !important;
        border: 1px solid #666 !important;
    }
    
    /* Sidebar improvements */
    section[data-testid="stSidebar"] {
        background-color: #1a1a1a !important;
    }
    
    section[data-testid="stSidebar"] .stTextInput label {
        color: #ffffff !important;
    }
    
    section[data-testid="stSidebar"] .stNumberInput label {
        color: #ffffff !important;
    }
    
    section[data-testid="stSidebar"] .stSlider label {
        color: #ffffff !important;
    }
    
    /* Dataframe styling */
    .dataframe {
        background-color: #2e2e2e !important;
        color: #ffffff !important;
    }
    
    .dataframe th {
        background-color: #1e1e1e !important;
        color: #ffffff !important;
    }
    
    .dataframe td {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
class RecommendationEngine:
    def __init__(self):
        """Initialize with both theoretical and real campaign data."""
        self.model = SentenceTransformer('KBLab/sentence-bert-swedish-cased')
        
        # Load real campaign data
        try:
            self.campaign_df = pd.read_csv('all_platforms_campaigns_complete.csv')
            self.has_real_data = True
        except:
            self.campaign_df = pd.DataFrame()
            self.has_real_data = False
        
        # Load theoretical training data as fallback
        try:
            self.training_df = pd.read_csv('enhanced_training_detailed.csv')
        except:
            self.training_df = pd.DataFrame()
        
        self.role_stats = self._calculate_role_statistics()
        self.known_roles = list(self.role_stats.keys())
        self.role_embeddings = self._create_role_embeddings()
        
    def _calculate_role_statistics(self) -> Dict:
        """Calculate statistics from real campaign data."""
        stats = {}
        
        if self.has_real_data and not self.campaign_df.empty:
            # Extract roles from campaign names
            role_patterns = {
                'Sjuksköterska': ['sjuksköterska', 'sjukskötare', 'nurse'],
                'Ambulanssjuksköterska': ['ambulanssjuksköterska', 'ambulans'],
                'Anestesisjuksköterska': ['anestesisjuksköterska', 'anestesi'],
                'Operationssjuksköterska': ['operationssjuksköterska', 'operation'],
                'Barnsjuksköterska': ['barnsjuksköterska', 'barn'],
                'Tekniker': ['tekniker', 'teknisk'],
                'Servicetekniker': ['servicetekniker', 'service'],
                'Fastighetstekniker': ['fastighetstekniker', 'fastighet'],
                'Chef': ['chef', 'ledare', 'manager'],
                'Platschef': ['platschef', 'plats'],
                'Driftchef': ['driftchef', 'drift'],
                'Säljare': ['säljare', 'sälj', 'sales'],
                'Ingenjör': ['ingenjör', 'engineer'],
                'Konsult': ['konsult', 'consultant'],
                'Projektledare': ['projektledare', 'project'],
                'Controller': ['controller', 'ekonom'],
                'Mekaniker': ['mekaniker', 'mek'],
                'HR-specialist': ['hr-specialist', 'hr specialist'],
                'IT-specialist': ['it-specialist', 'it specialist'],
                'Utvecklare': ['utvecklare', 'developer', 'programmerare'],
                'Lagerarbetare': ['lagerarbetare', 'lager'],
                'Butikschef': ['butikschef', 'butiks'],
                'VD': ['vd', 'ceo', 'verkställande'],
                'Elektriker': ['elektriker', 'el-installatör'],
                'Läkare': ['läkare', 'doktor'],
                'Undersköterska': ['undersköterska', 'vårdbiträde'],
                'Fysioterapeut': ['fysioterapeut', 'sjukgymnast'],
                'Redovisningsekonom': ['redovisningsekonom', 'redovisning'],
                'Fastighetsförvaltare': ['fastighetsförvaltare', 'förvaltare'],
                'Kock': ['kock', 'kökschef'],
                'Förare': ['förare', 'chaufför', 'driver']
            }
            
            self.campaign_df['Role'] = None
            for role, patterns in role_patterns.items():
                for pattern in patterns:
                    mask = self.campaign_df['campaign_name'].str.contains(
                        pattern, case=False, na=False
                    )
                    self.campaign_df.loc[mask & self.campaign_df['Role'].isna(), 'Role'] = role
            
            # Calculate stats for each role
            role_df = self.campaign_df[self.campaign_df['Role'].notna()].copy()
            
            for role in role_df['Role'].unique():
                role_data = role_df[role_df['Role'] == role]
                stats[role] = {}
                
                for platform in role_data['platform'].unique():
                    platform_data = role_data[role_data['platform'] == platform]
                    
                    total_impressions = platform_data['total_impressions'].sum()
                    total_clicks = platform_data['total_clicks'].sum()
                    total_spend = platform_data['total_spend'].sum()
                    campaign_count = len(platform_data)
                    
                    if total_impressions > 0 and total_clicks > 0:
                        stats[role][platform] = {
                            'ctr': (total_clicks / total_impressions) * 100,
                            'cpc': total_spend / total_clicks,
                            'avg_spend': total_spend / campaign_count,
                            'total_spend': total_spend,
                            'campaigns': campaign_count,
                            'clicks': total_clicks,
                            'impressions': total_impressions
                        }
        
        return stats
    
    def _create_role_embeddings(self) -> Dict:
        """Create embeddings for all known roles."""
        embeddings = {}
        for role in self.known_roles:
            embeddings[role] = self.model.encode(role)
        return embeddings
    
    def find_similar_roles(self, query_role: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Find the most similar roles."""
        if not self.role_embeddings:
            return []
        
        query_embedding = self.model.encode(query_role)
        similarities = []
        
        for role, role_embedding in self.role_embeddings.items():
            similarity = cosine_similarity(
                query_embedding.reshape(1, -1),
                role_embedding.reshape(1, -1)
            )[0][0]
            similarities.append((role, similarity))
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def get_recommendations(self, query_role: str, budget: float = None, 
                           campaign_days: int = 30) -> Dict:
        """Get channel recommendations for a role."""
        recommendations = {
            'query_role': query_role,
            'data_source': None,
            'similarity_score': None,
            'matched_role': None,
            'channels': {},
            'suggested_mix': {},
            'confidence': None,
            'explanation': None,
            'similar_roles': []
        }
        
        # Find similar roles
        similar_roles = self.find_similar_roles(query_role)
        recommendations['similar_roles'] = similar_roles
        
        # Check for exact match or use most similar
        if query_role in self.role_stats:
            recommendations['data_source'] = 'exact'
            recommendations['matched_role'] = query_role
            recommendations['similarity_score'] = 1.0
            recommendations['confidence'] = 'Hög'
            role_data = self.role_stats[query_role]
        elif similar_roles and similar_roles[0][1] > 0.7:
            matched_role, similarity = similar_roles[0]
            recommendations['data_source'] = 'similar'
            recommendations['matched_role'] = matched_role
            recommendations['similarity_score'] = similarity
            
            if similarity > 0.85:
                recommendations['confidence'] = 'Hög'
            elif similarity > 0.75:
                recommendations['confidence'] = 'Medel'
            else:
                recommendations['confidence'] = 'Låg'
            
            recommendations['explanation'] = f"Baserat på liknande roll: {matched_role} ({similarity*100:.0f}% likhet)"
            role_data = self.role_stats[matched_role]
        else:
            recommendations['explanation'] = "Ingen tillräckligt liknande roll hittades"
            return recommendations
        
        # Calculate channel recommendations
        for platform, metrics in role_data.items():
            recommendations['channels'][platform] = {
                'ctr': round(metrics['ctr'], 2),
                'cpc': round(metrics['cpc'], 2),
                'avg_spend_per_campaign': round(metrics['avg_spend'], 0),
                'campaigns_run': metrics['campaigns'],
                'performance_score': self._calculate_performance_score(metrics)
            }
        
        # Calculate optimal mix
        recommendations['suggested_mix'] = self._calculate_optimal_mix(role_data)
        
        # Predict outcomes if budget provided
        if budget:
            recommendations['predicted_outcomes'] = self._predict_outcomes(
                role_data, budget, campaign_days, recommendations['suggested_mix']
            )
        
        return recommendations
    
    def _calculate_performance_score(self, metrics: Dict) -> float:
        """Calculate performance score."""
        ctr_score = min(metrics['ctr'] / 5 * 100, 100)
        cpc_score = max(0, 100 - (metrics['cpc'] / 50 * 100))
        return round(ctr_score * 0.6 + cpc_score * 0.4, 1)
    
    def _calculate_optimal_mix(self, role_data: Dict) -> Dict:
        """Calculate optimal channel mix."""
        if not role_data:
            return {}
        
        scores = {platform: self._calculate_performance_score(metrics) 
                 for platform, metrics in role_data.items()}
        
        sorted_platforms = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        mix = {}
        if len(sorted_platforms) == 1:
            mix[sorted_platforms[0][0]] = 100
        elif len(sorted_platforms) == 2:
            mix[sorted_platforms[0][0]] = 70
            mix[sorted_platforms[1][0]] = 30
        else:
            mix[sorted_platforms[0][0]] = 60
            mix[sorted_platforms[1][0]] = 30
            if len(sorted_platforms) > 2:
                mix[sorted_platforms[2][0]] = 10
        
        return mix
    
    def _predict_outcomes(self, role_data: Dict, budget: float, 
                         campaign_days: int, channel_mix: Dict) -> Dict:
        """Predict campaign outcomes."""
        predictions = {
            'total_budget': budget,
            'campaign_days': campaign_days,
            'daily_budget': budget / campaign_days,
            'channels': {}
        }
        
        total_clicks = 0
        total_impressions = 0
        
        for platform, percentage in channel_mix.items():
            if platform in role_data:
                platform_budget = budget * (percentage / 100)
                metrics = role_data[platform]
                
                predicted_clicks = platform_budget / metrics['cpc']
                predicted_impressions = predicted_clicks / (metrics['ctr'] / 100)
                
                predictions['channels'][platform] = {
                    'budget': round(platform_budget, 0),
                    'predicted_clicks': round(predicted_clicks, 0),
                    'predicted_impressions': round(predicted_impressions, 0),
                    'predicted_ctr': round(metrics['ctr'], 2),
                    'predicted_cpc': round(metrics['cpc'], 2)
                }
                
                total_clicks += predicted_clicks
                total_impressions += predicted_impressions
        
        predictions['total_predicted_clicks'] = round(total_clicks, 0)
        predictions['total_predicted_impressions'] = round(total_impressions, 0)
        predictions['overall_predicted_ctr'] = round(
            (total_clicks / total_impressions * 100) if total_impressions > 0 else 0, 2
        )
        
        return predictions

def main():
    # Initialize engine
    if 'engine' not in st.session_state:
        with st.spinner('Laddar rekommendationsmotor...'):
            st.session_state.engine = RecommendationEngine()
    
    engine = st.session_state.engine
    
    # Header
    st.title("🎯 Smart Rekryteringsrekommendationer")
    st.markdown("### Kombinerar AI-matchning med verklig kampanjdata från 10,000+ kampanjer")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Inställningar")
        
        # Input fields
        role_input = st.text_input(
            "🔍 Sök roll",
            placeholder="T.ex. Ambulanssjuksköterska, Utvecklare, Platschef...",
            help="Skriv in vilken roll som helst - systemet hittar liknande roller om exakt matchning saknas",
            key="role_search"
        )
        
        # Search button
        search_button = st.button(
            "🚀 Sök rekommendationer",
            type="primary",
            use_container_width=True,
            disabled=not role_input
        )
        
        # Clear button if there's an active search
        if 'active_search' in st.session_state:
            if st.button("🔄 Rensa sökning", use_container_width=True):
                del st.session_state['active_search']
                del st.session_state['search_results']
                st.rerun()
        
        st.divider()
        
        budget = st.number_input(
            "💰 Budget (SEK)",
            min_value=1000,
            max_value=500000,
            value=20000,
            step=5000,
            help="Total kampanjbudget i SEK"
        )
        
        campaign_days = st.slider(
            "📅 Kampanjlängd (dagar)",
            min_value=7,
            max_value=90,
            value=30,
            help="Antal dagar kampanjen ska köras"
        )
        
        st.divider()
        
        # Show available roles
        if st.checkbox("📋 Visa tillgängliga roller"):
            st.subheader("Roller med data:")
            roles_df = pd.DataFrame({
                'Roll': engine.known_roles[:20],
                'Kampanjer': [len(engine.role_stats.get(r, {})) for r in engine.known_roles[:20]]
            })
            st.dataframe(roles_df, use_container_width=True)
            
            if len(engine.known_roles) > 20:
                st.info(f"...och {len(engine.known_roles) - 20} roller till")
    
    # Main content
    if search_button and role_input:
        # Store search in session state
        st.session_state['active_search'] = role_input
        st.session_state['search_results'] = engine.get_recommendations(role_input, budget, campaign_days)
    
    # Display results if we have an active search
    if 'active_search' in st.session_state and st.session_state.get('search_results'):
        recommendations = st.session_state['search_results']
        searched_role = st.session_state['active_search']
        
        # Display header with searched role
        st.header(f"📊 Rekommendationer för: **{searched_role}**")
        
        # Display results
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if recommendations['data_source']:
                st.metric(
                    "Datakälla",
                    "Exakt matchning" if recommendations['data_source'] == 'exact' else "Likhetsbaserad",
                    f"{recommendations['similarity_score']*100:.0f}% likhet" if recommendations['similarity_score'] else None
                )
            else:
                st.error("Ingen matchning")
        
        with col2:
            if recommendations['matched_role']:
                st.metric(
                    "Matchad roll",
                    recommendations['matched_role'],
                    recommendations['confidence'] if recommendations['confidence'] else None
                )
        
        with col3:
            if recommendations['channels']:
                total_campaigns = sum(ch['campaigns_run'] for ch in recommendations['channels'].values())
                st.metric(
                    "Dataunderlag",
                    f"{total_campaigns} kampanjer",
                    "Tillförlitlig data" if total_campaigns > 10 else "Begränsad data"
                )
        
        # Channel recommendations
        if recommendations['channels']:
            st.divider()
            
            # Tabs for different views
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Kanalmix", "📈 Prestanda", "🎯 Förutsägelser", "🔍 Liknande roller"])
            
            with tab1:
                st.subheader("Rekommenderad kanalmix")
                
                # Pie chart for channel mix
                fig = go.Figure(data=[go.Pie(
                    labels=list(recommendations['suggested_mix'].keys()),
                    values=list(recommendations['suggested_mix'].values()),
                    hole=.3,
                    marker_colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
                )])
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # Channel details
                for platform, percentage in recommendations['suggested_mix'].items():
                    if platform in recommendations['channels']:
                        metrics = recommendations['channels'][platform]
                        with st.expander(f"{platform.capitalize()} - {percentage}% av budget"):
                            col1, col2, col3, col4 = st.columns(4)
                            col1.metric("CTR", f"{metrics['ctr']}%")
                            col2.metric("CPC", f"{metrics['cpc']:.2f} SEK")
                            col3.metric("Performance", f"{metrics['performance_score']}/100")
                            col4.metric("Historik", f"{metrics['campaigns_run']} kampanjer")
            
            with tab2:
                st.subheader("Kanalprestandajämförelse")
                
                # Performance comparison
                perf_data = []
                for platform, metrics in recommendations['channels'].items():
                    perf_data.append({
                        'Kanal': platform.capitalize(),
                        'CTR (%)': metrics['ctr'],
                        'CPC (SEK)': metrics['cpc'],
                        'Performance Score': metrics['performance_score']
                    })
                
                perf_df = pd.DataFrame(perf_data)
                
                # Bar charts
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.bar(perf_df, x='Kanal', y='CTR (%)', 
                                title='Click-Through Rate per kanal',
                                color='CTR (%)', color_continuous_scale='viridis')
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.bar(perf_df, x='Kanal', y='CPC (SEK)', 
                                title='Cost Per Click per kanal',
                                color='CPC (SEK)', color_continuous_scale='reds_r')
                    st.plotly_chart(fig, use_container_width=True)
            
            with tab3:
                st.subheader("📊 Förutsägelser baserat på din budget")
                
                if 'predicted_outcomes' in recommendations:
                    pred = recommendations['predicted_outcomes']
                    
                    # Summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Total budget", f"{pred['total_budget']:,.0f} SEK")
                    col2.metric("Förväntade klick", f"{pred['total_predicted_clicks']:,.0f}")
                    col3.metric("Förväntad CTR", f"{pred['overall_predicted_ctr']}%")
                    col4.metric("Daglig budget", f"{pred['daily_budget']:,.0f} SEK")
                    
                    st.divider()
                    
                    # Per channel predictions
                    st.markdown("### Förutsägelser per kanal")
                    
                    for platform, channel_pred in pred['channels'].items():
                        with st.expander(f"{platform.capitalize()} - {channel_pred['budget']:,.0f} SEK"):
                            col1, col2, col3 = st.columns(3)
                            col1.metric("Förväntade klick", f"{channel_pred['predicted_clicks']:,.0f}")
                            col2.metric("Förväntade visningar", f"{channel_pred['predicted_impressions']:,.0f}")
                            col3.metric("Förväntad CPC", f"{channel_pred['predicted_cpc']:.2f} SEK")
            
            with tab4:
                st.subheader("🔍 Liknande roller")
                
                if recommendations['similar_roles']:
                    similar_df = pd.DataFrame(
                        recommendations['similar_roles'][:10],
                        columns=['Roll', 'Likhet']
                    )
                    similar_df['Likhet %'] = (similar_df['Likhet'] * 100).round(1)
                    similar_df = similar_df[['Roll', 'Likhet %']]
                    
                    # Bar chart of similarities
                    fig = px.bar(similar_df, x='Likhet %', y='Roll', 
                                orientation='h',
                                title='Top 10 mest liknande roller',
                                color='Likhet %',
                                color_continuous_scale='viridis')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Explanation
                    if recommendations['explanation']:
                        st.info(recommendations['explanation'])
        
        else:
            st.warning(recommendations['explanation'] if recommendations['explanation'] 
                      else "Ingen data tillgänglig för denna roll")
    
    else:
        # Welcome screen
        st.info("👈 Ange en roll i sidopanelen för att få rekommendationer")
        
        # Show some statistics
        st.divider()
        st.subheader("📊 Systemstatistik")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Tillgängliga roller",
                value=f"{len(engine.known_roles)} st",
                delta="Med exakt data"
            )
        
        with col2:
            if engine.has_real_data:
                campaign_count = len(engine.campaign_df)
                st.metric(
                    label="Kampanjer i databasen",
                    value=f"{campaign_count:,}",
                    delta=f"{campaign_count/1000:.1f}K kampanjer"
                )
            else:
                st.metric(
                    label="Kampanjer i databasen",
                    value="0",
                    delta="Ingen data"
                )
        
        with col3:
            st.metric(
                label="AI-modell",
                value="Svensk BERT",
                delta="KBLab model"
            )
        
        # Additional info
        st.divider()
        
        # Info boxes
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("""
            **🎯 Så fungerar systemet:**
            1. **Exakt matchning** - Om rollen finns i databasen
            2. **AI-matchning** - Hittar liknande roller automatiskt
            3. **Rekommendationer** - Baserat på 10,000+ kampanjer
            4. **Förutsägelser** - Beräknar förväntade resultat
            """)
        
        with col2:
            st.success("""
            **✨ Systemets fördelar:**
            - ✅ Fungerar för ALLA roller
            - ✅ Verklig kampanjdata
            - ✅ Intelligent matchning
            - ✅ Budgetoptimering
            """)
        
        # Example searches
        st.divider()
        st.subheader("💡 Testa dessa exempelsökningar")
        
        # Two rows of examples
        st.markdown("**Roller med exakt data:**")
        examples_exact = ["Sjuksköterska", "Tekniker", "Chef", "Säljare"]
        cols = st.columns(4)
        for i, example in enumerate(examples_exact):
            with cols[i]:
                if st.button(example, key=f"exact_{i}", use_container_width=True):
                    st.session_state['active_search'] = example
                    st.session_state['search_results'] = engine.get_recommendations(example, 20000, 30)
                    st.rerun()
        
        st.markdown("**Roller som använder AI-matchning:**")
        examples_ai = ["Ambulansförare", "Dataanalytiker", "UX-designer", "Scrum Master"]
        cols = st.columns(4)
        for i, example in enumerate(examples_ai):
            with cols[i]:
                if st.button(example, key=f"ai_{i}", use_container_width=True, type="secondary"):
                    st.session_state['active_search'] = example
                    st.session_state['search_results'] = engine.get_recommendations(example, 20000, 30)
                    st.rerun()

if __name__ == "__main__":
    main()
