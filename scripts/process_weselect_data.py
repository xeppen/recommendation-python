"""
Process WeSelect BigQuery campaign data into training format

Specialized parser for WeSelect employer branding campaign structure:
Company - Employer Branding - Step - Phase - CI: Industry - TA: Target Audience - Country - Location - Manager
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
            'Real Estate': 'Fastighetsmäklare',
            'Economy & Finance': 'Ekonom',
            'Marketing': 'Digital marknadsförare',
            'Multiple Target Audiences': 'Allmän rekrytering',
            'Sales': 'Försäljningsrepresentant',
            'Safety & Security': 'Säkerhetsvakt',
            'Automotive': 'Mekaniker'
        }
        
        # Map locations to city sizes
        self.location_to_size = {
            'Stockholm': 'Stor stad',
            'Gothenburg': 'Mellanstor stad', 
            'Multiple Cities': 'Multiple Cities',
            'Multiple cities': 'Multiple Cities',
            'Jönköping': 'Mellanstor stad',
            'City': 'Mellanstor stad',
            'Region Öst': 'Multiple Cities'
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
            'manager': None,
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
            
            # Extract manager (usually last part)
            if len(parts) >= 1:
                last_part = parts[-1].strip()
                if last_part in ['EDVIN', 'Edvin', 'AGNES', 'Agnes', 'MOA', 'Moa', 'SIMON', 'Simon']:
                    result['manager'] = last_part
            
            # Calculate confidence
            confidence = 0.0
            if result['company']: confidence += 0.2
            if result['job_role']: confidence += 0.4
            if result['location']: confidence += 0.2
            if result['industry']: confidence += 0.2
            result['confidence'] = confidence
            
        except Exception as e:
            print(f'Error parsing: {campaign_name[:50]}... - {e}')
        
        return result

# Test the parser
parser = WeSelectCampaignParser()
test_campaign = df.iloc[0]['campaign_name']
print(f'\n🎯 Testing parser on: {test_campaign}')
result = parser.parse_campaign(test_campaign)
for key, value in result.items():
    print(f'{key}: {value}')
"
