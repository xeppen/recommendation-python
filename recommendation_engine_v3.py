#!/usr/bin/env python3
"""
Enhanced recommendation engine v3 with industry/branch categorization.
Combines role specificity with industry context for ultra-targeted recommendations.
"""

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st
from typing import Dict, List, Tuple, Optional
import re

class IndustryAwareRecommendationEngine:
    def __init__(self, campaign_data_path: str = 'all_platforms_campaigns_complete.csv'):
        """Initialize with role and industry categorization."""
        self.model = SentenceTransformer('KBLab/sentence-bert-swedish-cased')
        self.campaign_df = self._load_and_process_campaign_data(campaign_data_path)
        self.role_industry_stats = self._calculate_role_industry_statistics()
        self.known_combinations = list(self.role_industry_stats.keys())
        self.embeddings = self._create_embeddings()
        
    def _extract_industry(self, company_name: str, campaign_name: str) -> str:
        """Extract industry/branch from company and campaign names."""
        if pd.isna(company_name) and pd.isna(campaign_name):
            return 'Okänd bransch'
        
        company_lower = str(company_name).lower() if company_name else ''
        campaign_lower = str(campaign_name).lower() if campaign_name else ''
        combined = f"{company_lower} {campaign_lower}"
        
        # RETAIL/DETALJHANDEL
        if any(x in combined for x in ['lindex', 'kappahl', 'h&m', 'hm', 'dressman', 'cubus', 'gina', 'bikbok', 
                                       'monki', 'weekday', 'cos', 'arket', 'mq', 'jack & jones', 'vero moda']):
            return 'Mode & Kläder'
        elif any(x in combined for x in ['ica', 'coop', 'willys', 'hemköp', 'lidl', 'city gross', 'maxi', 
                                         'netto', 'willy:s', 'mathem', 'matsmart']):
            return 'Dagligvaror'
        elif any(x in combined for x in ['rusta', 'jula', 'byggmax', 'bauhaus', 'hornbach', 'beijer', 
                                         'k-rauta', 'xl-bygg', 'bygghandel']):
            return 'Bygg & Hem'
        elif any(x in combined for x in ['elgiganten', 'media markt', 'netonnet', 'inet', 'webhallen', 
                                         'kjell & company', 'kjell', 'teknikmagasinet']):
            return 'Elektronik & Teknik'
        elif any(x in combined for x in ['apotek', 'kronans', 'hjärtat', 'apotea', 'lloyds']):
            return 'Apotek & Hälsa'
        elif any(x in combined for x in ['systembolaget', 'systembolag']):
            return 'Systembolaget'
        elif any(x in combined for x in ['biltema', 'mekonomen', 'autoexperten', 'däckia', 'euromaster',
                                         'vianor', 'nokian', 'däck', 'bildelar']):
            return 'Bildelar & Service'
        elif any(x in combined for x in ['mio', 'em home', 'ikea', 'jysk', 'chilli', 'sova', 'säng']):
            return 'Möbler & Inredning'
        elif any(x in combined for x in ['stadium', 'intersport', 'xxl', 'sportamore', 'team sportia']):
            return 'Sport & Fritid'
        elif any(x in combined for x in ['dollarstore', 'normal', 'flying tiger', 'lågpris']):
            return 'Lågprishandel'
        elif any(x in combined for x in ['office depot', 'staples', 'kontorsmaterial']):
            return 'Kontorsmaterial'
        elif any(x in combined for x in ['leksaker', 'br leksaker', 'toys r us', 'lek & baby']):
            return 'Leksaker'
        elif any(x in combined for x in ['åhléns', 'nk', 'nordiska kompaniet', 'varuhus']):
            return 'Varuhus'
        
        # HEALTHCARE/VÅRD
        elif any(x in combined for x in ['karolinska', 'sahlgrenska', 'akademiska', 'danderyds', 'sjukhus',
                                         'vårdcentral', 'hälsocentral', 'lasarett', 'kliniken']):
            return 'Sjukvård'
        elif any(x in combined for x in ['äldreomsorg', 'äldreboende', 'hemtjänst', 'omsorg', 'attendo',
                                         'vardaga', 'humana', 'frösunda']):
            return 'Äldreomsorg'
        elif any(x in combined for x in ['tandvård', 'folktandvård', 'praktikertjänst', 'tandläkare',
                                         'dental', 'smile']):
            return 'Tandvård'
        
        # TECH/IT
        elif any(x in combined for x in ['microsoft', 'google', 'apple', 'amazon', 'spotify', 'klarna',
                                         'tink', 'trustly', 'izettle', 'tech', 'software', 'it-']):
            return 'IT & Tech'
        elif any(x in combined for x in ['tele2', 'telia', 'telenor', 'tre', 'comviq', 'hallon']):
            return 'Telekom'
        elif any(x in combined for x in ['spel', 'gaming', 'king', 'dice', 'paradox', 'mojang']):
            return 'Gaming'
        
        # INDUSTRY/INDUSTRI
        elif any(x in combined for x in ['volvo', 'scania', 'saab', 'ford', 'volkswagen', 'bmw', 'mercedes',
                                         'toyota', 'nissan', 'polestar', 'lynk']):
            return 'Fordonsindustri'
        elif any(x in combined for x in ['abb', 'sandvik', 'atlas copco', 'alfa laval', 'skf', 'ssab']):
            return 'Verkstadsindustri'
        elif any(x in combined for x in ['bygg', 'ncc', 'skanska', 'peab', 'jm', 'veidekke', 'svevia']):
            return 'Byggindustri'
        elif any(x in combined for x in ['carglass', 'bilglas', 'ryds', 'speedy']):
            return 'Bilglas & Reparation'
        
        # SERVICES/TJÄNSTER
        elif any(x in combined for x in ['bank', 'seb', 'swedbank', 'handelsbanken', 'nordea', 'sbab']):
            return 'Bank & Finans'
        elif any(x in combined for x in ['försäkring', 'folksam', 'trygg-hansa', 'länsförsäkringar', 'if']):
            return 'Försäkring'
        elif any(x in combined for x in ['advokatbyrå', 'jurist', 'juridik', 'mannheimer', 'vinge']):
            return 'Juridik'
        elif any(x in combined for x in ['revision', 'pwc', 'ey', 'kpmg', 'deloitte', 'grant thornton']):
            return 'Revision & Redovisning'
        elif any(x in combined for x in ['bemanning', 'academic work', 'adecco', 'manpower', 'randstad']):
            return 'Bemanning & Rekrytering'
        elif any(x in combined for x in ['konsult', 'accenture', 'capgemini', 'cgi', 'tieto', 'evry']):
            return 'Konsultverksamhet'
        
        # HOSPITALITY/SERVICE
        elif any(x in combined for x in ['hotell', 'scandic', 'nordic choice', 'radisson', 'sheraton',
                                         'best western', 'clarion']):
            return 'Hotell & Logi'
        elif any(x in combined for x in ['restaurang', 'mcdonald', 'burger king', 'subway', 'espresso house',
                                         'waynes', 'starbucks', 'krog', 'pizzeria']):
            return 'Restaurang & Café'
        elif any(x in combined for x in ['gym', 'sats', 'fitness24seven', 'friskis', 'nordic wellness',
                                         'actic', 'träning']):
            return 'Gym & Träning'
        
        # TRANSPORT/LOGISTICS
        elif any(x in combined for x in ['postnord', 'dhl', 'ups', 'fedex', 'schenker', 'bring', 'budbee']):
            return 'Logistik & Distribution'
        elif any(x in combined for x in ['sj', 'mtr', 'nobina', 'keolis', 'arriva', 'västtrafik',
                                         'sl', 'kollektivtrafik']):
            return 'Kollektivtrafik'
        elif any(x in combined for x in ['åkeri', 'transport', 'lastbil', 'truck']):
            return 'Åkeri & Transport'
        
        # EDUCATION/UTBILDNING
        elif any(x in combined for x in ['skola', 'gymnasium', 'grundskola', 'förskola', 'utbildning']):
            return 'Utbildning'
        elif any(x in combined for x in ['universitet', 'högskola', 'kth', 'ki', 'su', 'gu', 'lu']):
            return 'Högre utbildning'
        
        # PUBLIC/OFFENTLIG
        elif any(x in combined for x in ['kommun', 'region', 'landsting', 'myndighet', 'försvarsmakten',
                                         'polisen', 'kriminalvården']):
            return 'Offentlig sektor'
        
        # ENERGY/ENERGI
        elif any(x in combined for x in ['vattenfall', 'eon', 'fortum', 'ellevio', 'kraftringen']):
            return 'Energi & Kraft'
        
        # REAL ESTATE/FASTIGHET
        elif any(x in combined for x in ['fastighet', 'rikshem', 'wallenstam', 'balder', 'castellum',
                                         'heimstaden', 'hufvudstaden']):
            return 'Fastighet'
        
        # MEDIA/MEDIA
        elif any(x in combined for x in ['svt', 'tv4', 'mtg', 'bonnier', 'schibsted', 'aftonbladet',
                                         'expressen', 'dn', 'svenska dagbladet']):
            return 'Media & Underhållning'
        
        # Try to identify from We Select fallback patterns
        elif 'we select' in company_lower:
            if 'fallback' in company_lower:
                return 'Diverse branscher'
            else:
                return 'Diverse branscher'
        
        # Default
        else:
            # Try to extract from campaign name patterns
            if any(x in campaign_lower for x in ['bygg', 'anläggning', 'konstruktion']):
                return 'Byggindustri'
            elif any(x in campaign_lower for x in ['vård', 'sjuk', 'hälso']):
                return 'Sjukvård'
            elif any(x in campaign_lower for x in ['it', 'data', 'system', 'utvecklare']):
                return 'IT & Tech'
            elif any(x in campaign_lower for x in ['sälj', 'försäljning', 'butik']):
                return 'Detaljhandel'
            elif any(x in campaign_lower for x in ['lager', 'logistik', 'transport']):
                return 'Logistik & Distribution'
            else:
                return 'Övrig bransch'
    
    def _extract_specific_role(self, campaign_name: str) -> str:
        """Extract specific role (same as v2 but simplified for readability)."""
        if pd.isna(campaign_name):
            return 'Övrig roll'
        
        name_lower = str(campaign_name).lower()
        
        # Simplified role extraction focusing on main categories
        # (Full implementation would be same as v2)
        
        if 'butikschef' in name_lower:
            return 'Butikschef'
        elif 'platschef' in name_lower:
            return 'Platschef'
        elif 'regionchef' in name_lower:
            return 'Regionchef'
        elif 'säljare' in name_lower:
            if 'butik' in name_lower:
                return 'Butikssäljare'
            elif 'fält' in name_lower or 'ute' in name_lower:
                return 'Fältsäljare'
            elif 'inne' in name_lower:
                return 'Innesäljare'
            else:
                return 'Säljare'
        elif 'tekniker' in name_lower:
            if 'service' in name_lower:
                return 'Servicetekniker'
            elif 'fastighet' in name_lower:
                return 'Fastighetstekniker'
            elif 'bilglas' in name_lower:
                return 'Bilglastekniker'
            else:
                return 'Tekniker'
        elif 'sjuksköterska' in name_lower:
            return 'Sjuksköterska'
        elif 'chef' in name_lower:
            return 'Chef'
        elif 'ingenjör' in name_lower:
            return 'Ingenjör'
        elif 'utvecklare' in name_lower:
            return 'Utvecklare'
        elif 'projektledare' in name_lower:
            return 'Projektledare'
        else:
            return 'Övrig roll'
    
    def _load_and_process_campaign_data(self, path: str) -> pd.DataFrame:
        """Load campaign data and extract role + industry."""
        df = pd.read_csv(path)
        
        # Extract role and industry
        df['Role'] = df['campaign_name'].apply(self._extract_specific_role)
        df['Industry'] = df.apply(lambda row: self._extract_industry(row.get('company'), row.get('campaign_name')), axis=1)
        
        # Create combined role-industry key
        df['Role_Industry'] = df['Role'] + ' - ' + df['Industry']
        
        # Remove unspecified combinations
        df = df[(df['Role'] != 'Övrig roll') & (df['Industry'] != 'Övrig bransch')]
        
        return df
    
    def _calculate_role_industry_statistics(self) -> Dict:
        """Calculate statistics for each role-industry combination."""
        stats = {}
        
        # Group by role-industry combination
        for combo in self.campaign_df['Role_Industry'].unique():
            combo_data = self.campaign_df[self.campaign_df['Role_Industry'] == combo]
            stats[combo] = {}
            
            for platform in combo_data['platform'].unique():
                platform_data = combo_data[combo_data['platform'] == platform]
                
                total_impressions = platform_data['total_impressions'].sum()
                total_clicks = platform_data['total_clicks'].sum()
                total_spend = platform_data['total_spend'].sum()
                campaign_count = len(platform_data)
                
                if total_impressions > 0 and total_clicks > 0:
                    stats[combo][platform] = {
                        'ctr': (total_clicks / total_impressions) * 100,
                        'cpc': total_spend / total_clicks,
                        'avg_spend': total_spend / campaign_count,
                        'total_spend': total_spend,
                        'campaigns': campaign_count,
                        'clicks': total_clicks,
                        'impressions': total_impressions
                    }
        
        return stats
    
    def _create_embeddings(self) -> Dict:
        """Create embeddings for all role-industry combinations."""
        embeddings = {}
        for combo in self.known_combinations:
            embeddings[combo] = self.model.encode(combo)
        return embeddings
    
    def find_similar_combinations(self, role: str, industry: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Find similar role-industry combinations."""
        query = f"{role} - {industry}"
        query_embedding = self.model.encode(query)
        
        similarities = []
        for combo, embedding in self.embeddings.items():
            similarity = cosine_similarity(
                query_embedding.reshape(1, -1),
                embedding.reshape(1, -1)
            )[0][0]
            similarities.append((combo, similarity))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def get_recommendations(self, role: str, industry: str = None, budget: float = None, 
                           campaign_days: int = 30) -> Dict:
        """Get channel recommendations for role + industry combination."""
        
        # If no industry specified, try to detect from role
        if not industry:
            industry = 'Diverse branscher'
        
        query_combo = f"{role} - {industry}"
        
        recommendations = {
            'query_role': role,
            'query_industry': industry,
            'query_combination': query_combo,
            'data_source': None,
            'matched_combination': None,
            'channels': {},
            'suggested_mix': {},
            'confidence': None,
            'explanation': None,
            'similar_combinations': []
        }
        
        # Find similar combinations
        similar = self.find_similar_combinations(role, industry)
        recommendations['similar_combinations'] = similar
        
        # Check for exact match
        if query_combo in self.role_industry_stats:
            recommendations['data_source'] = 'exact'
            recommendations['matched_combination'] = query_combo
            recommendations['confidence'] = 'Hög'
            combo_data = self.role_industry_stats[query_combo]
        elif similar and similar[0][1] > 0.7:
            matched_combo, similarity = similar[0]
            recommendations['data_source'] = 'similar'
            recommendations['matched_combination'] = matched_combo
            recommendations['similarity_score'] = similarity
            
            if similarity > 0.85:
                recommendations['confidence'] = 'Hög'
            elif similarity > 0.75:
                recommendations['confidence'] = 'Medel'
            else:
                recommendations['confidence'] = 'Låg'
            
            recommendations['explanation'] = f"Baserat på: {matched_combo} ({similarity*100:.0f}% likhet)"
            combo_data = self.role_industry_stats[matched_combo]
        else:
            # Try to find same role in different industry
            role_matches = [c for c in self.known_combinations if c.startswith(role)]
            if role_matches:
                recommendations['matched_combination'] = role_matches[0]
                recommendations['data_source'] = 'role_only'
                recommendations['confidence'] = 'Låg'
                recommendations['explanation'] = f"Baserat på {role} i annan bransch"
                combo_data = self.role_industry_stats[role_matches[0]]
            else:
                recommendations['explanation'] = "Ingen matchande data hittades"
                return recommendations
        
        # Calculate channel recommendations
        for platform, metrics in combo_data.items():
            recommendations['channels'][platform] = {
                'ctr': round(metrics['ctr'], 2),
                'cpc': round(metrics['cpc'], 2),
                'avg_spend_per_campaign': round(metrics['avg_spend'], 0),
                'campaigns_run': metrics['campaigns'],
                'performance_score': self._calculate_performance_score(metrics)
            }
        
        # Calculate optimal mix
        recommendations['suggested_mix'] = self._calculate_optimal_mix(combo_data)
        
        # Predict outcomes if budget provided
        if budget:
            recommendations['predicted_outcomes'] = self._predict_outcomes(
                combo_data, budget, campaign_days, recommendations['suggested_mix']
            )
        
        return recommendations
    
    def _calculate_performance_score(self, metrics: Dict) -> float:
        """Calculate performance score."""
        ctr_score = min(metrics['ctr'] / 5 * 100, 100)
        cpc_score = max(0, 100 - (metrics['cpc'] / 50 * 100))
        return round(ctr_score * 0.6 + cpc_score * 0.4, 1)
    
    def _calculate_optimal_mix(self, combo_data: Dict) -> Dict:
        """Calculate optimal channel mix."""
        if not combo_data:
            return {}
        
        scores = {platform: self._calculate_performance_score(metrics) 
                 for platform, metrics in combo_data.items()}
        
        sorted_platforms = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        mix = {}
        if len(sorted_platforms) == 1:
            mix[sorted_platforms[0][0]] = 100
        elif len(sorted_platforms) == 2:
            mix[sorted_platforms[0][0]] = 70
            mix[sorted_platforms[1][0]] = 30
        else:
            mix[sorted_platforms[0][0]] = 60
            mix[sorted_platforms[1][0]] = 30
            if len(sorted_platforms) > 2:
                mix[sorted_platforms[2][0]] = 10
        
        return mix
    
    def _predict_outcomes(self, combo_data: Dict, budget: float, 
                         campaign_days: int, channel_mix: Dict) -> Dict:
        """Predict campaign outcomes."""
        predictions = {
            'total_budget': budget,
            'campaign_days': campaign_days,
            'daily_budget': budget / campaign_days,
            'channels': {}
        }
        
        total_clicks = 0
        total_impressions = 0
        
        for platform, percentage in channel_mix.items():
            if platform in combo_data:
                platform_budget = budget * (percentage / 100)
                metrics = combo_data[platform]
                
                predicted_clicks = platform_budget / metrics['cpc']
                predicted_impressions = predicted_clicks / (metrics['ctr'] / 100)
                
                predictions['channels'][platform] = {
                    'budget': round(platform_budget, 0),
                    'predicted_clicks': round(predicted_clicks, 0),
                    'predicted_impressions': round(predicted_impressions, 0),
                    'predicted_ctr': round(metrics['ctr'], 2),
                    'predicted_cpc': round(metrics['cpc'], 2)
                }
                
                total_clicks += predicted_clicks
                total_impressions += predicted_impressions
        
        predictions['total_predicted_clicks'] = round(total_clicks, 0)
        predictions['total_predicted_impressions'] = round(total_impressions, 0)
        predictions['overall_predicted_ctr'] = round(
            (total_clicks / total_impressions * 100) if total_impressions > 0 else 0, 2
        )
        
        return predictions
    
    def get_available_industries(self) -> List[str]:
        """Get list of all available industries."""
        industries = set()
        for combo in self.known_combinations:
            industry = combo.split(' - ')[1] if ' - ' in combo else 'Okänd'
            industries.add(industry)
        return sorted(list(industries))
    
    def get_roles_for_industry(self, industry: str) -> List[str]:
        """Get all roles available for a specific industry."""
        roles = set()
        for combo in self.known_combinations:
            if industry in combo:
                role = combo.split(' - ')[0]
                roles.add(role)
        return sorted(list(roles))
    
    def get_industry_summary(self) -> Dict:
        """Get summary statistics by industry."""
        industry_stats = {}
        
        for combo in self.known_combinations:
            parts = combo.split(' - ')
            if len(parts) == 2:
                role, industry = parts
                
                if industry not in industry_stats:
                    industry_stats[industry] = {
                        'roles': set(),
                        'total_campaigns': 0,
                        'total_spend': 0
                    }
                
                industry_stats[industry]['roles'].add(role)
                
                # Sum up campaigns for this combination
                combo_data = self.campaign_df[self.campaign_df['Role_Industry'] == combo]
                industry_stats[industry]['total_campaigns'] += len(combo_data)
                industry_stats[industry]['total_spend'] += combo_data['total_spend'].sum()
        
        # Convert sets to lists
        for industry in industry_stats:
            industry_stats[industry]['roles'] = sorted(list(industry_stats[industry]['roles']))
            industry_stats[industry]['num_roles'] = len(industry_stats[industry]['roles'])
        
        return industry_stats


# Example usage
if __name__ == "__main__":
    print("🚀 Initierar branschmedveten rekommendationsmotor...")
    engine = IndustryAwareRecommendationEngine()
    
    print(f"\n📊 Laddat {len(engine.known_combinations)} roll-bransch kombinationer")
    
    # Show industry summary
    industry_summary = engine.get_industry_summary()
    print("\n🏢 BRANSCHER I SYSTEMET:")
    print("=" * 60)
    
    # Sort by number of campaigns
    sorted_industries = sorted(industry_summary.items(), 
                              key=lambda x: x[1]['total_campaigns'], 
                              reverse=True)
    
    for industry, stats in sorted_industries[:10]:
        print(f"\n{industry}:")
        print(f"  - {stats['num_roles']} olika roller")
        print(f"  - {stats['total_campaigns']} kampanjer")
        print(f"  - {stats['total_spend']/1000000:.1f}M SEK total spend")
        print(f"  - Roller: {', '.join(stats['roles'][:5])}")
        if len(stats['roles']) > 5:
            print(f"    ... och {len(stats['roles']) - 5} till")
    
    # Test recommendations
    print("\n" + "=" * 60)
    print("TEST: Butikschef inom olika branscher")
    print("=" * 60)
    
    # Test 1: Butikschef - Dagligvaror
    print("\n1. Butikschef - Dagligvaror (Lidl, ICA, etc)")
    result = engine.get_recommendations('Butikschef', 'Dagligvaror', budget=25000)
    if result['channels']:
        print(f"   Matchad: {result['matched_combination']}")
        print(f"   Konfidens: {result['confidence']}")
        for platform, metrics in list(result['channels'].items())[:2]:
            print(f"   {platform}: {metrics['ctr']}% CTR, {metrics['cpc']:.2f} SEK CPC")
    
    # Test 2: Butikschef - Mode
    print("\n2. Butikschef - Mode & Kläder (Lindex, H&M, etc)")
    result = engine.get_recommendations('Butikschef', 'Mode & Kläder', budget=25000)
    if result['channels']:
        print(f"   Matchad: {result['matched_combination']}")
        print(f"   Konfidens: {result['confidence']}")
        for platform, metrics in list(result['channels'].items())[:2]:
            print(f"   {platform}: {metrics['ctr']}% CTR, {metrics['cpc']:.2f} SEK CPC")
    
    # Test 3: Tekniker - Bilglas
    print("\n3. Tekniker - Bilglas & Reparation (Carglass)")
    result = engine.get_recommendations('Tekniker', 'Bilglas & Reparation', budget=20000)
    if result['channels']:
        print(f"   Matchad: {result['matched_combination']}")
        print(f"   Konfidens: {result['confidence']}")
        for platform, metrics in list(result['channels'].items())[:2]:
            print(f"   {platform}: {metrics['ctr']}% CTR, {metrics['cpc']:.2f} SEK CPC")
