#!/bin/bash

echo "🚀 Fetching ALL campaign data from BigQuery..."
echo "This will take a few minutes..."

# Fetch all Facebook campaigns (aggregated)
echo "📊 Fetching Facebook campaigns..."
bq query --use_legacy_sql=false --format=csv --max_rows=10000 '
SELECT 
  campaign_id,
  campaign as campaign_name,
  "facebook" as platform,
  account_name as company,
  MIN(date) as start_date,
  MAX(date) as end_date,
  DATE_DIFF(MAX(date), MIN(date), DAY) + 1 as campaign_days,
  SUM(impressions) as total_impressions,
  SUM(clicks) as total_clicks,
  SUM(spend) as total_spend,
  AVG(SAFE_CAST(REPLACE(ctr, "%", "") AS FLOAT64)) as avg_ctr_percent,
  SAFE_DIVIDE(SUM(spend), NULLIF(SUM(clicks), 0)) as cpc_sek,
  COUNT(DISTINCT date) as active_days
FROM `campaign_data.facebook_raw_data`
WHERE campaign_id IS NOT NULL 
  AND spend > 0
GROUP BY campaign_id, campaign, account_name
HAVING SUM(spend) > 500  -- Only meaningful campaigns
' > facebook_campaigns.csv 2>/dev/null

# Fetch all LinkedIn campaigns
echo "📊 Fetching LinkedIn campaigns..."
bq query --use_legacy_sql=false --format=csv --max_rows=2000 '
SELECT 
  campaign_id,
  campaign as campaign_name,
  "linkedin" as platform,
  account_name as company,
  MIN(date) as start_date,
  MAX(date) as end_date,
  DATE_DIFF(MAX(date), MIN(date), DAY) + 1 as campaign_days,
  SUM(impressions) as total_impressions,
  SUM(clicks) as total_clicks,
  SUM(spend) as total_spend,
  SAFE_DIVIDE(SUM(clicks), NULLIF(SUM(impressions), 0)) * 100 as avg_ctr_percent,
  SAFE_DIVIDE(SUM(spend), NULLIF(SUM(clicks), 0)) as cpc_sek,
  COUNT(DISTINCT date) as active_days
FROM `campaign_data.linkedin_raw_data`
WHERE campaign_id IS NOT NULL 
  AND spend > 0
GROUP BY campaign_id, campaign, account_name
HAVING SUM(spend) > 500
' > linkedin_campaigns.csv 2>/dev/null

# Fetch all Snapchat campaigns
echo "📊 Fetching Snapchat campaigns..."
bq query --use_legacy_sql=false --format=csv --max_rows=500 '
SELECT 
  campaign_id,
  campaign_name,
  "snapchat" as platform,
  NULL as company,
  MIN(date) as start_date,
  MAX(date) as end_date,
  DATE_DIFF(MAX(date), MIN(date), DAY) + 1 as campaign_days,
  SUM(impressions) as total_impressions,
  SUM(swipes) as total_clicks,
  SUM(spend) as total_spend,
  SAFE_DIVIDE(SUM(swipes), NULLIF(SUM(impressions), 0)) * 100 as avg_ctr_percent,
  SAFE_DIVIDE(SUM(spend), NULLIF(SUM(swipes), 0)) as cpc_sek,
  COUNT(DISTINCT date) as active_days
FROM `campaign_data.snapchat_raw_data`
WHERE campaign_id IS NOT NULL 
  AND spend > 0
GROUP BY campaign_id, campaign_name
HAVING SUM(spend) > 500
' > snapchat_campaigns.csv 2>/dev/null

# Fetch all TikTok campaigns
echo "📊 Fetching TikTok campaigns..."
bq query --use_legacy_sql=false --format=csv --max_rows=200 '
SELECT 
  campaign_id,
  campaign_name,
  "tiktok" as platform,
  advertiser_name as company,
  MIN(date) as start_date,
  MAX(date) as end_date,
  DATE_DIFF(MAX(date), MIN(date), DAY) + 1 as campaign_days,
  SUM(impressions) as total_impressions,
  SUM(clicks) as total_clicks,
  SUM(spend) as total_spend,
  SAFE_DIVIDE(SUM(clicks), NULLIF(SUM(impressions), 0)) * 100 as avg_ctr_percent,
  SAFE_DIVIDE(SUM(spend), NULLIF(SUM(clicks), 0)) as cpc_sek,
  COUNT(DISTINCT date) as active_days
FROM `campaign_data.tiktok_raw_data`
WHERE campaign_id IS NOT NULL 
  AND spend > 0
GROUP BY campaign_id, campaign_name, advertiser_name
HAVING SUM(spend) > 500
' > tiktok_campaigns.csv 2>/dev/null

echo "✅ Data fetch complete!"
echo ""
echo "📁 Files created:"
wc -l *_campaigns.csv

echo ""
echo "🔧 Now combining all platform data..."

# Combine all platforms into one file using Python
python3 -c "
import pandas as pd
import glob

# Read all platform files
all_files = glob.glob('*_campaigns.csv')
dfs = []

for file in all_files:
    try:
        df = pd.read_csv(file)
        if len(df) > 0:
            dfs.append(df)
            print(f'  ✅ Loaded {len(df)} campaigns from {file}')
    except:
        print(f'  ⚠️  Could not load {file}')

if dfs:
    # Combine all dataframes
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Save combined dataset
    combined_df.to_csv('all_platforms_campaigns_complete.csv', index=False)
    
    print(f'\\n📊 FINAL DATASET SUMMARY:')
    print(f'  Total campaigns: {len(combined_df)}')
    print(f'  Total spend: {combined_df[\"total_spend\"].sum():,.0f} SEK')
    print(f'  Platforms: {combined_df[\"platform\"].value_counts().to_dict()}')
    print(f'\\n✅ Saved to: all_platforms_campaigns_complete.csv')
else:
    print('❌ No data files found')
"
