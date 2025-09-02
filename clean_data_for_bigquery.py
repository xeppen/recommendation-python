#!/usr/bin/env python3
"""
Rensa och förbereda data för BigQuery upload
"""

import pandas as pd
import numpy as np

# Läs original data
df = pd.read_csv('data/processed/all_platforms_campaigns_complete.csv')
print(f"Original data: {len(df)} rader, {len(df.columns)} kolumner")

# Ta bara de kolumner vi behöver
required_columns = [
    'Roll', 'Storlek_pa_Stad', 'Location', 'Platform', 
    'Impressions', 'Clicks', 'Spend_SEK', 'CTR_Percent', 'CPC_SEK',
    'Campaign_Days', 'Daily_Spend', 
    'Meta', 'LinkedIn', 'Snapchat', 'Reddit', 'TikTok',
    'Company', 'Campaign_ID', 'Campaign_Name'
]

# Filtrera kolumner
df_clean = df[required_columns].copy()

# Rensa data
# Ta bort rader där Campaign_Name är NaN eller innehåller "Employer Branding"
df_clean = df_clean[df_clean['Campaign_Name'].notna()]
df_clean = df_clean[~df_clean['Campaign_Name'].str.contains('Employer Branding', case=False, na=False)]

# Konvertera datatypes
numeric_columns = ['Impressions', 'Clicks', 'Spend_SEK', 'CTR_Percent', 'CPC_SEK', 
                   'Campaign_Days', 'Daily_Spend']
for col in numeric_columns:
    df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

# Konvertera boolean columns
bool_columns = ['Meta', 'LinkedIn', 'Snapchat', 'Reddit', 'TikTok']
for col in bool_columns:
    df_clean[col] = df_clean[col].fillna(False).astype(bool)

# Fyll NaN värden
df_clean['Roll'] = df_clean['Roll'].fillna('Övrig roll')
df_clean['Storlek_pa_Stad'] = df_clean['Storlek_pa_Stad'].fillna('Unknown')
df_clean['Location'] = df_clean['Location'].fillna('Unknown')
df_clean['Company'] = df_clean['Company'].fillna('Unknown')

# Ta bort rader med kritiska NaN värden
df_clean = df_clean.dropna(subset=['Platform', 'Campaign_ID', 'Campaign_Name'])

print(f"Rensad data: {len(df_clean)} rader")
print(f"Kolumner: {df_clean.columns.tolist()}")

# Spara rensad data
df_clean.to_csv('data/processed/campaigns_clean_for_bigquery.csv', index=False)
print("✅ Sparad som: data/processed/campaigns_clean_for_bigquery.csv")
