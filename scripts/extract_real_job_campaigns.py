"""
Extract campaigns with actual job roles (not traffic campaigns or employer branding)
Keep each campaign separate to preserve unique role-platform-location performance data
"""

import pandas as pd
import re

class RealJobCampaignExtractor:
    """Extract campaigns with actual job titles, avoiding traffic/branding campaigns"""
    
    def __init__(self):
        # Blacklist - campaigns to ignore (not actual job roles)
        self.blacklist = [
            'Employer Branding',
            'Trafikdrivare',  # Traffic driving campaigns
            'Trafikdrivande', 
            'B2B Advertising',
            'Awareness',
            'Consideration', 
            'Decision',
            'Always-on',
            'Talent Pool',
            'E-books',
            'Webinars',
            'Templates'
        ]
        
        # Real job title patterns to look for
        self.job_title_patterns = [
            r'- ([A-ZÅÄÖ][a-zåäöé]+(?:\s+[a-zåäöé]+)*) till',  # "Role till Company"
            r'- ([A-ZÅÄÖ][a-zåäöé]+(?:\s+[a-zåäöé]+)*) -',     # "- Role -"
            r'till ([A-ZÅÄÖ][a-zåäöé]+(?:\s+[a-zåäöé]+)*)',    # "till Role"
            r'([A-ZÅÄÖ][a-zåäöé]+(?:\s+[a-zåäöé]+)*) till',    # "Role till"
        ]
        
        # Known Swedish job titles
        self.known_job_titles = [
            'Sjuksköterska', 'Läkare', 'Undersköterska', 'Arbetsterapeut', 'Fysioterapeut',
            'Ingenjör', 'Systemutvecklare', 'IT-specialist', 'Dataanalytiker', 'UX Designer',
            'Ekonom', 'Finansanalytiker', 'Redovisningsekonom', 'Controller',
            'Projektledare', 'HR-specialist', 'Rekryterare', 'Personalchef',
            'Fastighetsmäklare', 'Fastighetsutvecklare', 'Fastighetsförvaltare',
            'Butikschef', 'Säljare', 'Försäljningsrepresentant', 'Kundtjänst',
            'VD', 'Chef', 'Verksamhetschef', 'Avdelningschef', 'Enhetschef',
            'Grafisk formgivare', 'Webbdesigner', 'Marknadsförare', 'Kommunikatör',
            'Jurist', 'Advokat', 'Revisor', 'Konsult',
            'Lagerarbetare', 'Logistikkoordinator', 'Transportör',
            'Mekaniker', 'Tekniker', 'Underhållstekniker', 'Servicetekniker'
        ]
    
    def is_blacklisted_campaign(self, campaign_name: str) -> bool:
        """Check if campaign should be ignored"""
        return any(blacklisted in campaign_name for blacklisted in self.blacklist)
    
    def extract_job_title_from_campaign(self, campaign_name: str) -> str:
        """Extract actual job title from campaign name"""
        
        # Try known job title patterns
        for pattern in self.job_title_patterns:
            matches = re.findall(pattern, campaign_name, re.IGNORECASE)
            for match in matches:
                # Check if it's a known job title
                if match in self.known_job_titles:
                    return match
                
                # Check partial matches
                for job_title in self.known_job_titles:
                    if job_title.lower() in match.lower() or match.lower() in job_title.lower():
                        return job_title
        
        # Direct search for known job titles
        for job_title in self.known_job_titles:
            if job_title in campaign_name:
                return job_title
        
        return None
    
    def extract_location_info(self, campaign_name: str) -> tuple:
        """Extract location and city size"""
        
        # Location patterns
        locations = {
            'Stockholm': 'Stor stad',
            'Göteborg': 'Stor stad',
            'Malmö': 'Stor stad', 
            'Uppsala': 'Mellanstor stad',
            'Linköping': 'Mellanstor stad',
            'Jönköping': 'Mellanstor stad',
            'Örebro': 'Mellanstor stad',
            'Västerås': 'Mellanstor stad',
            'Norrköping': 'Mellanstor stad',
            'Helsingborg': 'Mellanstor stad',
            'Borås': 'Liten stad',
            'Sundsvall': 'Liten stad',
            'Gävle': 'Liten stad',
            'Multiple Cities': 'Multiple Cities',
            'Multiple cities': 'Multiple Cities',
            'Flera platser': 'Multiple Cities'
        }
        
        for location, size in locations.items():
            if location in campaign_name:
                return location, size
        
        return 'Unknown', 'Unknown'

def process_real_job_campaigns(csv_file: str) -> pd.DataFrame:
    """Process BigQuery export to find campaigns with real job titles"""
    
    print(f"🔍 Extracting real job campaigns from: {csv_file}")
    
    # Load data
    df = pd.read_csv(csv_file)
    print(f"📊 Total campaigns in export: {len(df)}")
    
    # Initialize extractor
    extractor = RealJobCampaignExtractor()
    
    # Process campaigns
    real_job_campaigns = []
    
    for _, row in df.iterrows():
        campaign_name = row['campaign_name']
        
        # Skip blacklisted campaigns
        if extractor.is_blacklisted_campaign(campaign_name):
            continue
        
        # Try to extract job title
        job_title = extractor.extract_job_title_from_campaign(campaign_name)
        if not job_title:
            continue
        
        # Extract location info
        location, city_size = extractor.extract_location_info(campaign_name)
        
        # Create individual campaign record (don't combine!)
        record = {
            # Core job data
            'Roll': job_title,
            'Storlek_pa_Stad': city_size,
            'Location': location,
            'Platform': row['platform'].capitalize(),
            
            # Performance data (unique per campaign)
            'Impressions': int(row['total_impressions']),
            'Clicks': int(row['total_clicks']),
            'Spend_SEK': round(row['total_spend'], 2),
            'CTR_Percent': round(row['ctr_percent'], 3),
            'CPC_SEK': round(row['cpc_sek'], 2),
            'Campaign_Days': int(row['campaign_days']),
            'Daily_Spend': round(row['total_spend'] / row['campaign_days'], 2),
            
            # Platform identification
            'Meta': row['platform'] == 'facebook',
            'LinkedIn': row['platform'] == 'linkedin',
            'Snapchat': row['platform'] == 'snapchat',
            'Reddit': row['platform'] == 'reddit', 
            'TikTok': row['platform'] == 'tiktok',
            
            # Campaign metadata
            'Company': campaign_name.split(' - ')[0].strip(),
            'Campaign_ID': row['campaign_id'],
            'Campaign_Name': campaign_name
        }
        
        real_job_campaigns.append(record)
    
    result_df = pd.DataFrame(real_job_campaigns)
    print(f"✅ Found {len(result_df)} campaigns with real job titles")
    
    # Show what was found
    if len(result_df) > 0:
        print(f"\n🎯 EXTRACTED JOB ROLES:")
        role_counts = result_df['Roll'].value_counts()
        for role, count in role_counts.items():
            platforms = result_df[result_df['Roll'] == role]['Platform'].unique()
            print(f"   👔 {role}: {count} campaigns on {', '.join(platforms)}")
    
    return result_df

def main():
    """Main extraction function"""
    
    print("🎯 Real Job Campaign Extraction")
    print("=" * 35)
    
    # Extract real job campaigns
    df = process_real_job_campaigns('bquxjob_59210a96_19909765211.csv')
    
    if len(df) == 0:
        print("\n❌ No campaigns with specific job titles found in this export")
        print("\n💡 RECOMMENDATION:")
        print("   This export contains mostly employer branding campaigns.")
        print("   You need to query BigQuery for campaigns that mention specific job titles.")
        print("\n🔍 Try searching for campaigns containing:")
        print("   • Specific job titles in campaign names")
        print("   • 'Position ID' campaigns")
        print("   • Direct job postings")
        return
    
    # Save results
    df.to_csv('real_job_campaigns.csv', index=False)
    print(f"\n💾 Saved to: real_job_campaigns.csv")
    
    # Show performance analysis
    print(f"\n📊 ROLE-PLATFORM PERFORMANCE ANALYSIS:")
    for role in df['Roll'].unique():
        role_data = df[df['Roll'] == role]
        print(f"\n👔 {role.upper()}:")
        
        for platform in role_data['Platform'].unique():
            platform_data = role_data[role_data['Platform'] == platform]
            total_spend = platform_data['Spend_SEK'].sum()
            avg_ctr = platform_data['CTR_Percent'].mean()
            avg_cpc = platform_data['CPC_SEK'].mean()
            
            print(f"   📱 {platform}: {total_spend:,.0f} SEK, {avg_ctr:.2f}% CTR, {avg_cpc:.2f} SEK CPC")

if __name__ == "__main__":
    main()
