#!/usr/bin/env python3
"""
AI-driven insights generator for channel recommendations
"""

import openai
import pandas as pd
from typing import Dict, List, Any
import streamlit as st

class AIInsightsGenerator:
    """Generate human-readable insights for channel recommendations"""
    
    def __init__(self, api_key: str = None):
        """Initialize with OpenAI API key"""
        self.api_key = api_key or st.secrets.get("OPENAI_API_KEY", "")
        if self.api_key:
            openai.api_key = self.api_key
    
    def generate_channel_insights(self, 
                                 role: str, 
                                 channel_data: pd.DataFrame,
                                 historical_performance: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate AI insights for why certain channels are recommended
        
        Args:
            role: Job role
            channel_data: DataFrame with channel performance metrics
            historical_performance: Historical data for the role
            
        Returns:
            Dictionary with insights per channel
        """
        insights = {}
        
        for _, row in channel_data.iterrows():
            channel = row['Platform']
            ctr = row.get('CTR', 0)
            cpc = row.get('CPC', 0)
            
            # Generate contextual insights
            insight = self._generate_single_insight(
                role, channel, ctr, cpc, historical_performance
            )
            insights[channel] = insight
        
        return insights
    
    def _generate_single_insight(self, 
                                role: str, 
                                channel: str, 
                                ctr: float, 
                                cpc: float,
                                historical: Dict) -> str:
        """Generate insight for a single channel"""
        
        # Rule-based insights (fallback if no API key)
        if not self.api_key:
            return self._generate_rule_based_insight(role, channel, ctr, cpc, historical)
        
        # AI-powered insights
        try:
            prompt = f"""
            Analysera varför {channel} rekommenderas för rollen {role}.
            
            Data:
            - CTR: {ctr:.2f}%
            - CPC: {cpc:.2f} SEK
            - Historiska kampanjer: {historical.get('campaign_count', 0)}
            
            Ge en kort, konkret förklaring (max 2 meningar) på svenska om:
            1. Varför denna kanal fungerar för denna roll
            2. En specifik insikt eller rekommendation
            
            Fokusera på praktiska, handlingsbara insikter.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Du är en expert på digital marknadsföring och rekrytering."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback to rule-based if API fails
            return self._generate_rule_based_insight(role, channel, ctr, cpc, historical)
    
    def _generate_rule_based_insight(self, 
                                    role: str, 
                                    channel: str, 
                                    ctr: float, 
                                    cpc: float,
                                    historical: Dict) -> str:
        """Generate rule-based insights without AI"""
        
        insights = []
        
        # CTR-baserade insikter
        if ctr > 3.0:
            insights.append(f"Mycket hög engagemang ({ctr:.1f}% CTR)")
        elif ctr > 2.0:
            insights.append(f"Bra engagemang ({ctr:.1f}% CTR)")
        elif ctr < 1.0:
            insights.append(f"Låg engagemang ({ctr:.1f}% CTR)")
        
        # CPC-baserade insikter
        if cpc < 20:
            insights.append(f"Kostnadseffektiv ({cpc:.0f} kr/klick)")
        elif cpc > 40:
            insights.append(f"Högre kostnad ({cpc:.0f} kr/klick)")
        
        # Kanalspecifika insikter
        channel_insights = {
            'Facebook': {
                'Sjuksköterska': "Sjukvårdspersonal är mycket aktiva på Facebook",
                'Säljare': "B2C-säljare når bred målgrupp här",
                'default': "Bred räckvidd för de flesta yrkesgrupper"
            },
            'LinkedIn': {
                'Utvecklare': "IT-proffs nätverkar aktivt på LinkedIn",
                'Chef': "Beslutsfattare och ledare är mest aktiva här",
                'Ingenjör': "Tekniska roller har hög närvaro",
                'default': "Professionellt nätverk för kvalificerade roller"
            },
            'Snapchat': {
                'default': "Yngre målgrupp, bra för entry-level roller"
            },
            'TikTok': {
                'default': "Växande plattform för kreativa roller"
            }
        }
        
        # Lägg till kanalspecifik insikt
        channel_dict = channel_insights.get(channel, {})
        specific_insight = channel_dict.get(role, channel_dict.get('default', ''))
        if specific_insight:
            insights.append(specific_insight)
        
        # Databaserade insikter
        campaign_count = historical.get('campaign_count', 0)
        if campaign_count < 5:
            insights.append(f"Begränsad data ({campaign_count} kampanjer)")
        elif campaign_count > 20:
            insights.append(f"Väl testad ({campaign_count} kampanjer)")
        
        return " • ".join(insights) if insights else "Standardrekommendation baserad på liknande roller"
    
    def generate_comparison_insights(self, 
                                    channels: List[Dict[str, Any]]) -> str:
        """Generate insights comparing multiple channels"""
        
        if len(channels) < 2:
            return ""
        
        # Sortera efter CTR
        sorted_channels = sorted(channels, key=lambda x: x.get('ctr', 0), reverse=True)
        
        best = sorted_channels[0]
        worst = sorted_channels[-1]
        
        insights = []
        
        # Jämför bästa och sämsta
        if best['ctr'] > worst['ctr'] * 1.5:
            insights.append(
                f"{best['channel']} har {best['ctr']/worst['ctr']:.1f}x "
                f"högre engagemang än {worst['channel']}"
            )
        
        # Kostnadsjämförelse
        cheapest = min(channels, key=lambda x: x.get('cpc', float('inf')))
        most_expensive = max(channels, key=lambda x: x.get('cpc', 0))
        
        if most_expensive['cpc'] > cheapest['cpc'] * 1.5:
            insights.append(
                f"{cheapest['channel']} är {most_expensive['cpc']/cheapest['cpc']:.1f}x "
                f"mer kostnadseffektiv än {most_expensive['channel']}"
            )
        
        return " | ".join(insights)
    
    def generate_optimization_tips(self, 
                                  role: str, 
                                  selected_channels: List[str]) -> List[str]:
        """Generate optimization tips for the campaign"""
        
        tips = []
        
        # Rollspecifika tips
        role_tips = {
            'Sjuksköterska': [
                "Publicera på kvällar och helger när sjukvårdspersonal är lediga",
                "Framhäv work-life balance och flexibilitet"
            ],
            'Utvecklare': [
                "Fokusera på tech-stack och utvecklingsmöjligheter",
                "Publicera tis-tors kl 9-11 för bäst resultat"
            ],
            'Säljare': [
                "Betona provisionsmöjligheter och karriärvägar",
                "Använd video för att visa företagskulturen"
            ]
        }
        
        tips.extend(role_tips.get(role, ["Testa olika budskap för att hitta vad som resonerar"]))
        
        # Kanalspecifika tips
        if 'LinkedIn' in selected_channels:
            tips.append("LinkedIn: Använd Sponsored InMail för direktkontakt")
        if 'Facebook' in selected_channels:
            tips.append("Facebook: Testa både feed och stories för maximal räckvidd")
        if 'TikTok' in selected_channels:
            tips.append("TikTok: Skapa autentiskt content som visar arbetsmiljön")
        
        return tips[:3]  # Max 3 tips
