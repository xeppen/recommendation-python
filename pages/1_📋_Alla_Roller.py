#!/usr/bin/env python3
"""
Streamlit page showing all roles with industry breakdown.
Enhanced with branch/industry categorization.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')

# Page config
st.set_page_config(
    page_title="Alla Roller & Branscher",
    page_icon="📋",
    layout="wide"
)

# Custom CSS for dark theme
st.markdown("""
<style>
    /* Dark theme styling */
    .main {
        padding: 0rem 1rem;
    }
    
    [data-testid="metric-container"] {
        background-color: #1e1e1e !important;
        border: 1px solid #333 !important;
        padding: 15px !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3) !important;
    }
    
    [data-testid="metric-container"] label {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    [data-testid="metric-container"] > div:nth-child(2) {
        color: #4CAF50 !important;
        font-size: 2rem !important;
        font-weight: bold !important;
    }
    
    h1, h2, h3 {
        color: #ffffff !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    .stDataFrame {
        background-color: #1e1e1e !important;
    }
    
    .dataframe {
        background-color: #2e2e2e !important;
        color: #ffffff !important;
    }
    
    .dataframe th {
        background-color: #1e1e1e !important;
        color: #ffffff !important;
        font-weight: bold !important;
    }
    
    .dataframe td {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

def extract_role_and_industry(row):
    """Extract role and industry from campaign data."""
    campaign_name = str(row.get('campaign_name', '')).lower()
    company = str(row.get('company', '')).lower()
    
    # Role extraction (simplified)
    role = 'Övrig roll'
    if 'sjuksköterska' in campaign_name:
        role = 'Sjuksköterska'
    elif 'butikschef' in campaign_name:
        role = 'Butikschef'
    elif 'säljare' in campaign_name or 'sälj' in campaign_name:
        role = 'Säljare'
    elif 'tekniker' in campaign_name:
        role = 'Tekniker'
    elif 'chef' in campaign_name:
        role = 'Chef'
    elif 'utvecklare' in campaign_name:
        role = 'Utvecklare'
    elif 'ingenjör' in campaign_name:
        role = 'Ingenjör'
    elif 'projektledare' in campaign_name:
        role = 'Projektledare'
    
    # Industry extraction (simplified)
    industry = 'Övrig bransch'
    combined = f"{company} {campaign_name}"
    
    if any(x in combined for x in ['ica', 'coop', 'willys', 'lidl', 'hemköp']):
        industry = 'Dagligvaror'
    elif any(x in combined for x in ['lindex', 'kappahl', 'h&m', 'dressman']):
        industry = 'Mode & Kläder'
    elif any(x in combined for x in ['rusta', 'jula', 'byggmax', 'bauhaus']):
        industry = 'Bygg & Hem'
    elif any(x in combined for x in ['sjukhus', 'vårdcentral', 'karolinska', 'sahlgrenska']):
        industry = 'Sjukvård'
    elif any(x in combined for x in ['microsoft', 'google', 'spotify', 'klarna', 'it-', 'tech']):
        industry = 'IT & Tech'
    elif any(x in combined for x in ['volvo', 'scania', 'ford', 'volkswagen']):
        industry = 'Fordonsindustri'
    elif any(x in combined for x in ['bank', 'seb', 'swedbank', 'handelsbanken']):
        industry = 'Bank & Finans'
    elif any(x in combined for x in ['kommun', 'region', 'myndighet']):
        industry = 'Offentlig sektor'
    elif 'we select' in company:
        industry = 'Diverse branscher'
    
    return pd.Series({'Roll': role, 'Bransch': industry})

def load_and_process_data():
    """Load and process campaign data with role and industry."""
    try:
        # Load the complete campaign data
        df = pd.read_csv('all_platforms_campaigns_complete.csv')
        
        # Extract role and industry
        role_industry = df.apply(extract_role_and_industry, axis=1)
        df['Roll'] = role_industry['Roll']
        df['Bransch'] = role_industry['Bransch']
        
        # Create combination
        df['Roll_Bransch'] = df['Roll'] + ' - ' + df['Bransch']
        
        # Calculate CTR and CPC
        df['CTR'] = (df['total_clicks'] / df['total_impressions'] * 100).fillna(0)
        df['CPC'] = (df['total_spend'] / df['total_clicks']).fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Kunde inte ladda data: {e}")
        return pd.DataFrame()

def main():
    st.title("📋 Alla Roller & Branscher i Systemet")
    st.markdown("### Översikt av alla roll-bransch kombinationer med prestanda")
    
    # Load data
    with st.spinner('Laddar kampanjdata...'):
        df = load_and_process_data()
    
    if df.empty:
        st.error("Ingen data tillgänglig")
        return
    
    # Filter out invalid combinations
    df = df[(df['Roll'] != 'Övrig roll') & (df['Bransch'] != 'Övrig bransch')]
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        unique_roles = df['Roll'].nunique()
        st.metric("Unika roller", unique_roles)
    
    with col2:
        unique_industries = df['Bransch'].nunique()
        st.metric("Unika branscher", unique_industries)
    
    with col3:
        unique_combos = df['Roll_Bransch'].nunique()
        st.metric("Roll-bransch kombinationer", unique_combos)
    
    with col4:
        total_campaigns = len(df)
        st.metric("Totalt antal kampanjer", f"{total_campaigns:,}")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["🏢 Branschöversikt", "👥 Rollöversikt", "🎯 Kombinationer", "📊 Jämförelser"])
    
    with tab1:
        st.subheader("🏢 Branscher i systemet")
        
        # Industry summary
        industry_stats = df.groupby('Bransch').agg({
            'campaign_id': 'count',
            'Roll': 'nunique',
            'total_spend': 'sum',
            'CTR': 'mean',
            'CPC': 'mean'
        }).round(2)
        industry_stats.columns = ['Kampanjer', 'Unika roller', 'Total spend (SEK)', 'Genomsnittlig CTR (%)', 'Genomsnittlig CPC (SEK)']
        industry_stats = industry_stats.sort_values('Kampanjer', ascending=False)
        
        # Display top industries
        st.dataframe(
            industry_stats.head(15).style.format({
                'Total spend (SEK)': '{:,.0f}',
                'Genomsnittlig CTR (%)': '{:.2f}',
                'Genomsnittlig CPC (SEK)': '{:.2f}'
            }),
            use_container_width=True
        )
        
        # Visualization
        col1, col2 = st.columns(2)
        
        with col1:
            # Industry distribution pie chart
            fig = px.pie(
                values=industry_stats['Kampanjer'].head(10),
                names=industry_stats.head(10).index,
                title="Top 10 branscher efter antal kampanjer"
            )
            fig.update_layout(
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white')
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # CTR by industry
            top_industries = industry_stats.nlargest(10, 'Kampanjer')
            fig = px.bar(
                x=top_industries['Genomsnittlig CTR (%)'],
                y=top_industries.index,
                orientation='h',
                title='CTR per bransch (Top 10)',
                color=top_industries['Genomsnittlig CTR (%)'],
                color_continuous_scale='RdYlGn'
            )
            fig.update_layout(
                height=400,
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                xaxis=dict(gridcolor='#333'),
                yaxis=dict(gridcolor='#333')
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("👥 Roller i systemet")
        
        # Role summary
        role_stats = df.groupby('Roll').agg({
            'campaign_id': 'count',
            'Bransch': 'nunique',
            'total_spend': 'sum',
            'CTR': 'mean',
            'CPC': 'mean'
        }).round(2)
        role_stats.columns = ['Kampanjer', 'Unika branscher', 'Total spend (SEK)', 'Genomsnittlig CTR (%)', 'Genomsnittlig CPC (SEK)']
        role_stats = role_stats.sort_values('Kampanjer', ascending=False)
        
        # Display top roles
        st.dataframe(
            role_stats.head(15).style.format({
                'Total spend (SEK)': '{:,.0f}',
                'Genomsnittlig CTR (%)': '{:.2f}',
                'Genomsnittlig CPC (SEK)': '{:.2f}'
            }),
            use_container_width=True
        )
        
        # Show which industries each role appears in
        st.subheader("🔍 Roller per bransch")
        
        selected_role = st.selectbox("Välj en roll för att se dess branscher:", role_stats.index.tolist())
        
        if selected_role:
            role_industries = df[df['Roll'] == selected_role].groupby('Bransch').agg({
                'campaign_id': 'count',
                'CTR': 'mean',
                'CPC': 'mean',
                'total_spend': 'sum'
            }).round(2)
            role_industries.columns = ['Kampanjer', 'CTR (%)', 'CPC (SEK)', 'Total spend (SEK)']
            role_industries = role_industries.sort_values('Kampanjer', ascending=False)
            
            st.dataframe(
                role_industries.style.format({
                    'Total spend (SEK)': '{:,.0f}',
                    'CTR (%)': '{:.2f}',
                    'CPC (SEK)': '{:.2f}'
                }),
                use_container_width=True
            )
    
    with tab3:
        st.subheader("🎯 Roll-Bransch Kombinationer")
        
        # Combination summary
        combo_stats = df.groupby('Roll_Bransch').agg({
            'campaign_id': 'count',
            'total_spend': 'sum',
            'CTR': 'mean',
            'CPC': 'mean',
            'platform': lambda x: ', '.join(x.value_counts().head(3).index.tolist())
        }).round(2)
        combo_stats.columns = ['Kampanjer', 'Total spend (SEK)', 'CTR (%)', 'CPC (SEK)', 'Top plattformar']
        combo_stats = combo_stats.sort_values('Kampanjer', ascending=False)
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            min_campaigns = st.number_input("Minst antal kampanjer:", min_value=1, value=5)
        with col2:
            min_ctr = st.number_input("Minst CTR (%):", min_value=0.0, value=0.0, step=0.5)
        with col3:
            max_cpc = st.number_input("Max CPC (SEK):", min_value=0.0, value=100.0, step=1.0)
        
        # Apply filters
        filtered_combos = combo_stats[
            (combo_stats['Kampanjer'] >= min_campaigns) &
            (combo_stats['CTR (%)'] >= min_ctr) &
            (combo_stats['CPC (SEK)'] <= max_cpc)
        ]
        
        st.info(f"Visar {len(filtered_combos)} av {len(combo_stats)} kombinationer baserat på filter")
        
        # Display filtered combinations
        st.dataframe(
            filtered_combos.head(20).style.format({
                'Total spend (SEK)': '{:,.0f}',
                'CTR (%)': '{:.2f}',
                'CPC (SEK)': '{:.2f}'
            }),
            use_container_width=True
        )
        
        # Heatmap of Role x Industry
        st.subheader("🗺️ Roll-Bransch Heatmap")
        
        # Create pivot table for heatmap
        pivot_data = df.pivot_table(
            values='CTR',
            index='Roll',
            columns='Bransch',
            aggfunc='mean'
        ).round(2)
        
        # Select top roles and industries for visibility
        top_roles = role_stats.head(10).index
        top_industries = industry_stats.head(10).index
        pivot_data = pivot_data.loc[
            pivot_data.index.intersection(top_roles),
            pivot_data.columns.intersection(top_industries)
        ]
        
        fig = px.imshow(
            pivot_data,
            labels=dict(x="Bransch", y="Roll", color="CTR (%)"),
            title="Genomsnittlig CTR per Roll-Bransch kombination",
            color_continuous_scale="RdYlGn",
            aspect="auto"
        )
        fig.update_layout(
            height=600,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.subheader("📊 Branschjämförelser")
        
        # Select two industries to compare
        col1, col2 = st.columns(2)
        with col1:
            industry1 = st.selectbox("Välj första bransch:", industry_stats.index.tolist())
        with col2:
            industry2 = st.selectbox("Välj andra bransch:", 
                                    [i for i in industry_stats.index.tolist() if i != industry1])
        
        if industry1 and industry2:
            # Get data for both industries
            ind1_data = df[df['Bransch'] == industry1]
            ind2_data = df[df['Bransch'] == industry2]
            
            # Comparison metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    f"{industry1} - Genomsnittlig CTR",
                    f"{ind1_data['CTR'].mean():.2f}%",
                    f"{(ind1_data['CTR'].mean() - ind2_data['CTR'].mean()):.2f}%"
                )
                st.metric(
                    f"{industry2} - Genomsnittlig CTR",
                    f"{ind2_data['CTR'].mean():.2f}%"
                )
            
            with col2:
                st.metric(
                    f"{industry1} - Genomsnittlig CPC",
                    f"{ind1_data['CPC'].mean():.2f} SEK",
                    f"{(ind1_data['CPC'].mean() - ind2_data['CPC'].mean()):.2f} SEK"
                )
                st.metric(
                    f"{industry2} - Genomsnittlig CPC",
                    f"{ind2_data['CPC'].mean():.2f} SEK"
                )
            
            with col3:
                st.metric(
                    f"{industry1} - Antal kampanjer",
                    f"{len(ind1_data):,}"
                )
                st.metric(
                    f"{industry2} - Antal kampanjer",
                    f"{len(ind2_data):,}"
                )
            
            # Common roles comparison
            st.subheader("🤝 Gemensamma roller")
            
            roles1 = set(ind1_data['Roll'].unique())
            roles2 = set(ind2_data['Roll'].unique())
            common_roles = roles1.intersection(roles2)
            
            if common_roles:
                comparison_data = []
                for role in common_roles:
                    r1_data = ind1_data[ind1_data['Roll'] == role]
                    r2_data = ind2_data[ind2_data['Roll'] == role]
                    
                    if len(r1_data) > 0 and len(r2_data) > 0:
                        comparison_data.append({
                            'Roll': role,
                            f'{industry1} CTR (%)': r1_data['CTR'].mean(),
                            f'{industry2} CTR (%)': r2_data['CTR'].mean(),
                            f'{industry1} CPC (SEK)': r1_data['CPC'].mean(),
                            f'{industry2} CPC (SEK)': r2_data['CPC'].mean(),
                            f'{industry1} Kampanjer': len(r1_data),
                            f'{industry2} Kampanjer': len(r2_data)
                        })
                
                if comparison_data:
                    comparison_df = pd.DataFrame(comparison_data).round(2)
                    comparison_df = comparison_df.sort_values(f'{industry1} Kampanjer', ascending=False)
                    
                    st.dataframe(
                        comparison_df.style.format({
                            f'{industry1} CTR (%)': '{:.2f}',
                            f'{industry2} CTR (%)': '{:.2f}',
                            f'{industry1} CPC (SEK)': '{:.2f}',
                            f'{industry2} CPC (SEK)': '{:.2f}'
                        }),
                        use_container_width=True
                    )
                    
                    # Visualization
                    fig = go.Figure()
                    
                    # Add CTR comparison
                    fig.add_trace(go.Bar(
                        name=f'{industry1} CTR',
                        x=comparison_df['Roll'],
                        y=comparison_df[f'{industry1} CTR (%)'],
                        marker_color='#4CAF50'
                    ))
                    
                    fig.add_trace(go.Bar(
                        name=f'{industry2} CTR',
                        x=comparison_df['Roll'],
                        y=comparison_df[f'{industry2} CTR (%)'],
                        marker_color='#2196F3'
                    ))
                    
                    fig.update_layout(
                        title="CTR-jämförelse för gemensamma roller",
                        barmode='group',
                        height=400,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white'),
                        xaxis=dict(gridcolor='#333'),
                        yaxis=dict(gridcolor='#333', title='CTR (%)')
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Inga gemensamma roller mellan dessa branscher")

if __name__ == "__main__":
    main()
