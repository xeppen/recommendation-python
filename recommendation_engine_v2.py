#!/usr/bin/env python3
"""
Enhanced recommendation engine with granular role categorization.
Splits generic roles like "Chef" into specific subcategories for better recommendations.
"""

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st
from typing import Dict, List, Tuple, Optional
import re

class EnhancedRecommendationEngine:
    def __init__(self, campaign_data_path: str = 'all_platforms_campaigns_complete.csv'):
        """Initialize with enhanced role categorization."""
        self.model = SentenceTransformer('KBLab/sentence-bert-swedish-cased')
        self.campaign_df = self._load_and_process_campaign_data(campaign_data_path)
        self.role_stats = self._calculate_role_statistics()
        self.known_roles = list(self.role_stats.keys())
        self.role_embeddings = self._create_role_embeddings()
        
    def _extract_specific_role(self, campaign_name: str) -> str:
        """Extract specific role with granular categorization."""
        if pd.isna(campaign_name):
            return 'Övrig roll'
        
        name_lower = str(campaign_name).lower()
        
        # CHEF ROLES - Hierarchical and functional
        if 'chef' in name_lower or 'ledare' in name_lower or 'manager' in name_lower:
            # Executive level
            if any(x in name_lower for x in ['vd', 'ceo', 'verkställande']):
                return 'VD/CEO'
            elif 'cfo' in name_lower or 'finanschef' in name_lower:
                return 'CFO/Finanschef'
            elif 'cto' in name_lower or 'teknikchef' in name_lower:
                return 'CTO/Teknikchef'
            
            # Regional/Area management
            elif 'regionchef' in name_lower or 'regionschef' in name_lower:
                return 'Regionchef'
            elif 'områdeschef' in name_lower:
                return 'Områdeschef'
            elif 'distriktschef' in name_lower:
                return 'Distriktschef'
            
            # Operational management
            elif 'platschef' in name_lower:
                return 'Platschef'
            elif 'driftchef' in name_lower or 'driftschef' in name_lower:
                return 'Driftchef'
            elif 'produktionschef' in name_lower:
                return 'Produktionschef'
            elif 'anläggningschef' in name_lower:
                return 'Anläggningschef'
            
            # Retail/Service
            elif 'butikschef' in name_lower:
                return 'Butikschef'
            elif 'restaurangchef' in name_lower:
                return 'Restaurangchef'
            elif 'hotellchef' in name_lower:
                return 'Hotellchef'
            
            # Healthcare
            elif 'verksamhetschef' in name_lower:
                if 'vård' in name_lower or 'hälso' in name_lower:
                    return 'Verksamhetschef Vård'
                else:
                    return 'Verksamhetschef'
            elif 'vårdchef' in name_lower:
                return 'Vårdchef'
            elif 'omvårdnadschef' in name_lower:
                return 'Omvårdnadschef'
            elif 'enhetschef' in name_lower:
                if 'vård' in name_lower or 'omsorg' in name_lower:
                    return 'Enhetschef Vård/Omsorg'
                else:
                    return 'Enhetschef'
            
            # Functional management
            elif 'försäljningschef' in name_lower or 'säljchef' in name_lower:
                return 'Försäljningschef'
            elif 'marknadschef' in name_lower:
                return 'Marknadschef'
            elif 'hr-chef' in name_lower or 'personalchef' in name_lower:
                return 'HR-chef'
            elif 'it-chef' in name_lower:
                return 'IT-chef'
            elif 'ekonomichef' in name_lower:
                return 'Ekonomichef'
            elif 'inköpschef' in name_lower:
                return 'Inköpschef'
            elif 'logistikchef' in name_lower:
                return 'Logistikchef'
            elif 'kvalitetschef' in name_lower:
                return 'Kvalitetschef'
            elif 'projektchef' in name_lower:
                return 'Projektchef'
            elif 'produktchef' in name_lower:
                return 'Produktchef'
            
            # Team level
            elif 'teamchef' in name_lower or 'gruppchef' in name_lower:
                return 'Teamchef/Gruppchef'
            elif 'avdelningschef' in name_lower:
                return 'Avdelningschef'
            elif 'sektionschef' in name_lower:
                return 'Sektionschef'
            
            # Generic chef
            elif 'chef' in name_lower:
                return 'Chef (allmän)'
        
        # TEKNIKER ROLES - By specialization
        elif 'tekniker' in name_lower:
            if 'servicetekniker' in name_lower:
                if 'hvac' in name_lower or 'ventilation' in name_lower:
                    return 'Servicetekniker HVAC'
                elif 'el' in name_lower:
                    return 'Servicetekniker El'
                elif 'it' in name_lower:
                    return 'Servicetekniker IT'
                else:
                    return 'Servicetekniker'
            elif 'fastighetstekniker' in name_lower:
                return 'Fastighetstekniker'
            elif 'drifttekniker' in name_lower:
                return 'Drifttekniker'
            elif 'automationstekniker' in name_lower:
                return 'Automationstekniker'
            elif 'processtekniker' in name_lower:
                return 'Processtekniker'
            elif 'laboratorietekniker' in name_lower or 'labbtekniker' in name_lower:
                return 'Laboratorietekniker'
            elif 'nätverkstekniker' in name_lower:
                return 'Nätverkstekniker'
            elif 'systemtekniker' in name_lower or 'it-tekniker' in name_lower:
                return 'IT-tekniker/Systemtekniker'
            elif 'biltekniker' in name_lower or 'fordonstekniker' in name_lower:
                return 'Biltekniker/Fordonstekniker'
            elif 'bilglastekniker' in name_lower:
                return 'Bilglastekniker'
            elif 'besiktningstekniker' in name_lower:
                return 'Besiktningstekniker'
            elif 'underhållstekniker' in name_lower:
                return 'Underhållstekniker'
            elif 'mättekniker' in name_lower:
                return 'Mättekniker'
            elif 'kyltekniker' in name_lower:
                return 'Kyltekniker'
            elif 'hissteknikeer' in name_lower:
                return 'Hisstekniker'
            else:
                return 'Tekniker (allmän)'
        
        # SÄLJARE ROLES - By type and industry
        elif 'säljare' in name_lower or 'sales' in name_lower:
            if 'butikssäljare' in name_lower or 'butiks' in name_lower:
                return 'Butikssäljare'
            elif 'fältsäljare' in name_lower or 'utesäljare' in name_lower:
                return 'Fältsäljare'
            elif 'innesäljare' in name_lower or 'inside sales' in name_lower:
                return 'Innesäljare'
            elif 'b2b' in name_lower or 'företagssäljare' in name_lower:
                return 'B2B-säljare'
            elif 'key account' in name_lower or 'kam' in name_lower:
                return 'Key Account Manager'
            elif 'account manager' in name_lower:
                return 'Account Manager'
            elif 'teknisk säljare' in name_lower:
                return 'Teknisk säljare'
            elif 'säljingenjör' in name_lower:
                return 'Säljingenjör'
            elif 'bilförsäljare' in name_lower:
                return 'Bilförsäljare'
            elif 'fastighetsmäklare' in name_lower or 'mäklare' in name_lower:
                return 'Fastighetsmäklare'
            elif 'telefonförsäljare' in name_lower:
                return 'Telefonförsäljare'
            else:
                return 'Säljare (allmän)'
        
        # SJUKSKÖTERSKA ROLES - By specialization
        elif 'sjuksköterska' in name_lower or 'sjukskötare' in name_lower:
            if 'anestesisjuksköterska' in name_lower:
                return 'Anestesisjuksköterska'
            elif 'operationssjuksköterska' in name_lower:
                return 'Operationssjuksköterska'
            elif 'intensivvårdssjuksköterska' in name_lower or 'iva' in name_lower:
                return 'Intensivvårdssjuksköterska'
            elif 'barnsjuksköterska' in name_lower:
                return 'Barnsjuksköterska'
            elif 'distriktssjuksköterska' in name_lower or 'distriktssköterska' in name_lower:
                return 'Distriktssjuksköterska'
            elif 'psykiatrisjuksköterska' in name_lower:
                return 'Psykiatrisjuksköterska'
            elif 'ambulanssjuksköterska' in name_lower:
                return 'Ambulanssjuksköterska'
            elif 'akutsjuksköterska' in name_lower:
                return 'Akutsjuksköterska'
            elif 'diabetessjuksköterska' in name_lower:
                return 'Diabetessjuksköterska'
            elif 'onkologisjuksköterska' in name_lower:
                return 'Onkologisjuksköterska'
            elif 'röntgensjuksköterska' in name_lower:
                return 'Röntgensjuksköterska'
            elif 'skolsköterska' in name_lower:
                return 'Skolsköterska'
            elif 'företagssköterska' in name_lower:
                return 'Företagssköterska'
            else:
                return 'Sjuksköterska (allmän)'
        
        # INGENJÖR ROLES - By field
        elif 'ingenjör' in name_lower or 'engineer' in name_lower:
            if 'civilingenjör' in name_lower:
                return 'Civilingenjör'
            elif 'maskiningenjör' in name_lower:
                return 'Maskiningenjör'
            elif 'elkraftsingenjör' in name_lower or 'elingenjör' in name_lower:
                return 'Elkraftsingenjör'
            elif 'byggingenjör' in name_lower:
                return 'Byggingenjör'
            elif 'konstruktionsingenjör' in name_lower:
                return 'Konstruktionsingenjör'
            elif 'processingenjör' in name_lower:
                return 'Processingenjör'
            elif 'kvalitetsingenjör' in name_lower:
                return 'Kvalitetsingenjör'
            elif 'miljöingenjör' in name_lower:
                return 'Miljöingenjör'
            elif 'automationsingenjör' in name_lower:
                return 'Automationsingenjör'
            elif 'mjukvaruingenjör' in name_lower or 'software engineer' in name_lower:
                return 'Mjukvaruingenjör'
            elif 'systemingenjör' in name_lower:
                return 'Systemingenjör'
            elif 'projektingenjör' in name_lower:
                return 'Projektingenjör'
            elif 'säljingenjör' in name_lower:
                return 'Säljingenjör'
            elif 'servicingenjör' in name_lower:
                return 'Servicingenjör'
            elif 'utvecklingsingenjör' in name_lower:
                return 'Utvecklingsingenjör'
            elif 'testingenjör' in name_lower:
                return 'Testingenjör'
            elif 'dataingenjör' in name_lower or 'data engineer' in name_lower:
                return 'Dataingenjör'
            elif 'devops' in name_lower:
                return 'DevOps-ingenjör'
            else:
                return 'Ingenjör (allmän)'
        
        # IT/UTVECKLARE ROLES
        elif any(x in name_lower for x in ['utvecklare', 'developer', 'programmerare']):
            if 'frontend' in name_lower:
                return 'Frontend-utvecklare'
            elif 'backend' in name_lower:
                return 'Backend-utvecklare'
            elif 'fullstack' in name_lower or 'full-stack' in name_lower:
                return 'Fullstack-utvecklare'
            elif 'app' in name_lower or 'mobilutvecklare' in name_lower:
                return 'Apputvecklare'
            elif 'webbutvecklare' in name_lower or 'web developer' in name_lower:
                return 'Webbutvecklare'
            elif 'systemutvecklare' in name_lower:
                return 'Systemutvecklare'
            elif 'javautvecklare' in name_lower:
                return 'Java-utvecklare'
            elif '.net' in name_lower or 'dotnet' in name_lower:
                return '.NET-utvecklare'
            elif 'python' in name_lower:
                return 'Python-utvecklare'
            elif 'c++' in name_lower or 'cpp' in name_lower:
                return 'C++-utvecklare'
            elif 'embedded' in name_lower or 'inbyggd' in name_lower:
                return 'Embedded-utvecklare'
            else:
                return 'Utvecklare (allmän)'
        
        # PROJEKTLEDARE ROLES
        elif 'projektledare' in name_lower or 'project manager' in name_lower:
            if 'it' in name_lower or 'teknisk' in name_lower:
                return 'IT-projektledare'
            elif 'bygg' in name_lower:
                return 'Byggprojektledare'
            elif 'anläggning' in name_lower:
                return 'Anläggningsprojektledare'
            elif 'el' in name_lower:
                return 'Elprojektledare'
            elif 'scrum master' in name_lower:
                return 'Scrum Master'
            elif 'agile' in name_lower:
                return 'Agile Coach'
            else:
                return 'Projektledare (allmän)'
        
        # KONSULT ROLES
        elif 'konsult' in name_lower or 'consultant' in name_lower:
            if 'managementkonsult' in name_lower:
                return 'Managementkonsult'
            elif 'it-konsult' in name_lower or 'systemkonsult' in name_lower:
                return 'IT-konsult'
            elif 'ekonomikonsult' in name_lower:
                return 'Ekonomikonsult'
            elif 'hr-konsult' in name_lower:
                return 'HR-konsult'
            elif 'säkerhetskonsult' in name_lower:
                return 'Säkerhetskonsult'
            elif 'miljökonsult' in name_lower:
                return 'Miljökonsult'
            elif 'byggkonsult' in name_lower:
                return 'Byggkonsult'
            else:
                return 'Konsult (allmän)'
        
        # EKONOMI ROLES
        elif any(x in name_lower for x in ['ekonom', 'controller', 'redovisning']):
            if 'ekonomichef' in name_lower:
                return 'Ekonomichef'
            elif 'controller' in name_lower:
                if 'business' in name_lower:
                    return 'Business Controller'
                elif 'financial' in name_lower:
                    return 'Financial Controller'
                else:
                    return 'Controller'
            elif 'redovisningsekonom' in name_lower:
                return 'Redovisningsekonom'
            elif 'ekonomiassistent' in name_lower:
                return 'Ekonomiassistent'
            elif 'löneadministratör' in name_lower or 'löneekonom' in name_lower:
                return 'Löneadministratör'
            elif 'revisor' in name_lower:
                return 'Revisor'
            else:
                return 'Ekonom (allmän)'
        
        # LAGER/LOGISTIK ROLES
        elif any(x in name_lower for x in ['lager', 'logistik', 'truck']):
            if 'lagerchef' in name_lower:
                return 'Lagerchef'
            elif 'lagerarbetare' in name_lower:
                return 'Lagerarbetare'
            elif 'truckförare' in name_lower:
                return 'Truckförare'
            elif 'lagerkoordinator' in name_lower:
                return 'Lagerkoordinator'
            elif 'logistiker' in name_lower:
                return 'Logistiker'
            elif 'terminalarbetare' in name_lower:
                return 'Terminalarbetare'
            else:
                return 'Lager/Logistik'
        
        # TRANSPORT ROLES
        elif any(x in name_lower for x in ['förare', 'chaufför', 'driver']):
            if 'lastbilsförare' in name_lower or 'lastbilschaufför' in name_lower:
                return 'Lastbilsförare'
            elif 'bussförare' in name_lower or 'busschaufför' in name_lower:
                return 'Bussförare'
            elif 'taxiförare' in name_lower:
                return 'Taxiförare'
            elif 'budbilsförare' in name_lower or 'bud' in name_lower:
                return 'Budbilsförare'
            elif 'maskinförare' in name_lower:
                return 'Maskinförare'
            else:
                return 'Förare (allmän)'
        
        # HR ROLES
        elif any(x in name_lower for x in ['hr', 'personal', 'rekryter']):
            if 'hr-chef' in name_lower or 'personalchef' in name_lower:
                return 'HR-chef'
            elif 'hr-specialist' in name_lower or 'hr specialist' in name_lower:
                return 'HR-specialist'
            elif 'hr-generalist' in name_lower:
                return 'HR-generalist'
            elif 'rekryterare' in name_lower or 'recruiter' in name_lower:
                return 'Rekryterare'
            elif 'personaladministratör' in name_lower:
                return 'Personaladministratör'
            else:
                return 'HR/Personal'
        
        # BYGG ROLES
        elif any(x in name_lower for x in ['snickare', 'elektriker', 'rörmontör', 'målare', 'plåtslagare']):
            if 'snickare' in name_lower:
                return 'Snickare'
            elif 'elektriker' in name_lower:
                return 'Elektriker'
            elif 'rörmontör' in name_lower or 'rörläggare' in name_lower:
                return 'Rörmontör'
            elif 'målare' in name_lower:
                return 'Målare'
            elif 'plåtslagare' in name_lower:
                return 'Plåtslagare'
            elif 'betongarbetare' in name_lower:
                return 'Betongarbetare'
            elif 'kranförare' in name_lower:
                return 'Kranförare'
            elif 'ställningsmontör' in name_lower:
                return 'Ställningsmontör'
            else:
                return 'Byggarbetare'
        
        # VÅRD ROLES (besides sjuksköterska)
        elif any(x in name_lower for x in ['läkare', 'doktor', 'undersköterska', 'vårdbiträde']):
            if 'läkare' in name_lower or 'doktor' in name_lower:
                if 'överläkare' in name_lower:
                    return 'Överläkare'
                elif 'specialistläkare' in name_lower:
                    return 'Specialistläkare'
                elif 'st-läkare' in name_lower:
                    return 'ST-läkare'
                else:
                    return 'Läkare'
            elif 'undersköterska' in name_lower:
                return 'Undersköterska'
            elif 'vårdbiträde' in name_lower:
                return 'Vårdbiträde'
            elif 'vårdadministratör' in name_lower:
                return 'Vårdadministratör'
        
        # SERVICE ROLES
        elif any(x in name_lower for x in ['kock', 'servitör', 'servitris', 'barista']):
            if 'kock' in name_lower:
                if 'kökschef' in name_lower:
                    return 'Kökschef'
                else:
                    return 'Kock'
            elif 'servitör' in name_lower or 'servitris' in name_lower:
                return 'Serveringspersonal'
            elif 'barista' in name_lower:
                return 'Barista'
            elif 'diskare' in name_lower:
                return 'Diskare'
        
        # FASTIGHET ROLES
        elif any(x in name_lower for x in ['fastighet', 'förvaltare', 'vaktmästare']):
            if 'fastighetsförvaltare' in name_lower:
                return 'Fastighetsförvaltare'
            elif 'fastighetsskötare' in name_lower:
                return 'Fastighetsskötare'
            elif 'fastighetstekniker' in name_lower:
                return 'Fastighetstekniker'
            elif 'vaktmästare' in name_lower:
                return 'Vaktmästare'
        
        # ADMIN ROLES
        elif any(x in name_lower for x in ['administratör', 'assistent', 'receptionist']):
            if 'administratör' in name_lower:
                return 'Administratör'
            elif 'assistent' in name_lower:
                if 'vd' in name_lower or 'executive' in name_lower:
                    return 'VD-assistent'
                else:
                    return 'Assistent'
            elif 'receptionist' in name_lower:
                return 'Receptionist'
            elif 'koordinator' in name_lower:
                return 'Koordinator'
        
        # MEKANIKER ROLES
        elif 'mekaniker' in name_lower:
            if 'bilmekaniker' in name_lower:
                return 'Bilmekaniker'
            elif 'lastbilsmekaniker' in name_lower:
                return 'Lastbilsmekaniker'
            elif 'industrimekaniker' in name_lower:
                return 'Industrimekaniker'
            else:
                return 'Mekaniker'
        
        # Default - try to extract something meaningful
        else:
            # Look for common role keywords
            role_keywords = {
                'specialist': 'Specialist',
                'analytiker': 'Analytiker',
                'designer': 'Designer',
                'arkitekt': 'Arkitekt',
                'operatör': 'Operatör',
                'montör': 'Montör',
                'inspektör': 'Inspektör',
                'handläggare': 'Handläggare',
                'utredare': 'Utredare',
                'rådgivare': 'Rådgivare',
                'coach': 'Coach',
                'tränare': 'Tränare',
                'pedagog': 'Pedagog',
                'lärare': 'Lärare',
                'forskare': 'Forskare'
            }
            
            for keyword, role in role_keywords.items():
                if keyword in name_lower:
                    return role
            
            return 'Övrig roll'
    
    def _load_and_process_campaign_data(self, path: str) -> pd.DataFrame:
        """Load campaign data and extract specific roles."""
        df = pd.read_csv(path)
        
        # Extract specific roles using the enhanced categorization
        df['Role'] = df['campaign_name'].apply(self._extract_specific_role)
        
        # Remove generic/unspecified roles
        df = df[df['Role'] != 'Övrig roll']
        
        return df
    
    def _calculate_role_statistics(self) -> Dict:
        """Calculate performance statistics for each specific role."""
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
    
    def find_similar_roles(self, query_role: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Find the most similar roles from the specific categories."""
        if not self.role_embeddings:
            return []
        
        query_embedding = self.model.encode(query_role)
        similarities = []
        
        for role, role_embedding in self.role_embeddings.items():
            similarity = cosine_similarity(
                query_embedding.reshape(1, -1),
                role_embedding.reshape(1, -1)
            )[0][0]
            similarities.append((role, similarity))
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def get_recommendations(self, query_role: str, budget: float = None, 
                           campaign_days: int = 30) -> Dict:
        """Get channel recommendations for a specific role."""
        recommendations = {
            'query_role': query_role,
            'data_source': None,
            'similarity_score': None,
            'matched_role': None,
            'channels': {},
            'suggested_mix': {},
            'confidence': None,
            'explanation': None,
            'similar_roles': [],
            'role_category': None
        }
        
        # Try to categorize the input role
        categorized_role = self._extract_specific_role(query_role)
        recommendations['role_category'] = categorized_role
        
        # Find similar roles
        similar_roles = self.find_similar_roles(query_role)
        recommendations['similar_roles'] = similar_roles
        
        # Check for exact match or use most similar
        if query_role in self.role_stats:
            recommendations['data_source'] = 'exact'
            recommendations['matched_role'] = query_role
            recommendations['similarity_score'] = 1.0
            recommendations['confidence'] = 'Hög'
            role_data = self.role_stats[query_role]
        elif categorized_role in self.role_stats:
            recommendations['data_source'] = 'category'
            recommendations['matched_role'] = categorized_role
            recommendations['similarity_score'] = 0.9
            recommendations['confidence'] = 'Hög'
            recommendations['explanation'] = f"Kategoriserad som: {categorized_role}"
            role_data = self.role_stats[categorized_role]
        elif similar_roles and similar_roles[0][1] > 0.7:
            matched_role, similarity = similar_roles[0]
            recommendations['data_source'] = 'similar'
            recommendations['matched_role'] = matched_role
            recommendations['similarity_score'] = similarity
            
            if similarity > 0.85:
                recommendations['confidence'] = 'Hög'
            elif similarity > 0.75:
                recommendations['confidence'] = 'Medel'
            else:
                recommendations['confidence'] = 'Låg'
            
            recommendations['explanation'] = f"Baserat på liknande roll: {matched_role} ({similarity*100:.0f}% likhet)"
            role_data = self.role_stats[matched_role]
        else:
            recommendations['explanation'] = "Ingen tillräckligt liknande roll hittades"
            return recommendations
        
        # Calculate channel recommendations
        for platform, metrics in role_data.items():
            recommendations['channels'][platform] = {
                'ctr': round(metrics['ctr'], 2),
                'cpc': round(metrics['cpc'], 2),
                'avg_spend_per_campaign': round(metrics['avg_spend'], 0),
                'campaigns_run': metrics['campaigns'],
                'performance_score': self._calculate_performance_score(metrics)
            }
        
        # Calculate optimal mix
        recommendations['suggested_mix'] = self._calculate_optimal_mix(role_data)
        
        # Predict outcomes if budget provided
        if budget:
            recommendations['predicted_outcomes'] = self._predict_outcomes(
                role_data, budget, campaign_days, recommendations['suggested_mix']
            )
        
        return recommendations
    
    def _calculate_performance_score(self, metrics: Dict) -> float:
        """Calculate performance score."""
        ctr_score = min(metrics['ctr'] / 5 * 100, 100)
        cpc_score = max(0, 100 - (metrics['cpc'] / 50 * 100))
        return round(ctr_score * 0.6 + cpc_score * 0.4, 1)
    
    def _calculate_optimal_mix(self, role_data: Dict) -> Dict:
        """Calculate optimal channel mix."""
        if not role_data:
            return {}
        
        scores = {platform: self._calculate_performance_score(metrics) 
                 for platform, metrics in role_data.items()}
        
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
    
    def _predict_outcomes(self, role_data: Dict, budget: float, 
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
            if platform in role_data:
                platform_budget = budget * (percentage / 100)
                metrics = role_data[platform]
                
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
    
    def get_role_hierarchy(self) -> Dict:
        """Get categorized role hierarchy for display."""
        hierarchy = {
            'Ledning & Chef': [],
            'Tekniker & Service': [],
            'Försäljning': [],
            'Vård & Omsorg': [],
            'IT & Utveckling': [],
            'Ekonomi & Administration': [],
            'Bygg & Anläggning': [],
            'Lager & Logistik': [],
            'Övriga': []
        }
        
        for role in self.known_roles:
            if any(x in role for x in ['chef', 'Chef', 'VD', 'CEO', 'ledare']):
                hierarchy['Ledning & Chef'].append(role)
            elif any(x in role for x in ['tekniker', 'Tekniker', 'service', 'Service']):
                hierarchy['Tekniker & Service'].append(role)
            elif any(x in role for x in ['säljare', 'Säljare', 'Account', 'Sales']):
                hierarchy['Försäljning'].append(role)
            elif any(x in role for x in ['sköterska', 'Läkare', 'Vård', 'Omsorg']):
                hierarchy['Vård & Omsorg'].append(role)
            elif any(x in role for x in ['utvecklare', 'IT', 'System', 'Data', 'DevOps']):
                hierarchy['IT & Utveckling'].append(role)
            elif any(x in role for x in ['ekonom', 'Ekonom', 'Controller', 'Redovisning', 'Administratör']):
                hierarchy['Ekonomi & Administration'].append(role)
            elif any(x in role for x in ['Bygg', 'Snickare', 'Elektriker', 'Rörmontör']):
                hierarchy['Bygg & Anläggning'].append(role)
            elif any(x in role for x in ['Lager', 'Truck', 'Logistik', 'Terminal']):
                hierarchy['Lager & Logistik'].append(role)
            else:
                hierarchy['Övriga'].append(role)
        
        # Sort each category
        for category in hierarchy:
            hierarchy[category].sort()
        
        return hierarchy


# Example usage
if __name__ == "__main__":
    print("🚀 Initierar förbättrad rekommendationsmotor...")
    engine = EnhancedRecommendationEngine()
    
    print(f"\n📊 Laddat data för {len(engine.known_roles)} specifika roller")
    
    # Show role hierarchy
    hierarchy = engine.get_role_hierarchy()
    print("\n📋 Rollkategorier:")
    for category, roles in hierarchy.items():
        if roles:
            print(f"\n{category} ({len(roles)} roller):")
            for role in roles[:5]:
                print(f"  - {role}")
            if len(roles) > 5:
                print(f"  ... och {len(roles) - 5} till")
    
    # Test with specific role
    print("\n" + "="*60)
    print("TEST: Specifik chef-roll")
    print("="*60)
    result = engine.get_recommendations('Platschef inom bygg', budget=20000)
    print(f"Kategoriserad som: {result['role_category']}")
    print(f"Matchad roll: {result['matched_role']}")
    print(f"Konfidens: {result['confidence']}")
    if result['channels']:
        print("Rekommenderade kanaler:")
        for platform, metrics in result['channels'].items():
            print(f"  {platform}: {metrics['ctr']}% CTR, {metrics['cpc']} SEK CPC")
