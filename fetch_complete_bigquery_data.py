#!/usr/bin/env python3
"""
Fetch comprehensive campaign data from BigQuery.
Aggregates daily data to campaign level and combines all platforms.
"""

import subprocess
import pandas as pd
from datetime import datetime

def run_bq_query(query, output_file):
    """Run a BigQuery query and save to CSV."""
    cmd = f'''bq query --use_legacy_sql=false --format=csv --max_rows=100000 "{query}" > {output_file} 2>/dev/null'''
    subprocess.run(cmd, shell=True)
    print(f"✅ Saved to {output_file}")

def main():
    print("🚀 Fetching comprehensive campaign data from BigQuery...")
    print("=" * 60)
    
    # First, let's get aggregated campaign data from all platforms
    aggregate_query = """
    WITH facebook_agg AS (
      SELECT 
        campaign_id,
        campaign as campaign_name,
        'facebook' as platform,
        account_name as company,
        MIN(date) as start_date,
        MAX(date) as end_date,
        DATE_DIFF(MAX(date), MIN(date), DAY) + 1 as campaign_days,
        SUM(impressions) as total_impressions,
        SUM(clicks) as total_clicks,
        SUM(spend) as total_spend,
        AVG(CAST(REPLACE(ctr, '%', '') AS FLOAT64)) as avg_ctr,
        COUNT(DISTINCT date) as active_days
      FROM `campaign_data.facebook_raw_data`
      WHERE campaign_id IS NOT NULL
      GROUP BY campaign_id, campaign, account_name
    ),
    linkedin_agg AS (
      SELECT 
        campaign_id,
        campaign as campaign_name,
        'linkedin' as platform,
        account_name as company,
        MIN(date) as start_date,
        MAX(date) as end_date,
        DATE_DIFF(MAX(date), MIN(date), DAY) + 1 as campaign_days,
        SUM(impressions) as total_impressions,
        SUM(clicks) as total_clicks,
        SUM(spend) as total_spend,
        SAFE_DIVIDE(SUM(clicks), SUM(impressions)) * 100 as avg_ctr,
        COUNT(DISTINCT date) as active_days
      FROM `campaign_data.linkedin_raw_data`
      WHERE campaign_id IS NOT NULL
      GROUP BY campaign_id, campaign, account_name
    ),
    snapchat_agg AS (
      SELECT 
        campaign_id,
        campaign_name,
        'snapchat' as platform,
        NULL as company,
        MIN(date) as start_date,
        MAX(date) as end_date,
        DATE_DIFF(MAX(date), MIN(date), DAY) + 1 as campaign_days,
        SUM(impressions) as total_impressions,
        SUM(swipes) as total_clicks,
        SUM(spend) as total_spend,
        SAFE_DIVIDE(SUM(swipes), SUM(impressions)) * 100 as avg_ctr,
        COUNT(DISTINCT date) as active_days
      FROM `campaign_data.snapchat_raw_data`
      WHERE campaign_id IS NOT NULL
      GROUP BY campaign_id, campaign_name
    ),
    tiktok_agg AS (
      SELECT 
        campaign_id,
        campaign_name,
        'tiktok' as platform,
        advertiser_name as company,
        MIN(date) as start_date,
        MAX(date) as end_date,
        DATE_DIFF(MAX(date), MIN(date), DAY) + 1 as campaign_days,
        SUM(impressions) as total_impressions,
        SUM(clicks) as total_clicks,
        SUM(spend) as total_spend,
        SAFE_DIVIDE(SUM(clicks), SUM(impressions)) * 100 as avg_ctr,
        COUNT(DISTINCT date) as active_days
      FROM `campaign_data.tiktok_raw_data`
      WHERE campaign_id IS NOT NULL
      GROUP BY campaign_id, campaign_name, advertiser_name
    )
    
    SELECT * FROM (
      SELECT * FROM facebook_agg
      UNION ALL
      SELECT * FROM linkedin_agg
      UNION ALL
      SELECT * FROM snapchat_agg
      UNION ALL
      SELECT * FROM tiktok_agg
    )
    WHERE total_spend > 100  -- Filter out test campaigns
    ORDER BY total_spend DESC
    LIMIT 5000  -- Get top 5000 campaigns by spend
    """
    
    print("\n📊 Fetching aggregated campaign data (top 5000 by spend)...")
    run_bq_query(aggregate_query, "bigquery_all_campaigns_aggregated.csv")
    
    # Get daily performance data for top campaigns (for time series analysis)
    daily_query = """
    WITH top_campaigns AS (
      SELECT campaign_id
      FROM `campaign_data.facebook_raw_data`
      WHERE spend > 100
      GROUP BY campaign_id
      ORDER BY SUM(spend) DESC
      LIMIT 100
    )
    SELECT 
      f.campaign_id,
      f.campaign as campaign_name,
      f.date,
      f.impressions,
      f.clicks,
      f.spend,
      f.ctr,
      f.reach,
      EXTRACT(DAYOFWEEK FROM f.date) as day_of_week,
      EXTRACT(WEEK FROM f.date) as week_num
    FROM `campaign_data.facebook_raw_data` f
    INNER JOIN top_campaigns t ON f.campaign_id = t.campaign_id
    ORDER BY f.campaign_id, f.date
    """
    
    print("\n📈 Fetching daily performance data for top 100 Facebook campaigns...")
    run_bq_query(daily_query, "bigquery_daily_performance_sample.csv")
    
    # Get campaign metadata and classifications
    metadata_query = """
    SELECT DISTINCT
      campaign_id,
      campaign as campaign_name,
      account_name as company,
      MIN(date) as first_seen,
      MAX(date) as last_seen,
      COUNT(DISTINCT ad_id) as num_ads,
      COUNT(DISTINCT adset_id) as num_adsets,
      STRING_AGG(DISTINCT publisher_platform, ', ') as platforms_used
    FROM `campaign_data.facebook_raw_data`
    WHERE campaign_id IS NOT NULL
    GROUP BY campaign_id, campaign, account_name
    LIMIT 1000
    """
    
    print("\n🏷️ Fetching campaign metadata...")
    run_bq_query(metadata_query, "bigquery_campaign_metadata.csv")
    
    # Summary statistics
    summary_query = """
    SELECT 
      'facebook' as platform,
      COUNT(DISTINCT campaign_id) as unique_campaigns,
      COUNT(DISTINCT account_name) as unique_advertisers,
      SUM(spend) as total_spend,
      SUM(clicks) as total_clicks,
      SUM(impressions) as total_impressions,
      AVG(SAFE_DIVIDE(clicks, impressions) * 100) as avg_ctr,
      AVG(SAFE_DIVIDE(spend, NULLIF(clicks, 0))) as avg_cpc
    FROM `campaign_data.facebook_raw_data`
    UNION ALL
    SELECT 
      'linkedin' as platform,
      COUNT(DISTINCT campaign_id) as unique_campaigns,
      COUNT(DISTINCT account_name) as unique_advertisers,
      SUM(spend) as total_spend,
      SUM(clicks) as total_clicks,
      SUM(impressions) as total_impressions,
      AVG(SAFE_DIVIDE(clicks, impressions) * 100) as avg_ctr,
      AVG(SAFE_DIVIDE(spend, NULLIF(clicks, 0))) as avg_cpc
    FROM `campaign_data.linkedin_raw_data`
    UNION ALL
    SELECT 
      'snapchat' as platform,
      COUNT(DISTINCT campaign_id) as unique_campaigns,
      COUNT(DISTINCT NULL) as unique_advertisers,
      SUM(spend) as total_spend,
      SUM(swipes) as total_clicks,
      SUM(impressions) as total_impressions,
      AVG(SAFE_DIVIDE(swipes, impressions) * 100) as avg_ctr,
      AVG(SAFE_DIVIDE(spend, NULLIF(swipes, 0))) as avg_cpc
    FROM `campaign_data.snapchat_raw_data`
    UNION ALL
    SELECT 
      'tiktok' as platform,
      COUNT(DISTINCT campaign_id) as unique_campaigns,
      COUNT(DISTINCT advertiser_name) as unique_advertisers,
      SUM(spend) as total_spend,
      SUM(clicks) as total_clicks,
      SUM(impressions) as total_impressions,
      AVG(SAFE_DIVIDE(clicks, impressions) * 100) as avg_ctr,
      AVG(SAFE_DIVIDE(spend, NULLIF(clicks, 0))) as avg_cpc
    FROM `campaign_data.tiktok_raw_data`
    """
    
    print("\n📊 Fetching platform summary statistics...")
    run_bq_query(summary_query, "bigquery_platform_summary.csv")
    
    print("\n" + "=" * 60)
    print("✅ Data fetch complete! Created files:")
    print("  1. bigquery_all_campaigns_aggregated.csv - Top 5000 campaigns")
    print("  2. bigquery_daily_performance_sample.csv - Daily data for analysis")
    print("  3. bigquery_campaign_metadata.csv - Campaign metadata")
    print("  4. bigquery_platform_summary.csv - Platform statistics")
    
    # Load and show summary
    try:
        df = pd.read_csv("bigquery_all_campaigns_aggregated.csv")
        print(f"\n📈 Aggregated Data Summary:")
        print(f"  - Total campaigns: {len(df)}")
        print(f"  - Total spend: {df['total_spend'].sum():,.0f} SEK")
        print(f"  - Date range: {df['start_date'].min()} to {df['end_date'].max()}")
        print(f"  - Platforms: {df['platform'].value_counts().to_dict()}")
    except Exception as e:
        print(f"Note: Could not load summary - {e}")

if __name__ == "__main__":
    main()
