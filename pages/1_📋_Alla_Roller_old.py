#!/usr/bin/env python3
"""
Page showing all available roles in the system with their statistics.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add parent directory to path to import recommendation_engine
sys.path.append(str(Path(__file__).parent.parent))
from recommendation_engine import RecommendationEngine

# Page config
st.set_page_config(
    page_title="Alla Roller - Smart Rekrytering",
    page_icon="📋",
    layout="wide"
)

# Apply dark theme CSS
st.markdown("""
<style>
    /* Darker background for metrics */
    [data-testid="metric-container"] {
        background-color: #1e1e1e !important;
        border: 1px solid #333 !important;
        padding: 15px !important;
        border-radius: 10px !important;
    }
    
    [data-testid="metric-container"] label {
        color: #ffffff !important;
    }
    
    [data-testid="metric-container"] > div:nth-child(2) {
        color: #4CAF50 !important;
        font-size: 1.5rem !important;
        font-weight: bold !important;
    }
    
    /* Better table styling */
    .dataframe {
        font-size: 14px !important;
    }
    
    .stDataFrame {
        background-color: #1e1e1e !important;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_engine():
    """Load the recommendation engine."""
    return RecommendationEngine()

def main():
    st.title("📋 Alla Tillgängliga Roller")
    st.markdown("### Översikt över alla roller med kampanjdata i systemet")
    
    # Load engine
    engine = load_engine()
    
    # Create statistics for all roles
    role_data = []
    
    for role in engine.known_roles:
        if role in engine.role_stats:
            stats = engine.role_stats[role]
            
            # Calculate totals across all platforms
            total_campaigns = sum(platform_stats['campaigns'] for platform_stats in stats.values())
            total_spend = sum(platform_stats['total_spend'] for platform_stats in stats.values())
            total_clicks = sum(platform_stats['clicks'] for platform_stats in stats.values())
            total_impressions = sum(platform_stats['impressions'] for platform_stats in stats.values())
            
            # Calculate averages
            avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
            avg_cpc = (total_spend / total_clicks) if total_clicks > 0 else 0
            
            # Get platforms used
            platforms = list(stats.keys())
            platform_str = ", ".join([p.capitalize() for p in platforms])
            
            # Find best performing platform
            best_platform = None
            best_ctr = 0
            for platform, platform_stats in stats.items():
                if platform_stats['ctr'] > best_ctr:
                    best_ctr = platform_stats['ctr']
                    best_platform = platform
            
            role_data.append({
                'Roll': role,
                'Kampanjer': total_campaigns,
                'Total Spend (SEK)': round(total_spend, 0),
                'Totala Klick': total_clicks,
                'Genomsnittlig CTR (%)': round(avg_ctr, 2),
                'Genomsnittlig CPC (SEK)': round(avg_cpc, 2),
                'Plattformar': platform_str,
                'Bästa Plattform': best_platform.capitalize() if best_platform else 'N/A',
                'Antal Plattformar': len(platforms)
            })
    
    # Create DataFrame
    df = pd.DataFrame(role_data)
    df = df.sort_values('Kampanjer', ascending=False)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Totalt antal roller",
            f"{len(df)} st",
            "Med kampanjdata"
        )
    
    with col2:
        st.metric(
            "Totalt antal kampanjer",
            f"{df['Kampanjer'].sum():,}",
            f"Snitt: {df['Kampanjer'].mean():.0f} per roll"
        )
    
    with col3:
        st.metric(
            "Total spend",
            f"{df['Total Spend (SEK)'].sum()/1_000_000:.1f}M SEK",
            f"Snitt: {df['Total Spend (SEK)'].mean()/1000:.0f}K per roll"
        )
    
    with col4:
        st.metric(
            "Genomsnittlig CTR",
            f"{df['Genomsnittlig CTR (%)'].mean():.2f}%",
            f"Min: {df['Genomsnittlig CTR (%)'].min():.2f}% Max: {df['Genomsnittlig CTR (%)'].max():.2f}%"
        )
    
    st.divider()
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Tabell", "📈 Kampanjfördelning", "💰 Spend-analys", "🎯 Prestanda"])
    
    with tab1:
        st.subheader("Komplett rollöversikt")
        
        # Search filter
        search = st.text_input("🔍 Filtrera roller", placeholder="Skriv för att filtrera...")
        
        if search:
            filtered_df = df[df['Roll'].str.contains(search, case=False, na=False)]
        else:
            filtered_df = df
        
        # Display options
        col1, col2 = st.columns([1, 3])
        with col1:
            show_all = st.checkbox("Visa alla kolumner", value=False)
        
        if show_all:
            st.dataframe(
                filtered_df,
                use_container_width=True,
                height=600,
                column_config={
                    "Total Spend (SEK)": st.column_config.NumberColumn(
                        "Total Spend (SEK)",
                        format="%.0f kr"
                    ),
                    "Genomsnittlig CPC (SEK)": st.column_config.NumberColumn(
                        "Genomsnittlig CPC (SEK)",
                        format="%.2f kr"
                    ),
                    "Genomsnittlig CTR (%)": st.column_config.NumberColumn(
                        "Genomsnittlig CTR (%)",
                        format="%.2f%%"
                    )
                }
            )
        else:
            # Simplified view
            simple_df = filtered_df[['Roll', 'Kampanjer', 'Genomsnittlig CTR (%)', 
                                    'Genomsnittlig CPC (SEK)', 'Bästa Plattform']]
            st.dataframe(
                simple_df,
                use_container_width=True,
                height=600,
                column_config={
                    "Genomsnittlig CPC (SEK)": st.column_config.NumberColumn(
                        "Genomsnittlig CPC (SEK)",
                        format="%.2f kr"
                    ),
                    "Genomsnittlig CTR (%)": st.column_config.NumberColumn(
                        "Genomsnittlig CTR (%)",
                        format="%.2f%%"
                    )
                }
            )
        
        # Download button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Ladda ner som CSV",
            data=csv,
            file_name='alla_roller_statistik.csv',
            mime='text/csv',
        )
    
    with tab2:
        st.subheader("Kampanjfördelning per roll")
        
        # Top 20 roles by campaign count
        top_roles = df.nlargest(20, 'Kampanjer')
        
        fig = px.bar(
            top_roles,
            x='Kampanjer',
            y='Roll',
            orientation='h',
            title='Top 20 roller med flest kampanjer',
            color='Kampanjer',
            color_continuous_scale='viridis',
            text='Kampanjer'
        )
        fig.update_traces(texttemplate='%{text}', textposition='outside')
        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Platform distribution
        st.subheader("Plattformsfördelning")
        platform_counts = df['Antal Plattformar'].value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_pie = go.Figure(data=[go.Pie(
                labels=[f"{i} plattform(ar)" for i in platform_counts.index],
                values=platform_counts.values,
                hole=.3
            )])
            fig_pie.update_layout(title="Roller per antal plattformar", height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Best platform distribution
            best_platform_counts = df['Bästa Plattform'].value_counts()
            fig_bar = px.bar(
                x=best_platform_counts.index,
                y=best_platform_counts.values,
                title="Bästa plattform per roll",
                labels={'x': 'Plattform', 'y': 'Antal roller'},
                color=best_platform_counts.values,
                color_continuous_scale='teal'
            )
            fig_bar.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
    
    with tab3:
        st.subheader("Spend-analys")
        
        # Top spenders - using bar chart instead of treemap
        top_spend = df.nlargest(15, 'Total Spend (SEK)')
        
        fig = px.bar(
            top_spend,
            x='Total Spend (SEK)',
            y='Roll',
            orientation='h',
            title='Top 15 roller efter total spend',
            color='Genomsnittlig CTR (%)',
            color_continuous_scale='RdYlGn',
            text='Total Spend (SEK)',
            hover_data={'Total Spend (SEK)': ':,.0f',
                       'Kampanjer': True,
                       'Genomsnittlig CTR (%)': ':.2f'}
        )
        fig.update_traces(texttemplate='%{text:,.0f} kr', textposition='outside')
        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Spend vs Performance scatter
        st.subheader("Spend vs Prestanda")
        
        fig_scatter = px.scatter(
            df,
            x='Total Spend (SEK)',
            y='Genomsnittlig CTR (%)',
            size='Kampanjer',
            color='Genomsnittlig CPC (SEK)',
            hover_name='Roll',
            title='Förhållande mellan spend, CTR och CPC',
            labels={'Total Spend (SEK)': 'Total Spend (SEK)',
                   'Genomsnittlig CTR (%)': 'Genomsnittlig CTR (%)'},
            color_continuous_scale='viridis_r'
        )
        fig_scatter.update_layout(height=500)
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    with tab4:
        st.subheader("Prestandaanalys")
        
        # Performance metrics
        col1, col2 = st.columns(2)
        
        with col1:
            # Best CTR
            best_ctr = df.nlargest(10, 'Genomsnittlig CTR (%)')
            fig_ctr = px.bar(
                best_ctr,
                x='Genomsnittlig CTR (%)',
                y='Roll',
                orientation='h',
                title='Top 10 roller - Bäst CTR',
                color='Genomsnittlig CTR (%)',
                color_continuous_scale='greens',
                text='Genomsnittlig CTR (%)'
            )
            fig_ctr.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
            fig_ctr.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_ctr, use_container_width=True)
        
        with col2:
            # Best CPC
            best_cpc = df.nsmallest(10, 'Genomsnittlig CPC (SEK)')
            fig_cpc = px.bar(
                best_cpc,
                x='Genomsnittlig CPC (SEK)',
                y='Roll',
                orientation='h',
                title='Top 10 roller - Lägst CPC',
                color='Genomsnittlig CPC (SEK)',
                color_continuous_scale='blues_r',
                text='Genomsnittlig CPC (SEK)'
            )
            fig_cpc.update_traces(texttemplate='%{text:.2f} kr', textposition='outside')
            fig_cpc.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_cpc, use_container_width=True)
        
        # Efficiency score
        st.subheader("Effektivitetspoäng")
        st.info("Effektivitetspoäng = (CTR / Genomsnittlig CTR) * (Genomsnittlig CPC / CPC)")
        
        # Calculate efficiency score
        avg_ctr_all = df['Genomsnittlig CTR (%)'].mean()
        avg_cpc_all = df['Genomsnittlig CPC (SEK)'].mean()
        
        df['Effektivitet'] = (df['Genomsnittlig CTR (%)'] / avg_ctr_all) * (avg_cpc_all / df['Genomsnittlig CPC (SEK)'])
        
        top_efficient = df.nlargest(15, 'Effektivitet')
        
        fig_eff = px.bar(
            top_efficient,
            x='Effektivitet',
            y='Roll',
            orientation='h',
            title='Top 15 mest effektiva roller',
            color='Effektivitet',
            color_continuous_scale='viridis',
            hover_data={'Genomsnittlig CTR (%)': ':.2f',
                       'Genomsnittlig CPC (SEK)': ':.2f',
                       'Kampanjer': True}
        )
        fig_eff.update_layout(height=600)
        st.plotly_chart(fig_eff, use_container_width=True)

if __name__ == "__main__":
    main()
