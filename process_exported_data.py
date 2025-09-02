"""
Process manually exported BigQuery data into training format

If BigQuery authentication is difficult, you can:
1. Run the SQL queries in BigQuery Console
2. Export results to CSV
3. Use this script to process the exported data
"""

import pandas as pd
import re
from campaign_parser import CampaignNameParser

def process_exported_bigquery_data(csv_file_path: str) -> pd.DataFrame:
    """
    Process exported BigQuery CSV into training data format
    
    Args:
        csv_file_path: Path to exported BigQuery CSV file
        
    Returns:
        Processed DataFrame ready for training
    """
    
    print(f"📂 Loading exported data from: {csv_file_path}")
    
    # Load the exported CSV
    df = pd.read_csv(csv_file_path)
    print(f"✅ Loaded {len(df)} records")
    
    # Initialize parser
    parser = CampaignNameParser()
    
    # Process each campaign
    processed_data = []
    
    for _, row in df.iterrows():
        # Parse campaign name
        parsed = parser.parse_campaign_name(row['campaign_name'])
        
        # Skip low confidence parses
        if parsed['confidence_score'] < 0.6:
            continue
        
        # Map location to city size categories
        city_size = map_location_to_city_size(parsed['location'])
        
        # Map package to standard types
        package_mapped = map_package_type(parsed['package_type'])
        
        # Create training record
        record = {
            'Roll': parsed['job_role'],
            'Category': 'From BigQuery',  # Could be enhanced with AI categorization
            'Storlek_pa_Stad': city_size,
            'Senioritet': 'Unknown',  # Not available in campaign names
            'Platform': row['platform'],
            'Package': package_mapped,
            
            # Performance data (the valuable addition!)
            'Total_Impressions': row.get('total_impressions', 0),
            'Total_Clicks': row.get('total_clicks', 0),
            'Total_Spend_SEK': row.get('total_spend', 0),
            'CTR_Percent': row.get('ctr_percent', 0),
            'CPC_SEK': row.get('cpc_sek', 0),
            'Campaign_Days': row.get('campaign_days', 0),
            
            # Metadata
            'Company': parsed['company'],
            'Location': parsed['location'],
            'Confidence': parsed['confidence_score'],
            'Original_Campaign': row['campaign_name']
        }
        
        processed_data.append(record)
    
    result_df = pd.DataFrame(processed_data)
    print(f"✅ Processed {len(result_df)} high-confidence records")
    
    return result_df

def map_location_to_city_size(location: str) -> str:
    """Map specific locations to city size categories"""
    if not location:
        return 'Unknown'
    
    location = location.lower()
    
    # Major cities
    if location in ['stockholm', 'göteborg', 'malmö']:
        return 'Stor stad'
    
    # Medium cities  
    elif location in ['uppsala', 'linköping', 'örebro', 'västerås', 'norrköping', 'helsingborg']:
        return 'Mellanstor stad'
    
    # Multiple cities or unknown
    elif 'multiple' in location or 'flera' in location:
        return 'Multiple Cities'
    
    # Default to small city
    else:
        return 'Liten stad'

def map_package_type(package_type: str) -> str:
    """Map package types to standard categories"""
    if not package_type:
        return 'Unknown'
    
    package_lower = package_type.lower()
    
    if 'boost plus' in package_lower:
        return 'Boost Video'  # Map to closest training category
    elif 'boost auto' in package_lower:
        return 'Boost Bild'   # Map to closest training category
    elif 'boost' in package_lower:
        return 'Boost Bild'   # Default boost mapping
    else:
        return 'Två-stegare'  # Default for complex packages

def create_performance_insights(df: pd.DataFrame):
    """Create quick performance insights from the processed data"""
    
    print("\n🎯 PERFORMANCE INSIGHTS:")
    print("=" * 50)
    
    # Top performing role-platform combinations
    top_performers = df.groupby(['Roll', 'Platform']).agg({
        'Total_Spend_SEK': 'sum',
        'CTR_Percent': 'mean',
        'CPC_SEK': 'mean'
    }).reset_index().sort_values('Total_Spend_SEK', ascending=False).head(10)
    
    print("\n🏆 TOP 10 ROLE-PLATFORM COMBINATIONS BY SPEND:")
    for _, row in top_performers.iterrows():
        print(f"   👔 {row['Roll']} on {row['Platform'].upper()}")
        print(f"      💰 {row['Total_Spend_SEK']:,.0f} SEK | 🎯 {row['CTR_Percent']:.2f}% CTR | 💳 {row['CPC_SEK']:.2f} SEK CPC")
    
    # Platform performance
    platform_perf = df.groupby('Platform').agg({
        'Total_Spend_SEK': 'sum',
        'CTR_Percent': 'mean',
        'CPC_SEK': 'mean',
        'Roll': 'count'
    }).reset_index().sort_values('Total_Spend_SEK', ascending=False)
    
    print(f"\n📱 PLATFORM PERFORMANCE:")
    for _, row in platform_perf.iterrows():
        print(f"   📊 {row['Platform'].upper()}: {row['Roll']} campaigns, {row['Total_Spend_SEK']:,.0f} SEK, {row['CTR_Percent']:.2f}% CTR")

if __name__ == "__main__":
    # Example usage - replace with your exported CSV file
    print("📝 To use this script:")
    print("1. Run the SQL queries in BigQuery Console")
    print("2. Export results to CSV")
    print("3. Run: python3 process_exported_data.py")
    print("4. Update the csv_file_path below")
    
    # Uncomment and update path when you have exported data
    # df = process_exported_bigquery_data("exported_campaigns.csv")
    # create_performance_insights(df)
