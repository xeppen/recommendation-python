#!/usr/bin/env python3
"""
Data-driven insights based on actual campaign performance
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
import streamlit as st

class DataDrivenInsights:
    """Generate insights based on actual historical data"""
    
    def __init__(self, campaigns_df: pd.DataFrame):
        """
        Initialize with campaign data
        
        Args:
            campaigns_df: DataFrame with all historical campaign data
        """
        self.campaigns_df = campaigns_df
        self._prepare_analytics()
    
    def _prepare_analytics(self):
        """Prepare analytical datasets"""
        # Beräkna aggregerad statistik per roll och plattform
        self.role_platform_stats = self.campaigns_df.groupby(['Roll', 'Platform']).agg({
            'CTR_Percent': ['mean', 'std', 'count'],
            'CPC_SEK': ['mean', 'std'],
            'Clicks': 'sum',
            'Spend_SEK': 'sum',
            'Campaign_Days': 'mean'
        }).round(2)
        
        # Beräkna tidsbaserade trender (om vi har datum)
        self.platform_performance = self.campaigns_df.groupby('Platform').agg({
            'CTR_Percent': 'mean',
            'CPC_SEK': 'mean',
            'Impressions': 'sum',
            'Clicks': 'sum'
        }).round(2)
        
        # Identifiera top performers
        self.top_combinations = self.campaigns_df.groupby(['Roll', 'Platform']).agg({
            'CTR_Percent': 'mean'
        }).sort_values('CTR_Percent', ascending=False).head(20)
    
    def get_role_insights(self, role: str) -> Dict[str, Any]:
        """
        Get data-driven insights for a specific role
        
        Returns insights based on ACTUAL performance data
        """
        # Filtrera data för denna roll
        role_data = self.campaigns_df[self.campaigns_df['Roll'] == role]
        
        if role_data.empty:
            # Om ingen exakt match, hitta liknande roller
            similar_roles = self._find_similar_roles(role)
            if similar_roles:
                role_data = self.campaigns_df[self.campaigns_df['Roll'].isin(similar_roles)]
        
        insights = {
            'total_campaigns': len(role_data),
            'platforms_used': role_data['Platform'].value_counts().to_dict(),
            'avg_performance': {
                'ctr': role_data['CTR_Percent'].mean(),
                'cpc': role_data['CPC_SEK'].mean(),
                'daily_spend': role_data['Daily_Spend'].mean()
            },
            'best_platform': self._get_best_platform(role_data),
            'trends': self._analyze_trends(role_data),
            'recommendations': self._generate_recommendations(role_data)
        }
        
        return insights
    
    def _get_best_platform(self, role_data: pd.DataFrame) -> Dict[str, Any]:
        """Identify best performing platform based on data"""
        if role_data.empty:
            return {}
        
        platform_stats = role_data.groupby('Platform').agg({
            'CTR_Percent': 'mean',
            'CPC_SEK': 'mean',
            'Campaign_ID': 'count'
        }).rename(columns={'Campaign_ID': 'campaign_count'})
        
        # Vikta prestanda: 60% CTR, 40% CPC (inverterad)
        platform_stats['score'] = (
            platform_stats['CTR_Percent'] * 0.6 + 
            (100 / platform_stats['CPC_SEK']) * 0.4
        )
        
        best = platform_stats.sort_values('score', ascending=False).iloc[0]
        best_platform = platform_stats.sort_values('score', ascending=False).index[0]
        
        return {
            'platform': best_platform,
            'ctr': best['CTR_Percent'],
            'cpc': best['CPC_SEK'],
            'campaigns': int(best['campaign_count']),
            'reason': self._explain_why_best(best_platform, platform_stats)
        }
    
    def _explain_why_best(self, platform: str, stats: pd.DataFrame) -> str:
        """Explain why a platform is best based on data"""
        platform_data = stats.loc[platform]
        all_platforms_avg_ctr = stats['CTR_Percent'].mean()
        all_platforms_avg_cpc = stats['CPC_SEK'].mean()
        
        reasons = []
        
        # CTR-analys
        if platform_data['CTR_Percent'] > all_platforms_avg_ctr * 1.2:
            improvement = ((platform_data['CTR_Percent'] / all_platforms_avg_ctr) - 1) * 100
            reasons.append(f"{improvement:.0f}% högre engagemang än genomsnittet")
        
        # CPC-analys
        if platform_data['CPC_SEK'] < all_platforms_avg_cpc * 0.8:
            savings = ((1 - platform_data['CPC_SEK'] / all_platforms_avg_cpc) * 100)
            reasons.append(f"{savings:.0f}% lägre kostnad per klick")
        
        # Volym-analys
        if platform_data['campaign_count'] >= 5:
            reasons.append(f"Väl testad med {int(platform_data['campaign_count'])} kampanjer")
        
        return " • ".join(reasons) if reasons else "Bäst overall prestanda"
    
    def _analyze_trends(self, role_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance trends in the data"""
        trends = {}
        
        # Plattformstrender
        platform_trend = role_data.groupby('Platform').agg({
            'CTR_Percent': ['mean', 'std'],
            'Campaign_ID': 'count'
        })
        
        # Hitta mest stabila plattformen (lägst standardavvikelse)
        if len(platform_trend) > 0:
            platform_trend.columns = ['_'.join(col).strip() for col in platform_trend.columns]
            most_stable = platform_trend.nsmallest(1, 'CTR_Percent_std').index[0]
            trends['most_stable_platform'] = most_stable
        
        # Budgettrender
        if 'Spend_SEK' in role_data.columns:
            trends['avg_budget'] = role_data['Spend_SEK'].mean()
            trends['optimal_budget_range'] = {
                'min': role_data['Spend_SEK'].quantile(0.25),
                'max': role_data['Spend_SEK'].quantile(0.75)
            }
        
        # Geografiska trender
        if 'Location' in role_data.columns:
            location_performance = role_data.groupby('Location')['CTR_Percent'].mean()
            if len(location_performance) > 0:
                trends['best_location'] = location_performance.idxmax()
                trends['location_ctr'] = location_performance.max()
        
        return trends
    
    def _generate_recommendations(self, role_data: pd.DataFrame) -> List[str]:
        """Generate specific recommendations based on data patterns"""
        recommendations = []
        
        if role_data.empty:
            return ["Ingen historisk data - överväg att starta med test-budget på flera plattformar"]
        
        # Analysera CTR-distribution
        avg_ctr = role_data['CTR_Percent'].mean()
        if avg_ctr < 1.5:
            recommendations.append(
                f"CTR är låg ({avg_ctr:.1f}%). Överväg att förnya annonskreativ eller targeting"
            )
        elif avg_ctr > 3.0:
            recommendations.append(
                f"Utmärkt CTR ({avg_ctr:.1f}%)! Överväg att öka budget för att skala"
            )
        
        # Analysera plattformsdiversifiering
        platforms_used = role_data['Platform'].nunique()
        if platforms_used == 1:
            recommendations.append(
                "Endast en plattform testad. Diversifiera för att hitta nya möjligheter"
            )
        elif platforms_used > 4:
            # Hitta sämst presterande
            worst_platform = role_data.groupby('Platform')['CTR_Percent'].mean().idxmin()
            recommendations.append(
                f"Överväg att pausa {worst_platform} och fokusera budget på top-performers"
            )
        
        # Budget-rekommendationer
        avg_daily_spend = role_data['Daily_Spend'].mean()
        if avg_daily_spend < 200:
            recommendations.append(
                "Låg daglig budget kan begränsa räckvidd. Testa högre budget för bättre data"
            )
        
        # Geografiska rekommendationer
        if 'Location' in role_data.columns:
            top_locations = role_data.groupby('Location')['CTR_Percent'].mean().nlargest(3)
            if len(top_locations) > 1:
                best_location = top_locations.index[0]
                recommendations.append(
                    f"Fokusera på {best_location} som visar bäst resultat"
                )
        
        return recommendations[:3]  # Max 3 rekommendationer
    
    def _find_similar_roles(self, role: str) -> List[str]:
        """Find similar roles in the data"""
        all_roles = self.campaigns_df['Roll'].unique()
        similar = []
        
        role_lower = role.lower()
        for existing_role in all_roles:
            if role_lower in existing_role.lower() or existing_role.lower() in role_lower:
                similar.append(existing_role)
        
        return similar
    
    def get_platform_comparison(self, role: str) -> pd.DataFrame:
        """
        Get detailed platform comparison for a role
        Returns DataFrame with all metrics
        """
        role_data = self.campaigns_df[self.campaigns_df['Roll'] == role]
        
        if role_data.empty:
            similar_roles = self._find_similar_roles(role)
            if similar_roles:
                role_data = self.campaigns_df[self.campaigns_df['Roll'].isin(similar_roles)]
        
        if role_data.empty:
            return pd.DataFrame()
        
        comparison = role_data.groupby('Platform').agg({
            'CTR_Percent': ['mean', 'std', 'count'],
            'CPC_SEK': ['mean', 'std'],
            'Clicks': 'sum',
            'Spend_SEK': ['sum', 'mean'],
            'Campaign_Days': 'mean'
        }).round(2)
        
        # Flatten column names
        comparison.columns = ['_'.join(col).strip() for col in comparison.columns]
        
        # Add performance score
        comparison['Performance_Score'] = (
            comparison['CTR_Percent_mean'] * 0.5 +  # 50% vikt på CTR
            (100 / comparison['CPC_SEK_mean']) * 0.3 +  # 30% vikt på CPC (inverterad)
            np.log1p(comparison['CTR_Percent_count']) * 0.2  # 20% vikt på datamängd
        )
        
        return comparison.sort_values('Performance_Score', ascending=False)
    
    def get_statistical_confidence(self, role: str, platform: str) -> Dict[str, Any]:
        """
        Calculate statistical confidence for recommendations
        Based on sample size and variance
        """
        data = self.campaigns_df[
            (self.campaigns_df['Roll'] == role) & 
            (self.campaigns_df['Platform'] == platform)
        ]
        
        if len(data) < 2:
            return {'confidence': 'low', 'reason': 'För lite data', 'sample_size': len(data)}
        
        # Beräkna variationskoefficient
        cv_ctr = data['CTR_Percent'].std() / data['CTR_Percent'].mean() if data['CTR_Percent'].mean() > 0 else 1
        
        confidence_level = 'high'
        reason = f"Baserat på {len(data)} kampanjer"
        
        if len(data) < 5:
            confidence_level = 'low'
            reason = f"Endast {len(data)} kampanjer"
        elif len(data) < 10:
            confidence_level = 'medium'
            reason = f"{len(data)} kampanjer ger måttlig säkerhet"
        elif cv_ctr > 0.5:
            confidence_level = 'medium'
            reason = f"Hög variation i resultat (CV={cv_ctr:.2f})"
        
        return {
            'confidence': confidence_level,
            'reason': reason,
            'sample_size': len(data),
            'cv': cv_ctr
        }
