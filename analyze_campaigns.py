"""
Quick analysis script to test campaign parsing with real BigQuery data
"""

from google.cloud import bigquery
from campaign_parser import CampaignNameParser
import pandas as pd

def quick_analysis():
    """Run quick analysis on recent campaign data"""
    
    print("🔍 Analyzing Recent Campaign Data\n")
    
    # Initialize
    client = bigquery.Client(project="we-select-data-prod")
    parser = CampaignNameParser()
    
    # Get recent campaign data
    query = """
    SELECT 
        d.campaign_id,
        d.campaign as campaign_name,
        d.data_source as platform,
        SUM(f.impressions) as total_impressions,
        SUM(f.clicks) as total_clicks,
        SUM(f.spend) as total_spend
    FROM `we-select-data-prod.campaign_analysis_dim.dim_all_campaigns` d
    JOIN `we-select-data-prod.campaign_analysis_fact.fact_all_campaigns` f
    ON d.campaign_id = f.campaign_id
    WHERE f.date >= '2024-08-01'
    AND f.impressions > 0
    GROUP BY d.campaign_id, d.campaign, d.data_source
    HAVING total_impressions > 100
    ORDER BY total_spend DESC
    LIMIT 20
    """
    
    print("📊 Fetching top 20 campaigns by spend (Aug 2024+)...")
    df = client.query(query).to_dataframe()
    
    print(f"✅ Loaded {len(df)} campaigns\n")
    
    # Parse campaign names
    parsed_results = []
    for _, row in df.iterrows():
        parsed = parser.parse_campaign_name(row['campaign_name'])
        
        result = {
            'campaign_id': row['campaign_id'],
            'platform': row['platform'],
            'job_role': parsed['job_role'],
            'location': parsed['location'],
            'package_type': parsed['package_type'],
            'confidence': parsed['confidence_score'],
            'impressions': row['total_impressions'],
            'clicks': row['total_clicks'],
            'spend': row['total_spend'],
            'ctr': row['total_clicks'] / row['total_impressions'] if row['total_impressions'] > 0 else 0,
            'cpc': row['total_spend'] / row['total_clicks'] if row['total_clicks'] > 0 else 0
        }
        parsed_results.append(result)
    
    results_df = pd.DataFrame(parsed_results)
    
    # Analysis 1: Role-Platform Performance
    print("🎯 TOP ROLE-PLATFORM COMBINATIONS BY PERFORMANCE:\n")
    
    role_platform = results_df[results_df['confidence'] >= 0.7].groupby(['job_role', 'platform']).agg({
        'impressions': 'sum',
        'clicks': 'sum',
        'spend': 'sum',
        'ctr': 'mean',
        'cpc': 'mean'
    }).reset_index()
    
    role_platform = role_platform.sort_values('spend', ascending=False).head(10)
    
    for _, row in role_platform.iterrows():
        print(f"👔 {row['job_role']} on {row['platform'].upper()}")
        print(f"   💰 Spend: {row['spend']:.0f} SEK | 👀 Impressions: {row['impressions']:.0f} | 🎯 CTR: {row['ctr']:.3f}%")
        print()
    
    # Analysis 2: Location Performance
    print("📍 TOP LOCATIONS BY PLATFORM:\n")
    
    location_platform = results_df[
        (results_df['confidence'] >= 0.7) & 
        (results_df['location'].notna())
    ].groupby(['location', 'platform']).agg({
        'spend': 'sum',
        'impressions': 'sum',
        'ctr': 'mean'
    }).reset_index()
    
    location_platform = location_platform.sort_values('spend', ascending=False).head(8)
    
    for _, row in location_platform.iterrows():
        print(f"📍 {row['location']} on {row['platform'].upper()}")
        print(f"   💰 Spend: {row['spend']:.0f} SEK | 👀 Impressions: {row['impressions']:.0f} | 🎯 CTR: {row['ctr']:.3f}%")
        print()
    
    # Analysis 3: Package Type Performance
    print("📦 PACKAGE TYPE PERFORMANCE:\n")
    
    package_perf = results_df[results_df['confidence'] >= 0.7].groupby('package_type').agg({
        'spend': 'sum',
        'impressions': 'sum',
        'clicks': 'sum',
        'ctr': 'mean',
        'cpc': 'mean'
    }).reset_index()
    
    package_perf = package_perf.sort_values('spend', ascending=False)
    
    for _, row in package_perf.iterrows():
        if pd.notna(row['package_type']):
            print(f"📦 {row['package_type']}")
            print(f"   💰 Total Spend: {row['spend']:.0f} SEK | 🎯 Avg CTR: {row['ctr']:.3f}% | 💳 Avg CPC: {row['cpc']:.2f}")
            print()
    
    # Save detailed results
    results_df.to_csv('campaign_analysis_results.csv', index=False)
    print("💾 Detailed results saved to 'campaign_analysis_results.csv'")
    
    print(f"\n📊 SUMMARY:")
    print(f"   • Parsed {len(results_df)} campaigns")
    print(f"   • Average confidence: {results_df['confidence'].mean():.2f}")
    print(f"   • High confidence (≥0.7): {(results_df['confidence'] >= 0.7).sum()} campaigns")

if __name__ == "__main__":
    quick_analysis()
