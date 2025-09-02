#!/usr/bin/env python3
"""
Skapar demo-data för online deployment utan känslig information
"""

import pandas as pd
import numpy as np
from pathlib import Path

def create_demo_data():
    """Skapa anonymiserad demo-data för test"""
    
    # Skapa demo-roller
    roles = ['Utvecklare', 'Sjuksköterska', 'Säljare', 'Chef', 'Tekniker', 
             'Lärare', 'Ingenjör', 'Designer', 'Projektledare', 'Konsult']
    
    platforms = ['Facebook', 'LinkedIn', 'Snapchat', 'TikTok', 'Reddit']
    locations = ['Stockholm', 'Göteborg', 'Malmö', 'Uppsala', 'Linköping']
    companies = ['Företag A', 'Företag B', 'Företag C', 'Företag D', 'Företag E']
    
    # Generera demo-kampanjer
    demo_campaigns = []
    
    for i in range(100):  # 100 demo-kampanjer
        role = np.random.choice(roles)
        platform = np.random.choice(platforms)
        location = np.random.choice(locations)
        company = np.random.choice(companies)
        
        # Simulera realistisk data baserat på plattform
        if platform == 'LinkedIn':
            ctr = np.random.uniform(0.8, 2.5)
            cpc = np.random.uniform(25, 50)
        elif platform == 'Facebook':
            ctr = np.random.uniform(2.0, 4.0)
            cpc = np.random.uniform(15, 30)
        elif platform == 'Snapchat':
            ctr = np.random.uniform(1.5, 3.0)
            cpc = np.random.uniform(20, 35)
        else:
            ctr = np.random.uniform(1.0, 2.5)
            cpc = np.random.uniform(20, 40)
        
        impressions = np.random.randint(10000, 500000)
        clicks = int(impressions * ctr / 100)
        spend = clicks * cpc
        campaign_days = np.random.randint(7, 90)
        
        demo_campaigns.append({
            'Roll': role,
            'Storlek_pa_Stad': 'Stor stad' if location in ['Stockholm', 'Göteborg'] else 'Medelstor stad',
            'Location': location,
            'Platform': platform,
            'Impressions': impressions,
            'Clicks': clicks,
            'Spend_SEK': round(spend, 2),
            'CTR_Percent': round(ctr, 2),
            'CPC_SEK': round(cpc, 2),
            'Campaign_Days': campaign_days,
            'Daily_Spend': round(spend / campaign_days, 2),
            'Meta': platform == 'Facebook',
            'LinkedIn': platform == 'LinkedIn',
            'Snapchat': platform == 'Snapchat',
            'Reddit': platform == 'Reddit',
            'TikTok': platform == 'TikTok',
            'Company': company,
            'Campaign_ID': f'DEMO_{i:05d}',
            'Campaign_Name': f'{company} - {role} - {location} - Demo Campaign'
        })
    
    # Skapa DataFrame
    df = pd.DataFrame(demo_campaigns)
    
    # Spara demo-data
    demo_dir = Path('data/demo')
    demo_dir.mkdir(parents=True, exist_ok=True)
    
    df.to_csv('data/demo/demo_campaigns.csv', index=False)
    
    # Skapa demo träningsdata
    training_data = []
    for role in roles:
        for i in range(3):  # 3 paket per roll
            package_type = np.random.choice(['Grundläggande', 'Standard', 'Premium'])
            channels = np.random.choice(platforms, size=np.random.randint(1, 4), replace=False)
            
            training_data.append({
                'Roll': role,
                'Paket': package_type,
                'Kanaler': ', '.join(channels),
                'Budget': np.random.choice([5000, 10000, 15000, 20000, 30000])
            })
    
    training_df = pd.DataFrame(training_data)
    training_df.to_excel('data/demo/demo_training_data.xlsx', index=False)
    
    print("✅ Demo-data skapad!")
    print(f"  - Kampanjdata: data/demo/demo_campaigns.csv ({len(df)} rader)")
    print(f"  - Träningsdata: data/demo/demo_training_data.xlsx ({len(training_df)} rader)")
    print("\n⚠️  OBS: Detta är DEMO-data, inte riktig data!")
    
    return df, training_df

if __name__ == "__main__":
    create_demo_data()
