#!/usr/bin/env python3
"""
Recommendation engine that combines role similarity matching with real campaign performance data.
Uses similarity scores to recommend channels for roles without direct campaign data.
"""

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st
from typing import Dict, List, Tuple, Optional

class RecommendationEngine:
    def __init__(self, campaign_data_path: str = 'all_platforms_campaigns_complete.csv'):
        """Initialize the recommendation engine with campaign data and similarity model."""
        self.model = SentenceTransformer('KBLab/sentence-bert-swedish-cased')
        self.campaign_df = self._load_and_process_campaign_data(campaign_data_path)
        self.role_stats = self._calculate_role_statistics()
        self.known_roles = list(self.role_stats.keys())
        self.role_embeddings = self._create_role_embeddings()
        
    def _load_and_process_campaign_data(self, path: str) -> pd.DataFrame:
        """Load campaign data and extract roles."""
        df = pd.read_csv(path)
        
        # Extract roles from campaign names
        role_patterns = {
            'Sjuksköterska': ['sjuksköterska', 'sjukskötare', 'nurse'],
            'Ambulanssjuksköterska': ['ambulanssjuksköterska', 'ambulans'],
            'Anestesisjuksköterska': ['anestesisjuksköterska', 'anestesi'],
            'Tekniker': ['tekniker', 'teknisk', 'technical'],
            'Servicetekniker': ['servicetekniker', 'service'],
            'Chef': ['chef', 'ledare', 'manager', 'platschef', 'driftchef'],
            'Säljare': ['säljare', 'sälj', 'sales', 'försäljning'],
            'Ingenjör': ['ingenjör', 'engineer'],
            'Konsult': ['konsult', 'consultant', 'rådgivare'],
            'Projektledare': ['projektledare', 'project', 'projektchef'],
            'Controller': ['controller', 'ekonom', 'business controller'],
            'Mekaniker': ['mekaniker', 'mek', 'bilmekaniker'],
            'HR-specialist': ['hr-specialist', 'hr specialist', 'personalspecialist'],
            'IT-specialist': ['it-specialist', 'it specialist', 'systemtekniker', 'utvecklare'],
            'Lagerarbetare': ['lagerarbetare', 'lager', 'terminal'],
            'Butikschef': ['butikschef', 'butiks', 'store manager'],
            'VD': ['vd', 'ceo', 'verkställande'],
            'Administratör': ['administratör', 'admin', 'administration'],
            'Elektriker': ['elektriker', 'el-installatör'],
            'Läkare': ['läkare', 'doktor', 'physician'],
            'Undersköterska': ['undersköterska', 'vårdbiträde'],
            'Fysioterapeut': ['fysioterapeut', 'sjukgymnast'],
            'Arbetsterapeut': ['arbetsterapeut'],
            'Redovisningsekonom': ['redovisningsekonom', 'redovisning'],
            'Fastighetsförvaltare': ['fastighetsförvaltare', 'förvaltare'],
            'Kock': ['kock', 'kökschef', 'chef de cuisine'],
            'Serveringspersonal': ['servering', 'servitör', 'servitris'],
            'Barista': ['barista', 'kafé'],
            'Förare': ['förare', 'chaufför', 'driver', 'lastbilsförare']
        }
        
        df['Role'] = None
        for role, patterns in role_patterns.items():
            for pattern in patterns:
                mask = df['campaign_name'].str.contains(pattern, case=False, na=False)
                df.loc[mask & df['Role'].isna(), 'Role'] = role
        
        return df
    
    def _calculate_role_statistics(self) -> Dict:
        """Calculate performance statistics for each role and platform."""
        stats = {}
        
        # Filter to only campaigns with identified roles
        role_df = self.campaign_df[self.campaign_df['Role'].notna()].copy()
        
        for role in role_df['Role'].unique():
            role_data = role_df[role_df['Role'] == role]
            stats[role] = {}
            
            for platform in role_data['platform'].unique():
                platform_data = role_data[role_data['platform'] == platform]
                
                # Calculate metrics
                total_impressions = platform_data['total_impressions'].sum()
                total_clicks = platform_data['total_clicks'].sum()
                total_spend = platform_data['total_spend'].sum()
                campaign_count = len(platform_data)
                
                if total_impressions > 0 and total_clicks > 0:
                    stats[role][platform] = {
                        'ctr': (total_clicks / total_impressions) * 100,
                        'cpc': total_spend / total_clicks,
                        'avg_spend': total_spend / campaign_count,
                        'total_spend': total_spend,
                        'campaigns': campaign_count,
                        'clicks': total_clicks,
                        'impressions': total_impressions
                    }
        
        return stats
    
    def _create_role_embeddings(self) -> Dict:
        """Create embeddings for all known roles."""
        embeddings = {}
        for role in self.known_roles:
            embeddings[role] = self.model.encode(role)
        return embeddings
    
    def find_similar_role(self, query_role: str, threshold: float = 0.7) -> Optional[Tuple[str, float]]:
        """
        Find the most similar role from known roles.
        Returns (role_name, similarity_score) or None if below threshold.
        """
        query_embedding = self.model.encode(query_role)
        
        max_similarity = 0
        best_match = None
        
        for role, role_embedding in self.role_embeddings.items():
            similarity = cosine_similarity(
                query_embedding.reshape(1, -1),
                role_embedding.reshape(1, -1)
            )[0][0]
            
            if similarity > max_similarity:
                max_similarity = similarity
                best_match = role
        
        if max_similarity >= threshold:
            return (best_match, max_similarity)
        return None
    
    def get_recommendations(self, query_role: str, budget: float = None, 
                           campaign_days: int = 30) -> Dict:
        """
        Get channel recommendations for a role.
        Uses exact match if available, otherwise finds similar role.
        """
        recommendations = {
            'query_role': query_role,
            'data_source': None,
            'similarity_score': None,
            'matched_role': None,
            'channels': {},
            'suggested_mix': {},
            'confidence': None,
            'explanation': None
        }
        
        # Check for exact match
        if query_role in self.role_stats:
            recommendations['data_source'] = 'exact'
            recommendations['matched_role'] = query_role
            recommendations['similarity_score'] = 1.0
            recommendations['confidence'] = 'Hög'
            role_data = self.role_stats[query_role]
        else:
            # Find similar role
            similar = self.find_similar_role(query_role)
            if similar:
                matched_role, similarity = similar
                recommendations['data_source'] = 'similar'
                recommendations['matched_role'] = matched_role
                recommendations['similarity_score'] = similarity
                recommendations['confidence'] = 'Medel' if similarity > 0.8 else 'Låg'
                recommendations['explanation'] = f"Baserat på liknande roll: {matched_role} ({similarity*100:.0f}% likhet)"
                role_data = self.role_stats[matched_role]
            else:
                recommendations['explanation'] = "Ingen liknande roll hittades i databasen"
                return recommendations
        
        # Calculate channel recommendations
        total_campaigns = sum(data['campaigns'] for data in role_data.values())
        
        for platform, metrics in role_data.items():
            recommendations['channels'][platform] = {
                'ctr': round(metrics['ctr'], 2),
                'cpc': round(metrics['cpc'], 2),
                'avg_spend_per_campaign': round(metrics['avg_spend'], 0),
                'total_historical_spend': round(metrics['total_spend'], 0),
                'campaigns_run': metrics['campaigns'],
                'performance_score': self._calculate_performance_score(metrics)
            }
        
        # Calculate suggested channel mix based on performance
        recommendations['suggested_mix'] = self._calculate_optimal_mix(role_data, budget)
        
        # Add predicted outcomes if budget provided
        if budget:
            recommendations['predicted_outcomes'] = self._predict_outcomes(
                role_data, budget, campaign_days, recommendations['suggested_mix']
            )
        
        return recommendations
    
    def _calculate_performance_score(self, metrics: Dict) -> float:
        """Calculate a performance score (0-100) based on CTR and CPC."""
        # Normalize CTR (assume 0-5% range)
        ctr_score = min(metrics['ctr'] / 5 * 100, 100)
        
        # Normalize CPC (inverse - lower is better, assume 0-50 SEK range)
        cpc_score = max(0, 100 - (metrics['cpc'] / 50 * 100))
        
        # Weight CTR more heavily than CPC
        return round(ctr_score * 0.6 + cpc_score * 0.4, 1)
    
    def _calculate_optimal_mix(self, role_data: Dict, budget: Optional[float] = None) -> Dict:
        """Calculate optimal channel mix based on performance."""
        if not role_data:
            return {}
        
        # Calculate performance scores
        scores = {}
        for platform, metrics in role_data.items():
            scores[platform] = self._calculate_performance_score(metrics)
        
        # Sort by performance
        sorted_platforms = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Recommend mix based on performance tiers
        mix = {}
        if len(sorted_platforms) == 1:
            mix[sorted_platforms[0][0]] = 100
        elif len(sorted_platforms) == 2:
            # 70/30 split for two channels
            mix[sorted_platforms[0][0]] = 70
            mix[sorted_platforms[1][0]] = 30
        else:
            # 60/30/10 split for three+ channels
            mix[sorted_platforms[0][0]] = 60
            if len(sorted_platforms) > 1:
                mix[sorted_platforms[1][0]] = 30
            if len(sorted_platforms) > 2:
                mix[sorted_platforms[2][0]] = 10
        
        return mix
    
    def _predict_outcomes(self, role_data: Dict, budget: float, 
                         campaign_days: int, channel_mix: Dict) -> Dict:
        """Predict campaign outcomes based on historical data."""
        predictions = {
            'total_budget': budget,
            'campaign_days': campaign_days,
            'daily_budget': budget / campaign_days,
            'channels': {}
        }
        
        total_predicted_clicks = 0
        total_predicted_impressions = 0
        
        for platform, percentage in channel_mix.items():
            if platform in role_data:
                platform_budget = budget * (percentage / 100)
                metrics = role_data[platform]
                
                # Predict based on historical CPC and CTR
                predicted_clicks = platform_budget / metrics['cpc']
                predicted_impressions = predicted_clicks / (metrics['ctr'] / 100)
                
                predictions['channels'][platform] = {
                    'budget': round(platform_budget, 0),
                    'predicted_clicks': round(predicted_clicks, 0),
                    'predicted_impressions': round(predicted_impressions, 0),
                    'predicted_ctr': round(metrics['ctr'], 2),
                    'predicted_cpc': round(metrics['cpc'], 2)
                }
                
                total_predicted_clicks += predicted_clicks
                total_predicted_impressions += predicted_impressions
        
        predictions['total_predicted_clicks'] = round(total_predicted_clicks, 0)
        predictions['total_predicted_impressions'] = round(total_predicted_impressions, 0)
        predictions['overall_predicted_ctr'] = round(
            (total_predicted_clicks / total_predicted_impressions * 100) if total_predicted_impressions > 0 else 0, 
            2
        )
        
        return predictions
    
    def get_all_known_roles(self) -> List[str]:
        """Return list of all roles with campaign data."""
        return sorted(self.known_roles)
    
    def get_role_summary(self, role: str) -> Optional[Dict]:
        """Get summary statistics for a specific role."""
        if role not in self.role_stats:
            return None
        
        summary = {
            'role': role,
            'platforms': list(self.role_stats[role].keys()),
            'total_campaigns': sum(data['campaigns'] for data in self.role_stats[role].values()),
            'total_spend': sum(data['total_spend'] for data in self.role_stats[role].values()),
            'best_platform': None,
            'worst_platform': None
        }
        
        # Find best and worst performing platforms
        platform_scores = {
            platform: self._calculate_performance_score(metrics)
            for platform, metrics in self.role_stats[role].items()
        }
        
        if platform_scores:
            summary['best_platform'] = max(platform_scores, key=platform_scores.get)
            summary['worst_platform'] = min(platform_scores, key=platform_scores.get)
        
        return summary


# Example usage
if __name__ == "__main__":
    print("🚀 Initierar rekommendationsmotor...")
    engine = RecommendationEngine()
    
    print(f"\n📊 Laddat data för {len(engine.known_roles)} roller")
    print(f"Kända roller: {', '.join(engine.known_roles[:10])}...")
    
    # Test exact match
    print("\n" + "="*60)
    print("TEST 1: Exakt matchning - 'Sjuksköterska'")
    print("="*60)
    result = engine.get_recommendations('Sjuksköterska', budget=20000, campaign_days=30)
    print(f"Datakälla: {result['data_source']}")
    print(f"Konfidens: {result['confidence']}")
    print(f"Rekommenderad kanalmix: {result['suggested_mix']}")
    for platform, metrics in result['channels'].items():
        print(f"  {platform}: {metrics['ctr']}% CTR, {metrics['cpc']} SEK CPC, Score: {metrics['performance_score']}")
    
    # Test similar match
    print("\n" + "="*60)
    print("TEST 2: Likhetsbaserad matchning - 'Ambulanssjuksköterska'")
    print("="*60)
    result = engine.get_recommendations('Ambulanssjuksköterska', budget=15000, campaign_days=30)
    print(f"Datakälla: {result['data_source']}")
    print(f"Matchad roll: {result['matched_role']} ({result['similarity_score']*100:.0f}% likhet)")
    print(f"Konfidens: {result['confidence']}")
    print(f"Förklaring: {result['explanation']}")
    print(f"Rekommenderad kanalmix: {result['suggested_mix']}")
    
    if 'predicted_outcomes' in result:
        print(f"\nFörutsägelser för 15,000 SEK budget:")
        pred = result['predicted_outcomes']
        print(f"  Totalt förväntade klick: {pred['total_predicted_clicks']:,.0f}")
        print(f"  Förväntad CTR: {pred['overall_predicted_ctr']}%")
    
    # Test no match
    print("\n" + "="*60)
    print("TEST 3: Ingen matchning - 'Astronaut'")
    print("="*60)
    result = engine.get_recommendations('Astronaut')
    print(f"Förklaring: {result['explanation']}")
