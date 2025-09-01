# BigQuery Campaign Data Analysis - Insights Report

## 📊 Overview

WeSelect has comprehensive campaign performance data stored in Google BigQuery with **520,019 campaign records** across multiple platforms. This data represents a goldmine for building performance-based job advertising recommendations.

## 🏗️ Data Architecture

### Project Structure
- **Project**: `we-select-data-prod`
- **Main Datasets**: 
  - `campaign_data` - Raw platform data
  - `campaign_analysis_fact` - Unified fact tables
  - `campaign_analysis_dim` - Dimension tables

## 📈 Platform Coverage

### 1. **Facebook/Meta** (`facebook_raw_data`)
- **Records**: 1,689,691 rows
- **Size**: 1.17 GB
- **Key Metrics**:
  - `impressions`, `clicks`, `spend`
  - `link_clicks`, `reach`
  - `video_p25_watched_actions_video_view`
  - `ctr`, `outbound_clicks_ctr`

### 2. **LinkedIn** (`linkedin_raw_data`)
- **Records**: 31,319 rows
- **Size**: 17.4 MB
- **Key Metrics**:
  - `impressions`, `clicks`, `spend`
  - `job_apply_clicks` (crucial for job ads!)
  - `landing_page_clicks`, `engagements`
  - `viral_clicks`, `viral_landing_page_clicks`

### 3. **Reddit** (`reddit_raw_data`)
- **Records**: 12,064 rows
- **Size**: 6.1 MB
- **Key Metrics**:
  - `impressions`, `clicks`, `spend`
  - `video_watched_25_percent`, `video_watched_75_percent`
  - `video_watched_3_seconds`

### 4. **Snapchat** (`snapchat_raw_data`)
- **Records**: 33,881 rows
- **Size**: 19.9 MB
- **Key Metrics**:
  - `impressions`, `clicks`, `spend`
  - `total_reach`, `quartile_1`
  - `conversion_ad_click`

### 5. **TikTok** (`tiktok_raw_data`)
- **Records**: 15,310 rows
- **Size**: 8.1 MB
- **Key Metrics**:
  - `impressions`, `clicks`, `spend`
  - `reach`, `play_first_quartile`, `play_third_quartile`

## 🎯 Campaign Naming Structure

Campaign names follow a structured format containing valuable metadata:

### Example Campaign Names:
```
LRF Media AB - Grafisk formgivare till LRF Media - Stockholm - Boost Plus (Tjänstemän)
Uppsala kommun - Fastighetsansvarig förskolan - Uppsala - Boost Plus: Utökad Radie
TioHundra AB - Vice VD/sjukhuschef till Norrtälje sjukhus - Norrtälje - Boost Plus
```

### Extractable Information:
1. **Company Name**: First part before " - "
2. **Job Title**: Second part (the actual role)
3. **Location**: Geographic targeting
4. **Package Type**: "Boost", "Boost Plus", "Boost Auto"
5. **Additional Targeting**: "(Tjänstemän)", "Utökad Radie"

## 📊 Unified Data Structure

### Fact Table (`fact_all_campaigns`)
- **Records**: 520,019 unified campaign records
- **Time Range**: Current data up to 2025-09-01
- **Partitioned**: By month for efficient querying
- **Key Fields**:
  - `campaign_id`, `source`, `date`
  - `impressions`, `clicks`, `spend`

### Dimension Table (`dim_all_campaigns`)
- **Records**: 11,467 unique campaigns
- **Key Fields**:
  - `campaign_id`, `campaign` (name)
  - `data_source`, `ticket_id`
  - `campaign_start_time`, `campaign_stop_time`

## 💎 Key Insights for Recommendation System

### 1. **Rich Performance Data**
- **Cost-per-click** data across all platforms
- **Platform-specific engagement** metrics
- **Job application clicks** (LinkedIn specific)
- **Video engagement** metrics (Reddit, Snapchat, TikTok)

### 2. **Job Role Intelligence**
- Campaign names contain **actual job titles**
- **Location-based** performance data
- **Package type** performance comparison
- **Industry patterns** (healthcare, tech, finance, etc.)

### 3. **Platform Performance Patterns**
- **LinkedIn**: Strong for professional roles (job_apply_clicks)
- **Facebook**: Broad reach with detailed engagement metrics
- **Reddit/TikTok**: Video-focused metrics for younger demographics
- **Snapchat**: Conversion tracking capabilities

## 🚀 Recommendation System Enhancement Opportunities

### 1. **Performance-Based Recommendations**
Instead of just similarity matching, we can recommend based on:
- **Historical ROI** for similar job titles
- **Platform effectiveness** per role category
- **Budget optimization** based on past performance

### 2. **Location Intelligence**
- **Geographic performance** patterns
- **City-specific** platform preferences
- **Regional cost variations**

### 3. **Industry Insights**
- **Sector-specific** channel effectiveness
- **Role category** performance patterns
- **Seasonal trends** in recruitment

### 4. **Package Optimization**
- **"Boost" vs "Boost Plus"** performance comparison
- **Package type** effectiveness per role
- **Budget allocation** recommendations

## 📋 Data Quality Assessment

### ✅ Strengths:
- **Comprehensive coverage** across 5 major platforms
- **Consistent daily updates** (latest: 2025-09-01)
- **Rich performance metrics** per platform
- **Structured campaign naming** with extractable metadata
- **Large dataset** (1.7M+ Facebook records alone)

### ⚠️ Considerations:
- **Campaign name parsing** needed to extract job titles
- **Data normalization** required across platforms
- **Performance metric** standardization needed
- **Historical data depth** varies by platform

## 🔧 Integration Recommendations

### Phase 1: Data Pipeline
1. **Extract job titles** from campaign names using NLP
2. **Normalize performance metrics** across platforms
3. **Create unified performance** scoring system

### Phase 2: Enhanced Recommendations
1. **Replace similarity-based** with performance-based recommendations
2. **Add ROI optimization** to budget suggestions
3. **Include platform effectiveness** scoring

### Phase 3: Advanced Analytics
1. **Predictive performance** modeling
2. **Seasonal trend** analysis
3. **A/B testing** framework integration

## 🎯 Next Steps

1. **Build data extraction pipeline** from BigQuery
2. **Parse campaign names** to extract job roles and metadata  
3. **Calculate performance metrics** (CTR, CPC, ROAS)
4. **Integrate with current recommendation system**
5. **Create performance-based scoring** algorithm

---

**This data represents a significant upgrade opportunity** - moving from similarity-based to **performance-based recommendations** using real campaign data from 520k+ campaigns across 5 platforms.
