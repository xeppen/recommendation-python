-- BigQuery Manual Queries for Data Extraction
-- Run these in BigQuery Console if Python authentication issues persist

-- Query 1: Get campaign performance data with role/location parsing potential
-- Copy/paste this into BigQuery Console
WITH campaign_performance AS (
    SELECT 
        d.campaign_id,
        d.campaign as campaign_name,
        d.data_source as platform,
        d.campaign_start_time,
        SUM(f.impressions) as total_impressions,
        SUM(f.clicks) as total_clicks,
        SUM(f.spend) as total_spend,
        COUNT(DISTINCT f.date) as campaign_days,
        SAFE_DIVIDE(SUM(f.clicks), SUM(f.impressions)) * 100 as ctr_percent,
        SAFE_DIVIDE(SUM(f.spend), SUM(f.clicks)) as cpc_sek
    FROM `we-select-data-prod.campaign_analysis_dim.dim_all_campaigns` d
    JOIN `we-select-data-prod.campaign_analysis_fact.fact_all_campaigns` f
    ON d.campaign_id = f.campaign_id
    WHERE f.date >= '2024-03-01'
    AND f.impressions > 0
    GROUP BY d.campaign_id, d.campaign, d.data_source, d.campaign_start_time
    HAVING total_spend >= 500
)
SELECT 
    campaign_name,
    platform,
    total_impressions,
    total_clicks,
    total_spend,
    campaign_days,
    ROUND(ctr_percent, 3) as ctr_percent,
    ROUND(cpc_sek, 2) as cpc_sek,
    ROUND(total_spend / campaign_days, 2) as daily_spend_sek,
    campaign_start_time
FROM campaign_performance
ORDER BY total_spend DESC
LIMIT 200;

-- Query 2: Platform-specific performance analysis
-- Shows which platforms perform best for different types of campaigns
SELECT 
    platform,
    COUNT(*) as campaign_count,
    SUM(total_impressions) as total_impressions,
    SUM(total_clicks) as total_clicks,
    SUM(total_spend) as total_spend,
    ROUND(AVG(ctr_percent), 3) as avg_ctr,
    ROUND(AVG(cpc_sek), 2) as avg_cpc,
    ROUND(SUM(total_spend) / SUM(total_clicks), 2) as overall_cpc
FROM (
    SELECT 
        d.data_source as platform,
        SUM(f.impressions) as total_impressions,
        SUM(f.clicks) as total_clicks,
        SUM(f.spend) as total_spend,
        SAFE_DIVIDE(SUM(f.clicks), SUM(f.impressions)) * 100 as ctr_percent,
        SAFE_DIVIDE(SUM(f.spend), SUM(f.clicks)) as cpc_sek
    FROM `we-select-data-prod.campaign_analysis_dim.dim_all_campaigns` d
    JOIN `we-select-data-prod.campaign_analysis_fact.fact_all_campaigns` f
    ON d.campaign_id = f.campaign_id
    WHERE f.date >= '2024-03-01'
    AND f.impressions > 0
    GROUP BY d.campaign_id, d.data_source
    HAVING total_spend >= 100
)
GROUP BY platform
ORDER BY total_spend DESC;

-- Query 3: Extract campaigns with job titles for manual parsing
-- Use this to get campaign names that you can process with the Python parser
SELECT DISTINCT
    d.campaign as campaign_name,
    d.data_source as platform,
    SUM(f.spend) as total_spend,
    SUM(f.impressions) as total_impressions,
    SUM(f.clicks) as total_clicks
FROM `we-select-data-prod.campaign_analysis_dim.dim_all_campaigns` d
JOIN `we-select-data-prod.campaign_analysis_fact.fact_all_campaigns` f
ON d.campaign_id = f.campaign_id
WHERE f.date >= '2024-06-01'
AND f.impressions > 0
AND d.campaign LIKE '%-%-%'  -- Filter for structured campaign names
GROUP BY d.campaign, d.data_source
HAVING total_spend >= 1000  -- Focus on significant campaigns
ORDER BY total_spend DESC
LIMIT 100;

-- Query 4: Job role extraction patterns
-- Helps identify common job role patterns in campaign names
SELECT 
    REGEXP_EXTRACT(campaign, r'^[^-]+ - ([^-]+)') as potential_job_role,
    COUNT(*) as frequency,
    SUM(total_spend) as total_spend
FROM (
    SELECT 
        d.campaign,
        SUM(f.spend) as total_spend
    FROM `we-select-data-prod.campaign_analysis_dim.dim_all_campaigns` d
    JOIN `we-select-data-prod.campaign_analysis_fact.fact_all_campaigns` f
    ON d.campaign_id = f.campaign_id
    WHERE f.date >= '2024-03-01'
    GROUP BY d.campaign
    HAVING total_spend >= 500
)
WHERE potential_job_role IS NOT NULL
GROUP BY potential_job_role
ORDER BY total_spend DESC
LIMIT 50;
