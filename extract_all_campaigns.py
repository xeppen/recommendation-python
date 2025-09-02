#!/usr/bin/env python3
"""
Extract ALL campaigns from BigQuery data with enhanced features for ML modeling.
This creates a comprehensive dataset for building the predictive recommendation system.
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime

def extract_campaign_type(campaign_name):
    """Categorize campaign based on name patterns."""
    name_lower = campaign_name.lower()
    
    if any(word in name_lower for word in ['awareness', 'brand', 'kännedom']):
        return 'Brand Awareness'
    elif any(word in name_lower for word in ['event', 'mässa', 'konferens']):
        return 'Event'
    elif any(word in name_lower for word in ['produkt', 'product', 'tjänst', 'service']):
        return 'Product/Service'
    elif any(word in name_lower for word in ['rekryter', 'tjänst', 'ledig', 'söker', 'chef', 
                                            'tekniker', 'säljare', 'sjuksköterska', 'ingenjör',
                                            'konsult', 'specialist', 'koordinator']):
        return 'Recruitment'
    else:
        return 'Other'

def extract_location(campaign_name):
    """Extract location from campaign name."""
    # Swedish cities
    cities = ['Stockholm', 'Göteborg', 'Malmö', 'Uppsala', 'Västerås', 'Örebro', 
              'Linköping', 'Helsingborg', 'Jönköping', 'Norrköping', 'Lund', 
              'Umeå', 'Gävle', 'Borås', 'Eskilstuna', 'Södertälje', 'Karlstad',
              'Täby', 'Sundsvall', 'Luleå', 'Kalmar', 'Solna', 'Kista', 'Huddinge',
              'Borlänge', 'Falun', 'Växjö', 'Kristianstad', 'Skövde', 'Trollhättan']
    
    for city in cities:
        if city in campaign_name:
            return city
    
    if 'Sverige' in campaign_name or 'Hela landet' in campaign_name:
        return 'National'
    
    return 'Unknown'

def extract_role(campaign_name):
    """Extract job role from recruitment campaigns."""
    # Common job roles in Swedish
    roles = {
        'Sjuksköterska': ['sjuksköterska', 'sjukskötare'],
        'Tekniker': ['tekniker', 'teknisk'],
        'Chef': ['chef', 'ledare', 'manager'],
        'Säljare': ['säljare', 'sälj', 'sales'],
        'Ingenjör': ['ingenjör', 'engineer'],
        'Konsult': ['konsult', 'consultant'],
        'Projektledare': ['projektledare', 'project'],
        'Specialist': ['specialist', 'expert'],
        'Controller': ['controller', 'ekonom'],
        'Mekaniker': ['mekaniker', 'mek'],
        'Servicetekniker': ['servicetekniker', 'service'],
        'HR-specialist': ['hr-specialist', 'hr specialist', 'personalspecialist'],
        'IT-specialist': ['it-specialist', 'it specialist', 'systemtekniker'],
        'Koordinator': ['koordinator', 'samordnare'],
        'Administratör': ['administratör', 'admin'],
        'VD': ['vd', 'ceo', 'verkställande'],
        'Lagerarbetare': ['lagerarbetare', 'lager'],
        'Butikschef': ['butikschef', 'butiks'],
        'Förare': ['förare', 'chaufför', 'driver']
    }
    
    name_lower = campaign_name.lower()
    for role, keywords in roles.items():
        if any(keyword in name_lower for keyword in keywords):
            return role
    
    return None

def calculate_city_size(city):
    """Categorize city by size."""
    large_cities = ['Stockholm', 'Göteborg', 'Malmö']
    medium_cities = ['Uppsala', 'Linköping', 'Örebro', 'Västerås', 'Helsingborg', 
                     'Norrköping', 'Jönköping', 'Lund', 'Umeå', 'Borås']
    
    if city in large_cities:
        return 'Stor stad'
    elif city in medium_cities:
        return 'Mellanstor stad'
    elif city == 'National':
        return 'Nationell'
    elif city == 'Unknown':
        return 'Unknown'
    else:
        return 'Liten stad'

def extract_company(campaign_name):
    """Extract company name from campaign."""
    # Split by common delimiters
    parts = re.split(r' - | – ', campaign_name)
    if parts:
        return parts[0].strip()
    return 'Unknown'

def main():
    print("📊 Loading complete BigQuery dataset...")
    
    # Load the full dataset
    df = pd.read_csv('bquxjob_59210a96_19909765211.csv')
    
    print(f"✅ Loaded {len(df)} campaigns")
    
    # Extract enhanced features
    print("\n🔧 Extracting enhanced features...")
    
    df['Campaign_Type'] = df['campaign_name'].apply(extract_campaign_type)
    df['Location'] = df['campaign_name'].apply(extract_location)
    df['City_Size'] = df['Location'].apply(calculate_city_size)
    df['Role'] = df['campaign_name'].apply(extract_role)
    df['Company'] = df['campaign_name'].apply(extract_company)
    
    # Calculate additional metrics
    df['Daily_Spend'] = df['total_spend'] / df['campaign_days']
    df['Clicks_Per_Day'] = df['total_clicks'] / df['campaign_days']
    df['Cost_Efficiency'] = df['total_clicks'] / df['total_spend'] * 100  # Clicks per 100 SEK
    
    # Create platform flags for multi-channel analysis
    df['Is_Facebook'] = (df['platform'] == 'facebook').astype(int)
    df['Is_LinkedIn'] = (df['platform'] == 'linkedin').astype(int)
    df['Is_Snapchat'] = (df['platform'] == 'snapchat').astype(int)
    df['Is_TikTok'] = (df['platform'] == 'tiktok').astype(int)
    
    # Performance categorization
    df['CTR_Category'] = pd.cut(df['ctr_percent'], 
                                 bins=[0, 1, 2, 3, 5, 100],
                                 labels=['Very Low', 'Low', 'Medium', 'High', 'Very High'])
    
    df['CPC_Category'] = pd.cut(df['cpc_sek'],
                                 bins=[0, 2, 5, 10, 20, 1000],
                                 labels=['Very Low', 'Low', 'Medium', 'High', 'Very High'])
    
    # Reorder columns for better readability
    column_order = [
        'campaign_id', 'campaign_name', 'Campaign_Type', 'Company',
        'Role', 'Location', 'City_Size',
        'platform', 'Is_Facebook', 'Is_LinkedIn', 'Is_Snapchat', 'Is_TikTok',
        'total_impressions', 'total_clicks', 'total_spend', 'campaign_days',
        'ctr_percent', 'CTR_Category', 'cpc_sek', 'CPC_Category',
        'Daily_Spend', 'Clicks_Per_Day', 'Cost_Efficiency'
    ]
    
    df = df[column_order]
    
    # Save the complete enhanced dataset
    output_file = 'all_campaigns_enhanced.csv'
    df.to_csv(output_file, index=False)
    print(f"\n✅ Saved enhanced dataset to {output_file}")
    
    # Print summary statistics
    print("\n📈 DATASET SUMMARY:")
    print("=" * 50)
    print(f"Total campaigns: {len(df)}")
    print(f"Total spend: {df['total_spend'].sum():,.0f} SEK")
    print(f"Total clicks: {df['total_clicks'].sum():,}")
    
    print("\n📊 Campaign Types:")
    print(df['Campaign_Type'].value_counts())
    
    print("\n🌍 Platforms:")
    print(df['platform'].value_counts())
    
    print("\n🏢 Top 10 Companies by Campaign Count:")
    print(df['Company'].value_counts().head(10))
    
    if df['Role'].notna().any():
        print("\n👥 Top 10 Roles (Recruitment Campaigns):")
        print(df[df['Role'].notna()]['Role'].value_counts().head(10))
    
    print("\n📍 Top 10 Locations:")
    print(df['Location'].value_counts().head(10))
    
    print("\n🎯 Performance Metrics:")
    print(f"Average CTR: {df['ctr_percent'].mean():.2f}%")
    print(f"Average CPC: {df['cpc_sek'].mean():.2f} SEK")
    print(f"Best CTR: {df['ctr_percent'].max():.2f}% ({df.loc[df['ctr_percent'].idxmax(), 'campaign_name'][:50]}...)")
    print(f"Lowest CPC: {df['cpc_sek'].min():.2f} SEK ({df.loc[df['cpc_sek'].idxmin(), 'campaign_name'][:50]}...)")
    
    print("\n💡 Platform Performance Comparison:")
    platform_stats = df.groupby('platform').agg({
        'ctr_percent': 'mean',
        'cpc_sek': 'mean',
        'total_spend': 'mean',
        'campaign_id': 'count'
    }).round(2)
    platform_stats.columns = ['Avg CTR %', 'Avg CPC (SEK)', 'Avg Spend (SEK)', 'Count']
    print(platform_stats)
    
    # Create a subset for recruitment campaigns only
    recruitment_df = df[df['Campaign_Type'] == 'Recruitment'].copy()
    if len(recruitment_df) > 0:
        recruitment_df.to_csv('recruitment_campaigns_enhanced.csv', index=False)
        print(f"\n✅ Also saved {len(recruitment_df)} recruitment campaigns to recruitment_campaigns_enhanced.csv")
    
    print("\n🚀 Ready for ML model development!")
    print("Next steps:")
    print("1. Use 'all_campaigns_enhanced.csv' for comprehensive analysis")
    print("2. Use 'recruitment_campaigns_enhanced.csv' for job-specific recommendations")
    print("3. Build predictive models for channel optimization")

if __name__ == "__main__":
    main()
