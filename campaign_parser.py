"""
Campaign Name Parser for WeSelect BigQuery Data

Parses structured campaign names to extract:
- Company name
- Job role/title  
- Location
- Package type
- Additional metadata
"""

import re
import pandas as pd
from typing import Dict, Optional, List
from google.cloud import bigquery

class CampaignNameParser:
    """Parser for WeSelect campaign naming structure"""
    
    def __init__(self):
        # Common Swedish job title patterns
        self.job_patterns = [
            r'till\s+([^-]+)',  # "Grafisk formgivare till LRF Media"
            r'som\s+([^-]+)',   # "Arbetsterapeut som specialist"
            r'^([^-]+)\s*-',    # Direct role at start
        ]
        
        # Location patterns (Swedish cities and regions)
        self.location_patterns = [
            r'\b(Stockholm|Göteborg|Malmö|Uppsala|Linköping|Örebro|Västerås|Norrköping|Helsingborg|Jönköping|Umeå|Lund|Borås|Sundsvall|Gävle|Eskilstuna|Karlstad|Växjö|Halmstad|Trollhättan|Östersund)\b',
            r'\b(Multiple\s+Cities|Multiple\s+cities|Flera\s+städer)\b',
            r'\b(Norge|Norway|Danmark|Denmark)\b',
        ]
        
        # Package type patterns
        self.package_patterns = [
            r'(Boost\s+Plus:?\s*[^-]*)',
            r'(Boost\s+Auto[^-]*)',
            r'(LinkedIn\s+Boost[^-]*)', 
            r'(Boost[^-]*)',
        ]

    def parse_campaign_name(self, campaign_name: str) -> Dict[str, Optional[str]]:
        """
        Parse a single campaign name into components
        
        Args:
            campaign_name: Full campaign name string
            
        Returns:
            Dictionary with parsed components
        """
        if not campaign_name:
            return self._empty_result()
            
        parts = campaign_name.split(' - ')
        
        result = {
            'original_name': campaign_name,
            'company': None,
            'job_role': None,
            'location': None,
            'package_type': None,
            'additional_info': None,
            'confidence_score': 0.0
        }
        
        try:
            # Extract company (usually first part)
            if len(parts) >= 1:
                result['company'] = parts[0].strip()
                
            # Extract job role (usually second part, may need cleaning)
            if len(parts) >= 2:
                job_part = parts[1].strip()
                result['job_role'] = self._extract_job_role(job_part)
                
            # Extract location (scan all parts)
            result['location'] = self._extract_location(campaign_name)
            
            # Extract package type (scan all parts)
            result['package_type'] = self._extract_package_type(campaign_name)
            
            # Calculate confidence score
            result['confidence_score'] = self._calculate_confidence(result)
            
        except Exception as e:
            print(f"Error parsing campaign: {campaign_name[:50]}... - {str(e)}")
            
        return result
    
    def _extract_job_role(self, job_part: str) -> Optional[str]:
        """Extract clean job role from job part"""
        # Remove common prefixes/suffixes
        job_part = re.sub(r'\s+till\s+.*$', '', job_part, flags=re.IGNORECASE)
        job_part = re.sub(r'\s+som\s+.*$', '', job_part, flags=re.IGNORECASE)
        job_part = re.sub(r'\s+på\s+.*$', '', job_part, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        job_part = re.sub(r'\s+', ' ', job_part).strip()
        
        return job_part if job_part else None
    
    def _extract_location(self, campaign_name: str) -> Optional[str]:
        """Extract location from campaign name"""
        for pattern in self.location_patterns:
            match = re.search(pattern, campaign_name, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_package_type(self, campaign_name: str) -> Optional[str]:
        """Extract package type from campaign name"""
        for pattern in self.package_patterns:
            match = re.search(pattern, campaign_name, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _calculate_confidence(self, result: Dict) -> float:
        """Calculate parsing confidence score (0-1)"""
        score = 0.0
        if result['company']: score += 0.2
        if result['job_role']: score += 0.4
        if result['location']: score += 0.3
        if result['package_type']: score += 0.1
        return score
    
    def _empty_result(self) -> Dict[str, Optional[str]]:
        """Return empty parsing result"""
        return {
            'original_name': '',
            'company': None,
            'job_role': None,
            'location': None,
            'package_type': None,
            'additional_info': None,
            'confidence_score': 0.0
        }

class BigQueryCampaignAnalyzer:
    """Analyzer for campaign performance by role and location"""
    
    def __init__(self, project_id: str = "we-select-data-prod"):
        self.client = bigquery.Client(project=project_id)
        self.parser = CampaignNameParser()
    
    def get_campaign_performance_data(self, date_from: str = "2024-01-01") -> pd.DataFrame:
        """
        Get campaign performance data with parsed names
        
        Args:
            date_from: Start date for analysis (YYYY-MM-DD)
            
        Returns:
            DataFrame with campaign performance and parsed components
        """
        query = f"""
        SELECT 
            d.campaign_id,
            d.campaign as campaign_name,
            d.data_source as platform,
            f.date,
            SUM(f.impressions) as total_impressions,
            SUM(f.clicks) as total_clicks,
            SUM(f.spend) as total_spend,
            SAFE_DIVIDE(SUM(f.clicks), SUM(f.impressions)) as ctr,
            SAFE_DIVIDE(SUM(f.spend), SUM(f.clicks)) as cpc
        FROM `{self.client.project}.campaign_analysis_dim.dim_all_campaigns` d
        JOIN `{self.client.project}.campaign_analysis_fact.fact_all_campaigns` f
        ON d.campaign_id = f.campaign_id
        WHERE f.date >= '{date_from}'
        AND f.impressions > 0
        GROUP BY d.campaign_id, d.campaign, d.data_source, f.date
        ORDER BY f.date DESC
        """
        
        df = self.client.query(query).to_dataframe()
        
        # Parse campaign names
        parsed_data = []
        for _, row in df.iterrows():
            parsed = self.parser.parse_campaign_name(row['campaign_name'])
            parsed_data.append({
                **row.to_dict(),
                **parsed
            })
        
        return pd.DataFrame(parsed_data)
    
    def analyze_role_platform_performance(self, df: pd.DataFrame, min_confidence: float = 0.6) -> pd.DataFrame:
        """
        Analyze performance by job role and platform
        
        Args:
            df: Campaign performance DataFrame
            min_confidence: Minimum parsing confidence score
            
        Returns:
            Performance summary by role and platform
        """
        # Filter by confidence score
        df_filtered = df[df['confidence_score'] >= min_confidence].copy()
        
        # Group by role and platform
        summary = df_filtered.groupby(['job_role', 'platform']).agg({
            'total_impressions': 'sum',
            'total_clicks': 'sum', 
            'total_spend': 'sum',
            'campaign_id': 'count'  # Number of campaigns
        }).reset_index()
        
        # Calculate performance metrics
        summary['avg_ctr'] = summary['total_clicks'] / summary['total_impressions']
        summary['avg_cpc'] = summary['total_spend'] / summary['total_clicks']
        summary['campaigns_count'] = summary['campaign_id']
        
        # Sort by performance
        summary = summary.sort_values(['job_role', 'avg_ctr'], ascending=[True, False])
        
        return summary[['job_role', 'platform', 'campaigns_count', 'total_impressions', 
                       'total_clicks', 'total_spend', 'avg_ctr', 'avg_cpc']]

def main():
    """Example usage"""
    # Initialize analyzer
    analyzer = BigQueryCampaignAnalyzer()
    
    # Get campaign data (last 6 months)
    print("Fetching campaign performance data...")
    df = analyzer.get_campaign_performance_data("2024-03-01")
    
    print(f"Loaded {len(df)} campaign records")
    print(f"Average parsing confidence: {df['confidence_score'].mean():.2f}")
    
    # Analyze role-platform performance
    print("\nAnalyzing role-platform performance...")
    role_performance = analyzer.analyze_role_platform_performance(df)
    
    print("\nTop performing role-platform combinations:")
    print(role_performance.head(20).to_string(index=False))
    
    # Save results
    role_performance.to_csv('role_platform_performance.csv', index=False)
    print("\nResults saved to role_platform_performance.csv")

if __name__ == "__main__":
    main()
