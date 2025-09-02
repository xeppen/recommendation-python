#!/usr/bin/env python3
"""
Industry-aware Streamlit app with enhanced recommendations.
Uses recommendation_engine_v3 for role + industry specific predictions.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Import the industry-aware recommendation engine and budget recommender
from recommendation_engine_v3 import IndustryAwareRecommendationEngine
from budget_recommender import BudgetRecommender

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
        background-color: rgba(30, 30, 30, 0.95) !important;
        border: 1px solid #555 !important;
        color: #ffffff !important;
        padding: 1rem !important;
    }
    
    /* Make info boxes more readable */
    [data-testid="stInfo"] {
        background-color: rgba(40, 60, 80, 0.95) !important;
        border-left: 4px solid #2196F3 !important;
    }
    
    [data-testid="stSuccess"] {
        background-color: rgba(40, 80, 40, 0.95) !important;
        border-left: 4px solid #4CAF50 !important;
    }
    
    [data-testid="stWarning"] {
        background-color: rgba(80, 60, 40, 0.95) !important;
        border-left: 4px solid #FF9800 !important;
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
    section[data-testid="stSidebar"] .stSelectbox label {
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

def display_recommendations(engine, budget_recommender, role: str, industry: Optional[str], 
                          campaign_days: int, selected_tier: str):
    """Display recommendations for a role + industry combination."""
    
    # Get budget recommendation first
    budget_rec = budget_recommender.get_budget_recommendation(role, industry, campaign_days)
    
    # Get the recommended budget based on selected tier
    if budget_rec['budget_tiers'] and selected_tier in budget_rec['budget_tiers']:
        budget = budget_rec['budget_tiers'][selected_tier]['total']
    else:
        budget = 2000  # Fallback budget
    
    # Get channel recommendations
    recommendations = engine.get_recommendations(
        role=role,
        industry=industry,
        budget=budget,
        campaign_days=campaign_days
    )
    
    if not recommendations['channels']:
        st.warning("⚠️ Ingen data hittades för denna roll och bransch")
        
        # Show similar combinations
        if recommendations['similar_combinations']:
            st.subheader("🔍 Liknande roller och branscher:")
            similar_df = pd.DataFrame(
                recommendations['similar_combinations'][:5],
                columns=['Roll-Bransch', 'Likhet']
            )
            similar_df['Likhet'] = (similar_df['Likhet'] * 100).round(1).astype(str) + '%'
            st.dataframe(similar_df, use_container_width=True)
        return
    
    # Data source info with industry context
    col1, col2 = st.columns([1, 2])
    with col1:
        if recommendations['data_source'] == 'exact':
            st.success(f"✅ Exakt matchning!")
        elif recommendations['data_source'] == 'similar':
            st.info(f"🔍 Liknande matchning")
        else:
            st.warning(f"⚠️ Baserat på roll")
        
        # Confidence indicator
        confidence_color = {
            'Hög': '🟢',
            'Medel': '🟡', 
            'Låg': '🔴'
        }.get(recommendations.get('confidence', 'Okänd'), '⚪')
        st.metric("Konfidens", f"{confidence_color} {recommendations.get('confidence', 'Okänd')}")
    
    with col2:
        # Show matched combination with better formatting
        matched = recommendations['matched_combination']
        if ' - ' in matched:
            role_part, industry_part = matched.split(' - ', 1)
            st.info(f"**Matchad roll:** {role_part}\n\n**Bransch:** {industry_part}")
        else:
            st.info(f"**Matchad:** {matched}")
    
    if recommendations.get('explanation'):
        st.caption(recommendations['explanation'])
    
    # Add spacing
    st.markdown("---")
    
    # Display budget recommendations
    st.subheader("💰 Budgetrekommendation")
    
    # Show all budget tiers
    col1, col2, col3 = st.columns(3)
    
    tiers_display = {
        'minimum': ('🥉 Grundläggande', col1),
        'standard': ('🥈 Rekommenderad', col2),
        'premium': ('🥇 Premium', col3)
    }
    
    for tier_key, (tier_label, col) in tiers_display.items():
        with col:
            if tier_key in budget_rec['budget_tiers']:
                tier_data = budget_rec['budget_tiers'][tier_key]
                is_selected = tier_key == selected_tier
                
                # Highlight selected tier
                if is_selected:
                    st.success(f"**{tier_label}** ✓")
            else:
                    st.info(tier_label)
                
                st.metric(
                    "Total budget",
                    f"{tier_data['total']:,.0f} SEK",
                    f"{tier_data['daily']:.0f} SEK/dag"
                )
                
                if 'expected_clicks' in tier_data and tier_data['expected_clicks'] > 0:
                    st.caption(f"~{tier_data['expected_clicks']:,} klick")
                
                if 'confidence' in tier_data:
                    st.caption(f"Framgång: {tier_data['confidence']}")
    
    # Show data confidence
    if budget_rec['data_points'] > 0:
        confidence_emoji = '🟢' if budget_rec['confidence'] == 'Hög' else '🟡' if budget_rec['confidence'] == 'Medel' else '🔴'
        avg_ctr = budget_rec['historical_data'].get('avg_ctr', 0)
        avg_cpc = budget_rec['historical_data'].get('avg_cpc', 0)
        st.info(f"""
        **Dataunderlag:** {budget_rec['data_points']} liknande kampanjer  
        **Konfidens:** {confidence_emoji} {budget_rec['confidence']}  
        **Historisk CTR:** {avg_ctr:.2f}%  
        **Historisk CPC:** {avg_cpc:.2f} SEK
        """)
    
    st.markdown("---")
    
    # Channel performance metrics
    st.subheader("📊 Kanalrekommendationer")
    
    channels_data = []
    for platform, metrics in recommendations['channels'].items():
        channels_data.append({
            'Kanal': platform.title(),
            'CTR': metrics['ctr'],
            'CPC': metrics['cpc'],
            'Performance': metrics['performance_score'],
            'Kampanjer': metrics['campaigns_run']
        })
    
    if channels_data:
        channels_df = pd.DataFrame(channels_data).sort_values('Performance', ascending=False)
        
        # Display channels in a more readable format
        for idx, row in channels_df.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
                
                with col1:
                    st.markdown(f"### {row['Kanal']}")
                    st.caption(f"Baserat på {row['Kampanjer']} kampanjer")
                
                with col2:
                    st.metric("CTR", f"{row['CTR']:.2f}%")
                
                with col3:
                    st.metric("CPC", f"{row['CPC']:.2f} SEK")
                
                with col4:
                    # Performance indicator with color
                    perf_color = '#4CAF50' if row['Performance'] > 70 else '#FFC107' if row['Performance'] > 40 else '#f44336'
                    st.markdown(f"""
                    <div style='margin-top: 20px;'>
                        <p style='color: #888; font-size: 0.9em; margin-bottom: 5px;'>Performance Score</p>
                        <div style='background: #333; height: 20px; border-radius: 10px; position: relative;'>
                            <div style='background: {perf_color}; width: {row['Performance']}%; height: 100%; 
                                        border-radius: 10px; position: absolute;'></div>
                            <span style='position: absolute; left: 50%; transform: translateX(-50%); 
                                       color: white; font-weight: bold; line-height: 20px;'>
                                {row['Performance']:.0f}/100
                            </span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
    
    # Suggested channel mix
    if recommendations['suggested_mix']:
        st.subheader("🎯 Rekommenderad kanalmix")
        
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=[p.title() for p in recommendations['suggested_mix'].keys()],
            values=list(recommendations['suggested_mix'].values()),
            hole=.3,
            marker=dict(colors=['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336'])
        )])
        fig.update_layout(
            showlegend=True,
            height=300,
            margin=dict(t=0, b=0, l=0, r=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Predicted outcomes
    if 'predicted_outcomes' in recommendations:
        st.subheader("📈 Förväntade resultat")
        
        outcomes = recommendations['predicted_outcomes']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Total budget",
                f"{outcomes['total_budget']:,.0f} SEK",
                f"{outcomes['daily_budget']:.0f} SEK/dag"
            )
        with col2:
            st.metric(
                "Förväntade klick",
                f"{outcomes['total_predicted_clicks']:,.0f}",
                f"Över {outcomes['campaign_days']} dagar"
            )
        with col3:
            st.metric(
                "Förväntade visningar",
                f"{outcomes['total_predicted_impressions']/1000:.1f}K",
                f"CTR: {outcomes['overall_predicted_ctr']:.2f}%"
            )
        with col4:
            avg_cpc = outcomes['total_budget'] / outcomes['total_predicted_clicks'] if outcomes['total_predicted_clicks'] > 0 else 0
            st.metric(
                "Genomsnittlig CPC",
                f"{avg_cpc:.2f} SEK",
                "Över alla kanaler"
            )
        
        # Channel breakdown
        if outcomes['channels']:
            st.subheader("📊 Fördelning per kanal")
            
            breakdown_data = []
            for platform, pred in outcomes['channels'].items():
                breakdown_data.append({
                    'Kanal': platform.title(),
                    'Budget (SEK)': pred['budget'],
                    'Klick': pred['predicted_clicks'],
                    'Visningar': pred['predicted_impressions'],
                    'CTR (%)': pred['predicted_ctr'],
                    'CPC (SEK)': pred['predicted_cpc']
                })
            
            breakdown_df = pd.DataFrame(breakdown_data)
            
            # Create bar chart
            fig = px.bar(
                breakdown_df,
                x='Kanal',
                y='Budget (SEK)',
                color='CTR (%)',
                color_continuous_scale='RdYlGn',
                text='Budget (SEK)',
                hover_data={
                    'Klick': ':,.0f',
                    'Visningar': ':,.0f',
                    'CPC (SEK)': ':.2f'
                }
            )
            fig.update_traces(texttemplate='%{text:,.0f} SEK', textposition='outside')
            fig.update_layout(
                showlegend=False,
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                xaxis=dict(gridcolor='#333'),
                yaxis=dict(gridcolor='#333')
            )
            st.plotly_chart(fig, use_container_width=True)

def main():
    st.title("🎯 Smart Rekryteringsrekommendationer med Branschinsikter")
    st.markdown("### Få AI-drivna rekommendationer baserade på 10,000+ kampanjer")
    
    # Load recommendation engine and budget recommender
    if 'engine' not in st.session_state:
        with st.spinner('Laddar branschmedveten rekommendationsmotor...'):
            st.session_state.engine = IndustryAwareRecommendationEngine()
            st.session_state.budget_recommender = BudgetRecommender()
    
    engine = st.session_state.engine
    budget_recommender = st.session_state.budget_recommender
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Inställningar")
        
        # Role and industry input with search button
        st.subheader("🔍 Sök roll och bransch")
        
        role_input = st.text_input(
            "Vilken roll vill du rekrytera för?",
            placeholder="T.ex. Sjuksköterska, Utvecklare, Butikschef...",
            key="role_input"
        )
        
        # Get available industries from engine
        industries = ['Automatisk'] + engine.get_available_industries()
        selected_industry = st.selectbox(
            "Välj bransch",
            industries,
            help="Välj 'Automatisk' för att låta systemet gissa bransch"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            search_clicked = st.button("🔍 Sök", type="primary", use_container_width=True)
        
        with col2:
            if st.button("🔄 Rensa", use_container_width=True):
                st.session_state.searched_role = None
                st.session_state.searched_industry = None
                st.session_state.role_input = ""
                st.rerun()
        
        # Handle search
        if search_clicked and role_input:
            st.session_state.searched_role = role_input
            st.session_state.searched_industry = None if selected_industry == 'Automatisk' else selected_industry
        
        # Example buttons with industries
        st.markdown("---")
        st.subheader("📌 Snabbval")
        examples = [
            ("Sjuksköterska", "👩‍⚕️", "Sjukvård"),
            ("Butikschef", "🏪", "Dagligvaror"),
            ("Utvecklare", "💻", "IT & Tech"),
            ("Säljare", "💼", "Bygg & Hem"),
            ("Tekniker", "🔧", "Fordonsindustri"),
            ("Chef", "👔", "Bank & Finans")
        ]
        
        for example_role, emoji, example_industry in examples:
            if st.button(f"{emoji} {example_role} - {example_industry}", use_container_width=True):
                st.session_state.searched_role = example_role
                st.session_state.searched_industry = example_industry
                st.rerun()
        
        # Campaign settings
        st.markdown("---")
        st.subheader("📅 Kampanjinställningar")
        
        campaign_days = st.slider(
            "Kampanjlängd (dagar)",
            min_value=7,
            max_value=90,
            value=30,
            help="Antal dagar kampanjen ska pågå"
        )
        
        # Budget tier selection
        st.markdown("---")
        st.subheader("💰 Budgetnivå")
        
        budget_tier = st.radio(
            "Välj ambitionsnivå:",
            ["🥉 Grundläggande", "🥈 Rekommenderad", "🥇 Premium"],
            index=1,
            help="Välj baserat på hur viktigt det är att fylla tjänsten snabbt"
        )
        
        # Map selection to tier
        tier_mapping = {
            "🥉 Grundläggande": "minimum",
            "🥈 Rekommenderad": "standard",
            "🥇 Premium": "premium"
        }
        selected_tier = tier_mapping[budget_tier]
        
        # Info about the system
        st.markdown("---")
        st.subheader("📊 Om systemet")
        
        # Get industry summary
        industry_summary = engine.get_industry_summary()
        
        st.metric("Totalt antal branscher", len(industry_summary))
        st.metric("Roll-bransch kombinationer", len(engine.known_combinations))
        st.metric("Kampanjer analyserade", f"{len(engine.campaign_df):,}")
        
        # Top industries
        st.markdown("**Top branscher:**")
        top_industries = sorted(
            industry_summary.items(),
            key=lambda x: x[1]['total_campaigns'],
            reverse=True
        )[:5]
        
        for industry, stats in top_industries:
            st.caption(f"• {industry}: {stats['num_roles']} roller")
    
    # Main content
    # Display header with role and industry
    if 'searched_role' in st.session_state and st.session_state.searched_role:
        st.header(f"🎯 Rekommendationer")
        
        # Display role and industry in a clear format
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Roll:** {st.session_state.searched_role}")
        with col2:
            industry = st.session_state.get('searched_industry', 'Automatisk')
            st.info(f"**Bransch:** {industry if industry != 'Automatisk' else 'Automatiskt vald'}")
        
        display_recommendations(
            engine,
            budget_recommender,
            st.session_state.searched_role,
            st.session_state.get('searched_industry'),
            campaign_days,
            selected_tier
        )
    else:
        # Welcome message
        st.info("""
        👋 **Välkommen till den branschmedvetna rekommendationsmotorn!**
        
        Systemet analyserar över 10,000 kampanjer och ger specifika rekommendationer baserat på:
        - **Roll**: Den specifika tjänsten du vill rekrytera för
        - **Bransch**: Industrin eller sektorn där tjänsten finns
        - **Budget**: Din tillgängliga kampanjbudget
        - **Kampanjlängd**: Hur länge kampanjen ska pågå
        
        **Nyhet!** 🎉 Nu med branschspecifika insikter - samma roll kan prestera helt olika i olika branscher!
        
        Använd sökfältet i sidofältet eller välj ett snabbval för att börja.
        """)
        
        # Show some interesting insights
        st.subheader("💡 Visste du att...")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Butikschef - Dagligvaror",
                "4.46% CTR",
                "0.83 SEK CPC",
                help="Bäst prestanda inom detaljhandel"
            )
        with col2:
                st.metric(
                "Säljare - IT & Tech",
                "2.82% CTR",
                "1.71 SEK CPC",
                help="Högre CPC men mer nischad målgrupp"
            )
        with col3:
            st.metric(
                "Sjuksköterska - Sjukvård",
                "3.11% CTR",
                "1.23 SEK CPC",
                help="Stabil prestanda över alla plattformar"
            )
        
        # Industry comparison chart
        st.subheader("📊 Branschjämförelse - CTR per bransch")
        
        # Sample data for visualization
        sample_data = pd.DataFrame({
            'Bransch': ['Dagligvaror', 'IT & Tech', 'Sjukvård', 'Bygg & Hem', 'Mode & Kläder'],
            'Genomsnittlig CTR (%)': [4.46, 2.82, 3.11, 4.19, 3.84],
            'Genomsnittlig CPC (SEK)': [0.83, 1.71, 1.23, 0.95, 0.93]
        })
        
        fig = px.scatter(
            sample_data,
            x='Genomsnittlig CPC (SEK)',
            y='Genomsnittlig CTR (%)',
            size='Genomsnittlig CTR (%)',
            color='Bransch',
            hover_data=['Bransch'],
            title="CTR vs CPC per bransch"
        )
        fig.update_layout(
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(gridcolor='#333'),
            yaxis=dict(gridcolor='#333')
        )
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
