"""
Extract job-specific campaigns (not employer branding) for role-platform analysis
"""

import pandas as pd
import re

class JobSpecificCampaignParser:
    """Parser focused on campaigns with specific job roles"""
    
    def __init__(self):
        # Common Swedish job titles to look for in campaign names
        self.job_titles = [
            'Trafikdrivare', 'Sjuksköterska', 'Läkare', 'Ingenjör', 'Ekonom',
            'IT-specialist', 'Systemutvecklare', 'Projektledare', 'HR-specialist',
            'Fastighetsmäklare', 'Butikssäljare', 'Rekryterare', 'Konsult',
            'Dataanalytiker', 'UX Designer', 'Grafisk formgivare', 'Marknadsförare',
            'Säljare', 'Kundtjänst', 'Administratör', 'Chef', 'VD', 'Utvecklare',
            'Tekniker', 'Specialist', 'Koordinator', 'Assistent', 'Manager'
        ]
        
        # Location mapping
        self.location_mapping = {
            'Stockholm': 'Stor stad',
            'Göteborg': 'Stor stad', 
            'Malmö': 'Stor stad',
            'Uppsala': 'Mellanstor stad',
            'Linköping': 'Mellanstor stad',
            'Jönköping': 'Mellanstor stad',
            'Sverige': 'Multiple Cities',
            'Sweden': 'Multiple Cities',
            'Flera platser': 'Multiple Cities',
            'Multiple Cities': 'Multiple Cities',
            'Norway': 'International',
            'Germany': 'International',
            'USA': 'International'
        }
    
    def extract_job_role(self, campaign_name: str) -> str:
        """Extract specific job role from campaign name"""
        
        # Look for known job titles
        for job_title in self.job_titles:
            if job_title.lower() in campaign_name.lower():
                return job_title
        
        # Try to extract from common patterns
        patterns = [
            r'- ([A-ZÅÄÖ][a-zåäöé]+(?:\s+[a-zåäöé]+)*) -',  # Between dashes
            r'^[^-]+ - ([A-ZÅÄÖ][a-zåäöé]+(?:\s+[a-zåäöé]+)*)',  # After first dash
            r'till ([A-ZÅÄÖ][a-zåäöé]+(?:\s+[a-zåäöé]+)*)',  # After "till"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, campaign_name)
            if match:
                potential_role = match.group(1).strip()
                # Check if it looks like a job title (not a company name)
                if len(potential_role.split()) <= 3 and not any(char.isdigit() for char in potential_role):
                    return potential_role
        
        return None
    
    def extract_location(self, campaign_name: str) -> tuple:
        """Extract location and map to city size"""
        
        for location, size in self.location_mapping.items():
            if location in campaign_name:
                return location, size
        
        return None, 'Unknown'
    
    def is_job_specific_campaign(self, campaign_name: str) -> bool:
        """Check if campaign is for a specific job role (not employer branding)"""
        
        # Skip employer branding campaigns
        if 'Employer Branding' in campaign_name:
            return False
        
        # Look for job-specific indicators
        job_indicators = [
            'Trafikdrivare', 'Lediga Jobb', 'Tjänster', 'Position ID',
            'Grafisk formgivare', 'Vice VD', 'Chef', 'Manager'
        ]
        
        return any(indicator in campaign_name for indicator in job_indicators)

def process_job_specific_campaigns(csv_file: str) -> pd.DataFrame:
    """Process BigQuery export to extract job-specific campaign data"""
    
    print(f"🎯 Processing job-specific campaigns from: {csv_file}")
    
    # Load data
    df = pd.read_csv(csv_file)
    print(f"📊 Total campaigns: {len(df)}")
    
    # Initialize parser
    parser = JobSpecificCampaignParser()
    
    # Filter for job-specific campaigns
    job_campaigns = []
    
    for _, row in df.iterrows():
        campaign_name = row['campaign_name']
        
        # Check if job-specific
        if not parser.is_job_specific_campaign(campaign_name):
            continue
        
        # Extract job role
        job_role = parser.extract_job_role(campaign_name)
        if not job_role:
            continue
        
        # Extract location
        location, city_size = parser.extract_location(campaign_name)
        
        # Create structured record
        record = {
            # Core data (like training CSV)
            'Roll': job_role,
            'Storlek_pa_Stad': city_size,
            'Platform': row['platform'].capitalize(),
            
            # Performance metrics (the valuable part!)
            'Total_Impressions': int(row['total_impressions']),
            'Total_Clicks': int(row['total_clicks']),
            'Total_Spend_SEK': round(row['total_spend'], 2),
            'CTR_Percent': round(row['ctr_percent'], 3),
            'CPC_SEK': round(row['cpc_sek'], 2),
            'Campaign_Days': int(row['campaign_days']),
            'Daily_Spend_SEK': round(row['total_spend'] / row['campaign_days'], 2),
            
            # Platform booleans (like training CSV)
            'Meta': row['platform'] == 'facebook',
            'LinkedIn': row['platform'] == 'linkedin',
            'Snapchat': row['platform'] == 'snapchat', 
            'Reddit': row['platform'] == 'reddit',
            'TikTok': row['platform'] == 'tiktok',
            
            # Metadata
            'Company': campaign_name.split(' - ')[0].strip(),
            'Location': location,
            'Campaign_ID': row['campaign_id'],
            'Original_Campaign_Name': campaign_name
        }
        
        job_campaigns.append(record)
    
    result_df = pd.DataFrame(job_campaigns)
    print(f"✅ Extracted {len(result_df)} job-specific campaigns")
    
    return result_df

def create_role_platform_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    """Create recommendations by role showing best platforms and expected performance"""
    
    print("📊 Creating role-platform recommendations...")
    
    # Group by role and platform
    role_platform = df.groupby(['Roll', 'Platform']).agg({
        'Total_Impressions': 'sum',
        'Total_Clicks': 'sum', 
        'Total_Spend_SEK': 'sum',
        'CTR_Percent': 'mean',
        'CPC_SEK': 'mean',
        'Daily_Spend_SEK': 'mean',
        'Campaign_ID': 'count',
        'Storlek_pa_Stad': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'Unknown'
    }).reset_index()
    
    role_platform = role_platform.rename(columns={'Campaign_ID': 'Number_of_Campaigns'})
    
    # Calculate performance scores
    role_platform['Performance_Score'] = (
        role_platform['CTR_Percent'] * 0.6 +  # CTR weight
        (1 / role_platform['CPC_SEK']) * 100 * 0.4  # Inverse CPC weight (lower CPC = better)
    )
    
    role_platform = role_platform.sort_values(['Roll', 'Performance_Score'], ascending=[True, False])
    
    return role_platform

def main():
    """Extract and analyze job-specific campaigns"""
    
    print("🎯 Job-Specific Campaign Analysis")
    print("=" * 40)
    
    # Process job-specific campaigns
    df = process_job_specific_campaigns('bquxjob_1b660101_1990936b855.csv')
    
    if len(df) == 0:
        print("❌ No job-specific campaigns found in this dataset")
        print("💡 This export contains mostly employer branding campaigns")
        print("🔍 Try querying for campaigns with specific job titles in BigQuery")
        return
    
    # Create role-platform recommendations
    recommendations = create_role_platform_recommendations(df)
    
    # Save results
    df.to_csv('job_specific_campaigns.csv', index=False)
    recommendations.to_csv('role_platform_recommendations.csv', index=False)
    
    print(f"\n💾 Files saved:")
    print(f"   • job_specific_campaigns.csv - Detailed job campaign data")
    print(f"   • role_platform_recommendations.csv - Role-platform performance")
    
    # Show results
    print(f"\n🎯 JOB ROLE CAMPAIGN ANALYSIS:")
    print(f"   • Total job-specific campaigns: {len(df)}")
    print(f"   • Unique job roles: {df['Roll'].nunique()}")
    print(f"   • Platforms used: {', '.join(df['Platform'].unique())}")
    
    print(f"\n🏆 ROLE-PLATFORM RECOMMENDATIONS:")
    for _, row in recommendations.head(10).iterrows():
        print(f"   👔 {row['Roll']} on {row['Platform'].upper()}")
        print(f"      💰 {row['Total_Spend_SEK']:,.0f} SEK | 🎯 {row['CTR_Percent']:.2f}% CTR | 💳 {row['CPC_SEK']:.2f} SEK CPC")

if __name__ == "__main__":
    main()
