"""
Process exported BigQuery campaign data into enhanced training format
"""

import pandas as pd
import re

class WeSelectCampaignParser:
    """Parser for WeSelect employer branding campaign structure"""
    
    def __init__(self):
        # Map Target Audiences to job categories
        self.ta_to_role_mapping = {
            'Data & IT': 'IT-specialist',
            'Logistics & Transportation': 'Logistikkoordinator', 
            'Retail & Grocery Stores': 'Butikssäljare',
            'Construction, Civil Engineering & Infrastructure': 'Ingenjör',
            'Engineering': 'Ingenjör',
            'Manufacturing & Production': 'Produktionstekniker',
            'Installation, Operations & Maintenance': 'Underhållstekniker',
            'Head Office': 'Administrativ assistent',
            'Health Care': 'Sjuksköterska',
            'Healthcare': 'Sjuksköterska',
            'Real Estate': 'Fastighetsmäklare',
            'Economy & Finance': 'Ekonom',
            'Marketing': 'Digital marknadsförare',
            'Multiple Target Audiences': 'Allmän rekrytering',
            'Sales': 'Försäljningsrepresentant',
            'Safety & Security': 'Säkerhetsvakt',
            'Automotive': 'Mekaniker',
            'Public Administration': 'Offentlig förvaltare',
            'Technology & Electronics': 'IT-tekniker',
            'Telecommunication': 'IT-tekniker',
            'Consulting': 'Konsult'
        }
        
        # Map locations to city sizes
        self.location_to_size = {
            'Stockholm': 'Stor stad',
            'Gothenburg': 'Mellanstor stad', 
            'Multiple Cities': 'Multiple Cities',
            'Multiple cities': 'Multiple Cities',
            'Jönköping': 'Mellanstor stad',
            'City': 'Mellanstor stad',
            'Region Öst': 'Multiple Cities',
            'Norway': 'International',
            'Germany': 'International', 
            'Finland': 'International',
            'USA': 'International'
        }
    
    def parse_campaign(self, campaign_name: str) -> dict:
        """Parse WeSelect campaign name structure"""
        
        parts = campaign_name.split(' - ')
        
        result = {
            'company': None,
            'industry': None,
            'target_audience': None,
            'job_role': None,
            'country': None,
            'location': None,
            'city_size': None,
            'campaign_step': None,
            'confidence': 0.0
        }
        
        try:
            # Extract company (Part 1)
            if len(parts) >= 1:
                result['company'] = parts[0].strip()
            
            # Extract campaign step (Part 3)
            if len(parts) >= 3:
                result['campaign_step'] = parts[2].strip()
            
            # Extract industry (CI: part)
            for part in parts:
                if part.strip().startswith('CI:'):
                    result['industry'] = part.replace('CI:', '').strip()
                    break
            
            # Extract target audience (TA: part)  
            for part in parts:
                if part.strip().startswith('TA:'):
                    ta = part.replace('TA:', '').strip()
                    result['target_audience'] = ta
                    # Map to job role
                    result['job_role'] = self.ta_to_role_mapping.get(ta, ta)
                    break
            
            # Extract country and location
            for i, part in enumerate(parts):
                part = part.strip()
                if part in ['Sweden', 'Norway', 'Germany', 'Finland', 'USA']:
                    result['country'] = part
                    # Next part might be location
                    if i + 1 < len(parts):
                        location = parts[i + 1].strip()
                        if location not in ['EDVIN', 'Edvin', 'AGNES', 'Agnes', 'MOA', 'Moa', 'SIMON', 'Simon']:
                            result['location'] = location
                            result['city_size'] = self.location_to_size.get(location, 'Liten stad')
                    break
            
            # Calculate confidence
            confidence = 0.0
            if result['company']: confidence += 0.2
            if result['job_role'] and result['job_role'] != result['target_audience']: confidence += 0.4
            if result['location']: confidence += 0.2
            if result['industry']: confidence += 0.2
            result['confidence'] = confidence
            
        except Exception as e:
            print(f'Error parsing: {campaign_name[:50]}... - {e}')
        
        return result

def process_bigquery_export(csv_file: str) -> pd.DataFrame:
    """Process the exported BigQuery CSV into training data format"""
    
    print(f"📂 Processing BigQuery export: {csv_file}")
    
    # Load data
    df = pd.read_csv(csv_file)
    print(f"✅ Loaded {len(df)} campaign records")
    
    # Initialize parser
    parser = WeSelectCampaignParser()
    
    # Process each campaign
    enhanced_data = []
    
    for _, row in df.iterrows():
        parsed = parser.parse_campaign(row['campaign_name'])
        
        # Skip if no meaningful job role extracted
        if not parsed['job_role'] or parsed['confidence'] < 0.6:
            continue
        
        # Create enhanced record
        record = {
            # Training data structure
            'Roll': parsed['job_role'],
            'Category': parsed['industry'] or 'Unknown',
            'Storlek_pa_Stad': parsed['city_size'] or 'Unknown',
            'Senioritet': 'Unknown',  # Not available in campaign names
            'Platform': row['platform'].capitalize(),
            
            # Performance metrics (the valuable addition!)
            'Total_Impressions': int(row['total_impressions']),
            'Total_Clicks': int(row['total_clicks']),
            'Total_Spend_SEK': round(row['total_spend'], 2),
            'Campaign_Days': int(row['campaign_days']),
            'CTR_Percent': round(row['ctr_percent'], 3),
            'CPC_SEK': round(row['cpc_sek'], 2),
            'Daily_Spend_SEK': round(row['total_spend'] / row['campaign_days'], 2),
            
            # Metadata
            'Company': parsed['company'],
            'Industry': parsed['industry'],
            'Target_Audience': parsed['target_audience'],
            'Country': parsed['country'],
            'Location': parsed['location'],
            'Campaign_Step': parsed['campaign_step'],
            'Confidence': parsed['confidence'],
            'Campaign_ID': row['campaign_id'],
            'Original_Campaign_Name': row['campaign_name']
        }
        
        enhanced_data.append(record)
    
    result_df = pd.DataFrame(enhanced_data)
    print(f"✅ Successfully processed {len(result_df)} campaigns with confidence ≥ 0.6")
    
    return result_df

def create_role_platform_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create summary similar to training CSV structure but with real performance data"""
    
    print("📊 Creating role-platform performance summary...")
    
    # Group by role and platform
    summary = df.groupby(['Roll', 'Platform']).agg({
        'Total_Impressions': 'sum',
        'Total_Clicks': 'sum',
        'Total_Spend_SEK': 'sum',
        'Campaign_Days': 'sum',
        'CTR_Percent': 'mean',
        'CPC_SEK': 'mean',
        'Daily_Spend_SEK': 'mean',
        'Campaign_ID': 'count',  # Number of campaigns
        'Storlek_pa_Stad': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'Unknown',
        'Category': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'Unknown'
    }).reset_index()
    
    # Rename and calculate additional metrics
    summary = summary.rename(columns={'Campaign_ID': 'Number_of_Campaigns'})
    summary['Avg_CTR'] = round(summary['CTR_Percent'], 3)
    summary['Avg_CPC'] = round(summary['CPC_SEK'], 2)
    summary['Total_Budget_Used'] = round(summary['Total_Spend_SEK'], 2)
    
    # Create platform boolean columns (like training CSV)
    summary['Meta'] = summary['Platform'] == 'Facebook'
    summary['LinkedIn'] = summary['Platform'] == 'Linkedin' 
    summary['Snapchat'] = summary['Platform'] == 'Snapchat'
    summary['Reddit'] = summary['Platform'] == 'Reddit'
    summary['TikTok'] = summary['Platform'] == 'Tiktok'
    
    # Sort by performance
    summary = summary.sort_values(['Roll', 'Total_Spend_SEK'], ascending=[True, False])
    
    return summary

def main():
    """Process the exported BigQuery data"""
    
    print("🚀 Processing WeSelect BigQuery Campaign Data")
    print("=" * 50)
    
    # Process the exported file
    df = process_bigquery_export('bquxjob_1b660101_1990936b855.csv')
    
    # Create role-platform summary
    summary = create_role_platform_summary(df)
    
    # Save results
    df.to_csv('enhanced_training_detailed.csv', index=False)
    summary.to_csv('enhanced_training_summary.csv', index=False)
    
    print(f"\n💾 Files saved:")
    print(f"   • enhanced_training_detailed.csv - Full campaign data")
    print(f"   • enhanced_training_summary.csv - Role-platform summary")
    
    # Show top performers
    print(f"\n🏆 TOP 10 ROLE-PLATFORM COMBINATIONS BY SPEND:")
    top_10 = summary.nlargest(10, 'Total_Budget_Used')[['Roll', 'Platform', 'Number_of_Campaigns', 'Total_Budget_Used', 'Avg_CTR', 'Avg_CPC']]
    print(top_10.to_string(index=False))
    
    # Platform performance overview
    platform_summary = df.groupby('Platform').agg({
        'Total_Spend_SEK': 'sum',
        'CTR_Percent': 'mean',
        'CPC_SEK': 'mean',
        'Campaign_ID': 'count'
    }).reset_index().sort_values('Total_Spend_SEK', ascending=False)
    
    print(f"\n📱 PLATFORM PERFORMANCE OVERVIEW:")
    for _, row in platform_summary.iterrows():
        print(f"   {row['Platform'].upper()}: {row['Campaign_ID']} campaigns, {row['Total_Spend_SEK']:,.0f} SEK, {row['CTR_Percent']:.2f}% CTR")

if __name__ == "__main__":
    main()
