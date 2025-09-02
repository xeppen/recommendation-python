#!/usr/bin/env python3
"""
Budget recommendation module for recruitment campaigns.
Analyzes historical data to suggest optimal budget ranges.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional

class BudgetRecommender:
    def __init__(self, campaign_data_path: str = 'data/processed/all_platforms_campaigns_complete.csv'):
        """Initialize budget recommender with campaign data."""
        self.df = pd.read_csv(campaign_data_path)
        self._prepare_data()
        self._calculate_success_metrics()
        self._calculate_budget_tiers()
        
    def _prepare_data(self):
        """Prepare and clean campaign data."""
        # Calculate CTR and CPC
        self.df['CTR'] = (self.df['total_clicks'] / self.df['total_impressions'] * 100).fillna(0)
        self.df['CPC'] = (self.df['total_spend'] / self.df['total_clicks']).fillna(0)
        
        # Extract role and industry
        self.df['Role'] = self.df['campaign_name'].apply(self._extract_role)
        self.df['Industry'] = self.df.apply(
            lambda row: self._extract_industry(row.get('company'), row.get('campaign_name')), 
            axis=1
        )
        
        # Create role-industry combination
        self.df['Role_Industry'] = self.df['Role'] + ' - ' + self.df['Industry']
        
        # Filter out outliers and low-quality campaigns
        self.df_clean = self.df[
            (self.df['total_spend'] > 100) & 
            (self.df['total_spend'] < 100000) & 
            (self.df['CTR'] > 0.5) &
            (self.df['total_clicks'] > 10)
        ].copy()
        
    def _extract_role(self, campaign_name: str) -> str:
        """Extract role from campaign name."""
        if pd.isna(campaign_name):
            return 'Övrig roll'
        
        name_lower = str(campaign_name).lower()
        
        # Role mapping
        role_patterns = {
            'Sjuksköterska': ['sjuksköterska', 'sjukskötare'],
            'Butikschef': ['butikschef'],
            'Butikssäljare': ['butikssälj'],
            'Säljare': ['säljare', 'sälj'],
            'Utvecklare': ['utvecklare', 'developer', 'programmerare'],
            'Chef': ['chef', 'ledare', 'manager'],
            'Tekniker': ['tekniker'],
            'Ingenjör': ['ingenjör', 'engineer'],
            'Projektledare': ['projektledare', 'project'],
            'Lagerarbetare': ['lagerarbetare', 'lager'],
            'Chaufför': ['chaufför', 'förare', 'driver'],
            'Elektriker': ['elektriker'],
            'Mekaniker': ['mekaniker'],
            'Konsult': ['konsult'],
        }
        
        for role, patterns in role_patterns.items():
            if any(pattern in name_lower for pattern in patterns):
                return role
        
        return 'Övrig roll'
    
    def _extract_industry(self, company: str, campaign_name: str) -> str:
        """Extract industry from company and campaign name."""
        if pd.isna(company) and pd.isna(campaign_name):
            return 'Övrig bransch'
        
        combined = f"{str(company).lower()} {str(campaign_name).lower()}"
        
        # Industry patterns (simplified)
        if any(x in combined for x in ['ica', 'coop', 'willys', 'lidl']):
            return 'Dagligvaror'
        elif any(x in combined for x in ['lindex', 'kappahl', 'h&m']):
            return 'Mode & Kläder'
        elif any(x in combined for x in ['sjukhus', 'vårdcentral', 'karolinska']):
            return 'Sjukvård'
        elif any(x in combined for x in ['microsoft', 'google', 'spotify', 'klarna', 'tech']):
            return 'IT & Tech'
        elif any(x in combined for x in ['rusta', 'jula', 'byggmax']):
            return 'Bygg & Hem'
        elif any(x in combined for x in ['volvo', 'scania', 'ford']):
            return 'Fordonsindustri'
        elif 'we select' in str(company).lower():
            return 'Diverse branscher'
        else:
            return 'Övrig bransch'
    
    def _calculate_success_metrics(self):
        """Calculate what constitutes a successful campaign."""
        # Define success as top 25% CTR per platform
        self.success_thresholds = {}
        for platform in self.df_clean['platform'].unique():
            platform_data = self.df_clean[self.df_clean['platform'] == platform]
            if len(platform_data) >= 10:
                self.success_thresholds[platform] = {
                    'ctr_threshold': platform_data['CTR'].quantile(0.75),
                    'median_budget': platform_data['total_spend'].median()
                }
        
        # Mark successful campaigns
        self.df_clean['successful'] = self.df_clean.apply(
            lambda row: row['CTR'] >= self.success_thresholds.get(
                row['platform'], {'ctr_threshold': 3.0}
            ).get('ctr_threshold', 3.0),
            axis=1
        )
        
        self.successful_campaigns = self.df_clean[self.df_clean['successful']].copy()
        
    def _calculate_budget_tiers(self):
        """Calculate budget tiers based on successful campaigns."""
        if len(self.successful_campaigns) > 0:
            budget_stats = self.successful_campaigns['total_spend'].describe(
                percentiles=[0.25, 0.5, 0.75, 0.90]
            )
            
            self.budget_tiers = {
                'minimum': {
                    'amount': budget_stats['25%'],
                    'description': 'Grundläggande synlighet',
                    'expected_performance': 'Basnivå för att nå ut'
                },
                'standard': {
                    'amount_min': budget_stats['50%'],
                    'amount_max': budget_stats['75%'],
                    'description': 'Rekommenderad nivå',
                    'expected_performance': 'God räckvidd och engagemang'
                },
                'premium': {
                    'amount_min': budget_stats['75%'],
                    'amount_max': budget_stats['90%'],
                    'description': 'Optimalt för bästa resultat',
                    'expected_performance': 'Maximal synlighet och konvertering'
                }
            }
        else:
            # Fallback values if no successful campaigns
            self.budget_tiers = {
                'minimum': {'amount': 1000, 'description': 'Grundläggande'},
                'standard': {'amount_min': 1500, 'amount_max': 2500, 'description': 'Standard'},
                'premium': {'amount_min': 2500, 'amount_max': 5000, 'description': 'Premium'}
            }
    
    def get_budget_recommendation(self, role: str, industry: Optional[str] = None, 
                                 campaign_days: int = 30) -> Dict:
        """Get budget recommendation for a specific role and industry."""
        
        recommendations = {
            'role': role,
            'industry': industry or 'Alla branscher',
            'campaign_days': campaign_days,
            'budget_tiers': {},
            'historical_data': {},
            'confidence': 'Låg',
            'data_points': 0
        }
        
        # Try to find exact role-industry match
        if industry:
            role_industry = f"{role} - {industry}"
            matching_campaigns = self.successful_campaigns[
                self.successful_campaigns['Role_Industry'] == role_industry
            ]
        else:
            matching_campaigns = self.successful_campaigns[
                self.successful_campaigns['Role'] == role
            ]
        
        # If no exact match, try similar roles
        if len(matching_campaigns) == 0:
            matching_campaigns = self.successful_campaigns[
                self.successful_campaigns['Role'].str.contains(role.split()[0], case=False, na=False)
            ]
        
        if len(matching_campaigns) > 0:
            recommendations['data_points'] = len(matching_campaigns)
            
            # Calculate budget statistics
            budget_stats = matching_campaigns['total_spend'].describe(
                percentiles=[0.25, 0.5, 0.75, 0.90]
            )
            
            # Daily budget calculations
            daily_min = budget_stats['25%'] / 30
            daily_standard = budget_stats['50%'] / 30
            daily_premium = budget_stats['75%'] / 30
            
            # Adjust for campaign length
            recommendations['budget_tiers'] = {
                'minimum': {
                    'total': round(daily_min * campaign_days, -1),  # Round to nearest 10
                    'daily': round(daily_min, 0),
                    'description': '🥉 Grundläggande synlighet',
                    'expected_clicks': self._estimate_clicks(daily_min * campaign_days, matching_campaigns),
                    'confidence': '60-70%'
                },
                'standard': {
                    'total': round(daily_standard * campaign_days, -1),
                    'daily': round(daily_standard, 0),
                    'description': '🥈 Rekommenderad nivå',
                    'expected_clicks': self._estimate_clicks(daily_standard * campaign_days, matching_campaigns),
                    'confidence': '70-85%'
                },
                'premium': {
                    'total': round(daily_premium * campaign_days, -1),
                    'daily': round(daily_premium, 0),
                    'description': '🥇 Optimalt resultat',
                    'expected_clicks': self._estimate_clicks(daily_premium * campaign_days, matching_campaigns),
                    'confidence': '85-95%'
                }
            }
            
            # Historical performance data
            recommendations['historical_data'] = {
                'avg_ctr': round(matching_campaigns['CTR'].mean(), 2),
                'avg_cpc': round(matching_campaigns['CPC'].mean(), 2),
                'median_budget': round(budget_stats['50%'], 0),
                'success_rate': round(len(matching_campaigns) / len(self.df_clean[
                    (self.df_clean['Role'] == role) if not industry else 
                    (self.df_clean['Role_Industry'] == role_industry)
                ]) * 100, 1) if len(matching_campaigns) > 0 else 0
            }
            
            # Set confidence based on data points
            if recommendations['data_points'] >= 50:
                recommendations['confidence'] = 'Hög'
            elif recommendations['data_points'] >= 20:
                recommendations['confidence'] = 'Medel'
            else:
                recommendations['confidence'] = 'Låg'
        
        else:
            # Use overall budget tiers as fallback
            recommendations['budget_tiers'] = {
                'minimum': {
                    'total': round(self.budget_tiers['minimum']['amount'] / 30 * campaign_days, -1),
                    'daily': round(self.budget_tiers['minimum']['amount'] / 30, 0),
                    'description': '🥉 Grundläggande synlighet'
                },
                'standard': {
                    'total': round(self.budget_tiers['standard']['amount_min'] / 30 * campaign_days, -1),
                    'daily': round(self.budget_tiers['standard']['amount_min'] / 30, 0),
                    'description': '🥈 Rekommenderad nivå'
                },
                'premium': {
                    'total': round(self.budget_tiers['premium']['amount_min'] / 30 * campaign_days, -1),
                    'daily': round(self.budget_tiers['premium']['amount_min'] / 30, 0),
                    'description': '🥇 Optimalt resultat'
                }
            }
            recommendations['confidence'] = 'Låg'
            recommendations['note'] = 'Baserat på generell data, ingen specifik data för denna roll/bransch'
        
        return recommendations
    
    def _estimate_clicks(self, budget: float, historical_data: pd.DataFrame) -> int:
        """Estimate expected clicks based on budget and historical CPC."""
        if len(historical_data) > 0:
            avg_cpc = historical_data['CPC'].mean()
            if avg_cpc > 0:
                return int(budget / avg_cpc)
        return 0
    
    def get_role_comparison(self, roles: list) -> pd.DataFrame:
        """Compare budget requirements for multiple roles."""
        comparison_data = []
        
        for role in roles:
            rec = self.get_budget_recommendation(role)
            if rec['budget_tiers']:
                comparison_data.append({
                    'Roll': role,
                    'Minimum Budget': rec['budget_tiers']['minimum']['total'],
                    'Standard Budget': rec['budget_tiers']['standard']['total'],
                    'Premium Budget': rec['budget_tiers']['premium']['total'],
                    'Datapunkter': rec['data_points'],
                    'Konfidens': rec['confidence']
                })
        
        return pd.DataFrame(comparison_data)


# Example usage
if __name__ == "__main__":
    print("🎯 Initierar budgetrekommendationsmotor...")
    recommender = BudgetRecommender()
    
    print(f"\n📊 Analyserat {len(recommender.df_clean)} kampanjer")
    print(f"✅ {len(recommender.successful_campaigns)} framgångsrika kampanjer identifierade")
    
    # Test recommendations
    print("\n" + "=" * 60)
    print("BUDGETREKOMMENDATIONER")
    print("=" * 60)
    
    test_roles = [
        ('Sjuksköterska', 'Sjukvård'),
        ('Butikschef', 'Dagligvaror'),
        ('Utvecklare', 'IT & Tech'),
        ('Säljare', None)
    ]
    
    for role, industry in test_roles:
        print(f"\n📋 {role}" + (f" - {industry}" if industry else ""))
        print("-" * 40)
        
        rec = recommender.get_budget_recommendation(role, industry, campaign_days=30)
        
        if rec['budget_tiers']:
            print(f"Datapunkter: {rec['data_points']} kampanjer")
            print(f"Konfidens: {rec['confidence']}")
            
            if rec['historical_data']:
                print(f"\nHistorisk prestanda:")
                print(f"  • Genomsnittlig CTR: {rec['historical_data']['avg_ctr']}%")
                print(f"  • Genomsnittlig CPC: {rec['historical_data']['avg_cpc']:.2f} SEK")
            
            print(f"\nRekommenderade budgetnivåer (30 dagar):")
            for tier_name, tier_data in rec['budget_tiers'].items():
                print(f"\n{tier_data['description']}:")
                print(f"  Total: {tier_data['total']:,.0f} SEK")
                print(f"  Daglig: {tier_data['daily']:,.0f} SEK")
                if 'expected_clicks' in tier_data and tier_data['expected_clicks'] > 0:
                    print(f"  Förväntade klick: ~{tier_data['expected_clicks']:,}")
                if 'confidence' in tier_data:
                    print(f"  Sannolikhet för framgång: {tier_data['confidence']}")
