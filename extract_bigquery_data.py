"""
BigQuery Data Extractor for Training Data Enhancement

Extracts campaign performance data from BigQuery and structures it 
similar to the training CSV but with real social media analytics.
"""

import pandas as pd
import re
from google.cloud import bigquery
from campaign_parser import CampaignNameParser

class BigQueryDataExtractor:
    """Extract and structure BigQuery campaign data for training"""
    
    def __init__(self, project_id: str = "we-select-data-prod"):
        self.client = bigquery.Client(project=project_id)
        self.parser = CampaignNameParser()
    
    def extract_campaign_data(self, date_from: str = "2024-01-01", min_spend: float = 100.0) -> pd.DataFrame:
        """
        Extract campaign data with performance metrics
        
        Args:
            date_from: Start date for data extraction (YYYY-MM-DD)
            min_spend: Minimum spend threshold to filter campaigns
            
        Returns:
            DataFrame with structured training data + performance metrics
        """
        
        print(f"🔍 Extracting campaign data from {date_from} with min spend {min_spend} SEK...")
        
        # Query to get campaign performance data
        query = f"""
        WITH campaign_performance AS (
            SELECT 
                d.campaign_id,
                d.campaign as campaign_name,
                d.data_source as platform,
                d.campaign_start_time,
                d.campaign_stop_time,
                SUM(f.impressions) as total_impressions,
                SUM(f.clicks) as total_clicks,
                SUM(f.spend) as total_spend,
                COUNT(DISTINCT f.date) as campaign_days,
                MIN(f.date) as first_active_date,
                MAX(f.date) as last_active_date
            FROM `{self.client.project}.campaign_analysis_dim.dim_all_campaigns` d
            JOIN `{self.client.project}.campaign_analysis_fact.fact_all_campaigns` f
            ON d.campaign_id = f.campaign_id
            WHERE f.date >= '{date_from}'
            AND f.impressions > 0
            GROUP BY d.campaign_id, d.campaign, d.data_source, d.campaign_start_time, d.campaign_stop_time
            HAVING total_spend >= {min_spend}
        )
        SELECT * FROM campaign_performance
        ORDER BY total_spend DESC
        """
        
        print("📊 Running BigQuery extraction...")
        df = self.client.query(query).to_dataframe()
        print(f"✅ Extracted {len(df)} campaign records")
        
        return df
    
    def parse_and_structure_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse campaign names and structure data for training
        
        Args:
            df: Raw campaign performance DataFrame
            
        Returns:
            Structured DataFrame similar to training CSV + performance metrics
        """
        
        print("🔧 Parsing campaign names and structuring data...")
        
        structured_data = []
        
        for _, row in df.iterrows():
            # Parse campaign name
            parsed = self.parser.parse_campaign_name(row['campaign_name'])
            
            # Skip if confidence too low
            if parsed['confidence_score'] < 0.5:
                continue
                
            # Calculate performance metrics
            ctr = (row['total_clicks'] / row['total_impressions']) * 100 if row['total_impressions'] > 0 else 0
            cpc = row['total_spend'] / row['total_clicks'] if row['total_clicks'] > 0 else 0
            daily_spend = row['total_spend'] / row['campaign_days'] if row['campaign_days'] > 0 else 0
            
            # Map parsed data to training structure
            record = {
                # Basic info (similar to training CSV)
                'Roll': parsed['job_role'],
                'Company': parsed['company'],
                'Location': parsed['location'],
                'Package_Type': parsed['package_type'],
                'Platform': row['platform'],
                'Confidence_Score': parsed['confidence_score'],
                
                # Performance metrics (NEW - from BigQuery)
                'Total_Impressions': int(row['total_impressions']),
                'Total_Clicks': int(row['total_clicks']),
                'Total_Spend_SEK': round(row['total_spend'], 2),
                'CTR_Percent': round(ctr, 3),
                'CPC_SEK': round(cpc, 2),
                'Campaign_Days': int(row['campaign_days']),
                'Daily_Spend_SEK': round(daily_spend, 2),
                
                # Campaign metadata
                'Campaign_ID': row['campaign_id'],
                'Campaign_Start': row['campaign_start_time'],
                'Campaign_Stop': row['campaign_stop_time'],
                'First_Active': row['first_active_date'],
                'Last_Active': row['last_active_date'],
                
                # Original campaign name for reference
                'Original_Campaign_Name': row['campaign_name']
            }
            
            structured_data.append(record)
        
        result_df = pd.DataFrame(structured_data)
        print(f"✅ Structured {len(result_df)} records with confidence ≥ 0.5")
        
        return result_df
    
    def create_platform_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create summary by role and platform (similar to training CSV structure)
        
        Args:
            df: Structured campaign DataFrame
            
        Returns:
            Summary DataFrame grouped by role and platform
        """
        
        print("📈 Creating role-platform performance summary...")
        
        # Group by role and platform
        summary = df.groupby(['Roll', 'Platform']).agg({
            'Total_Impressions': 'sum',
            'Total_Clicks': 'sum',
            'Total_Spend_SEK': 'sum',
            'Campaign_Days': 'sum',
            'Campaign_ID': 'count',  # Number of campaigns
            'CTR_Percent': 'mean',
            'CPC_SEK': 'mean',
            'Daily_Spend_SEK': 'mean',
            'Location': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'Unknown'  # Most common location
        }).reset_index()
        
        # Rename columns for clarity
        summary = summary.rename(columns={
            'Campaign_ID': 'Number_of_Campaigns',
            'Location': 'Most_Common_Location'
        })
        
        # Calculate overall performance metrics
        summary['Avg_CTR'] = round(summary['CTR_Percent'], 3)
        summary['Avg_CPC'] = round(summary['CPC_SEK'], 2)
        summary['Total_Budget_Used'] = round(summary['Total_Spend_SEK'], 2)
        
        # Sort by total spend
        summary = summary.sort_values(['Roll', 'Total_Spend_SEK'], ascending=[True, False])
        
        print(f"✅ Created summary with {len(summary)} role-platform combinations")
        
        return summary
    
    def save_extracted_data(self, detailed_df: pd.DataFrame, summary_df: pd.DataFrame, 
                           output_prefix: str = "bigquery_extracted"):
        """
        Save extracted data to CSV files
        
        Args:
            detailed_df: Detailed campaign data
            summary_df: Role-platform summary
            output_prefix: Prefix for output files
        """
        
        detailed_file = f"{output_prefix}_detailed.csv"
        summary_file = f"{output_prefix}_summary.csv"
        
        # Save detailed data
        detailed_df.to_csv(detailed_file, index=False)
        print(f"💾 Detailed data saved to: {detailed_file}")
        
        # Save summary data  
        summary_df.to_csv(summary_file, index=False)
        print(f"💾 Summary data saved to: {summary_file}")
        
        # Print sample of what was extracted
        print(f"\n📋 SAMPLE OF EXTRACTED DATA:")
        print("=" * 60)
        print(summary_df[['Roll', 'Platform', 'Number_of_Campaigns', 'Total_Budget_Used', 'Avg_CTR', 'Avg_CPC']].head(10).to_string(index=False))

def main():
    """Extract BigQuery data and create training-ready datasets"""
    
    print("🚀 BigQuery Training Data Extraction")
    print("=" * 50)
    
    # Initialize extractor
    extractor = BigQueryDataExtractor()
    
    # Extract campaign data (last 6 months, min 500 SEK spend)
    raw_df = extractor.extract_campaign_data(
        date_from="2024-03-01", 
        min_spend=500.0
    )
    
    # Parse and structure data
    structured_df = extractor.parse_and_structure_data(raw_df)
    
    # Create platform summary
    summary_df = extractor.create_platform_summary(structured_df)
    
    # Save results
    extractor.save_extracted_data(structured_df, summary_df)
    
    print(f"\n🎯 EXTRACTION COMPLETE!")
    print(f"   • Raw campaigns: {len(raw_df)}")
    print(f"   • Parsed successfully: {len(structured_df)}")
    print(f"   • Role-platform combinations: {len(summary_df)}")
    print(f"   • Files saved with real performance data!")

if __name__ == "__main__":
    main()
