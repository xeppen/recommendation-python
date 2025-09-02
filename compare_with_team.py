#!/usr/bin/env python3
"""
Jämförelseverktyg för att utvärdera AI vs Team rekommendationer
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
from pathlib import Path

class RecommendationEvaluator:
    def __init__(self):
        # Ladda historisk data
        self.campaigns_df = pd.read_csv('data/processed/all_platforms_campaigns_complete.csv')
        self.results_file = Path('evaluation_results.json')
        self.load_results()
    
    def load_results(self):
        """Ladda tidigare testresultat"""
        if self.results_file.exists():
            with open(self.results_file, 'r') as f:
                self.results = json.load(f)
        else:
            self.results = []
    
    def save_results(self):
        """Spara testresultat"""
        with open(self.results_file, 'w') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
    
    def get_historical_performance(self, role, platform=None):
        """Hämta faktisk historisk prestanda för en roll"""
        role_data = self.campaigns_df[
            self.campaigns_df['Roll'].str.contains(role, case=False, na=False)
        ]
        
        if platform:
            role_data = role_data[role_data['Platform'] == platform]
        
        if role_data.empty:
            return None
        
        return {
            'campaigns': len(role_data),
            'avg_ctr': role_data['CTR_Percent'].mean(),
            'avg_cpc': role_data['CPC_SEK'].mean(),
            'avg_spend': role_data['Spend_SEK'].mean(),
            'platforms': role_data['Platform'].value_counts().to_dict(),
            'best_platform': role_data.groupby('Platform')['CTR_Percent'].mean().idxmax() if not role_data.empty else None
        }
    
    def evaluate_recommendation(self, role, ai_recommendation, team_recommendation):
        """Jämför AI och team rekommendationer mot historisk data"""
        historical = self.get_historical_performance(role)
        
        if not historical:
            print(f"⚠️ Ingen historisk data för {role}")
            return None
        
        evaluation = {
            'timestamp': datetime.now().isoformat(),
            'role': role,
            'historical': historical,
            'ai_recommendation': ai_recommendation,
            'team_recommendation': team_recommendation,
            'scores': {}
        }
        
        # Beräkna träffsäkerhet för plattformsval
        if historical['best_platform']:
            best_platform = historical['best_platform']
            
            # AI träffsäkerhet
            ai_platforms = ai_recommendation.get('platforms', [])
            ai_hit = 1.0 if best_platform in ai_platforms else 0.0
            
            # Team träffsäkerhet  
            team_platforms = team_recommendation.get('platforms', [])
            team_hit = 1.0 if best_platform in team_platforms else 0.0
            
            evaluation['scores']['platform_accuracy'] = {
                'ai': ai_hit,
                'team': team_hit,
                'best_historical': best_platform
            }
        
        # Jämför CTR-estimat
        if 'expected_ctr' in ai_recommendation and 'expected_ctr' in team_recommendation:
            actual_ctr = historical['avg_ctr']
            ai_ctr_error = abs(ai_recommendation['expected_ctr'] - actual_ctr) / actual_ctr
            team_ctr_error = abs(team_recommendation['expected_ctr'] - actual_ctr) / actual_ctr
            
            evaluation['scores']['ctr_accuracy'] = {
                'ai_error': ai_ctr_error,
                'team_error': team_ctr_error,
                'actual': actual_ctr
            }
        
        # Jämför CPC-estimat
        if 'expected_cpc' in ai_recommendation and 'expected_cpc' in team_recommendation:
            actual_cpc = historical['avg_cpc']
            ai_cpc_error = abs(ai_recommendation['expected_cpc'] - actual_cpc) / actual_cpc
            team_cpc_error = abs(team_recommendation['expected_cpc'] - actual_cpc) / actual_cpc
            
            evaluation['scores']['cpc_accuracy'] = {
                'ai_error': ai_cpc_error,
                'team_error': team_cpc_error,
                'actual': actual_cpc
            }
        
        # Spara resultat
        self.results.append(evaluation)
        self.save_results()
        
        return evaluation
    
    def print_evaluation(self, evaluation):
        """Skriv ut utvärdering på ett snyggt sätt"""
        if not evaluation:
            return
        
        print("\n" + "="*60)
        print(f"📊 UTVÄRDERING: {evaluation['role']}")
        print("="*60)
        
        print(f"\n📈 Historisk data ({evaluation['historical']['campaigns']} kampanjer):")
        print(f"  • Bästa plattform: {evaluation['historical']['best_platform']}")
        print(f"  • Genomsnittlig CTR: {evaluation['historical']['avg_ctr']:.2f}%")
        print(f"  • Genomsnittlig CPC: {evaluation['historical']['avg_cpc']:.2f} SEK")
        
        scores = evaluation['scores']
        
        if 'platform_accuracy' in scores:
            print(f"\n🎯 Plattformsträffsäkerhet:")
            pa = scores['platform_accuracy']
            print(f"  • AI: {'✅' if pa['ai'] == 1.0 else '❌'}")
            print(f"  • Team: {'✅' if pa['team'] == 1.0 else '❌'}")
        
        if 'ctr_accuracy' in scores:
            print(f"\n📊 CTR-estimat (lägre fel = bättre):")
            ca = scores['ctr_accuracy']
            print(f"  • AI fel: {ca['ai_error']*100:.1f}%")
            print(f"  • Team fel: {ca['team_error']*100:.1f}%")
            winner = "AI" if ca['ai_error'] < ca['team_error'] else "Team"
            print(f"  • Vinnare: {winner} 🏆")
        
        if 'cpc_accuracy' in scores:
            print(f"\n💰 CPC-estimat (lägre fel = bättre):")
            cpc = scores['cpc_accuracy']
            print(f"  • AI fel: {cpc['ai_error']*100:.1f}%")
            print(f"  • Team fel: {cpc['team_error']*100:.1f}%")
            winner = "AI" if cpc['ai_error'] < cpc['team_error'] else "Team"
            print(f"  • Vinnare: {winner} 🏆")
    
    def run_test_suite(self):
        """Kör en serie standardtester"""
        test_cases = [
            {
                'role': 'Sjuksköterska',
                'ai_recommendation': {
                    'platforms': ['Facebook', 'LinkedIn'],
                    'expected_ctr': 3.11,
                    'expected_cpc': 20.0
                },
                'team_recommendation': {
                    'platforms': ['Facebook'],
                    'expected_ctr': 2.8,
                    'expected_cpc': 18.0
                }
            },
            {
                'role': 'Utvecklare',
                'ai_recommendation': {
                    'platforms': ['LinkedIn', 'Facebook'],
                    'expected_ctr': 1.5,
                    'expected_cpc': 35.0
                },
                'team_recommendation': {
                    'platforms': ['LinkedIn'],
                    'expected_ctr': 1.8,
                    'expected_cpc': 40.0
                }
            }
        ]
        
        print("\n🧪 KÖRNING AV TESTSVIT")
        print("="*60)
        
        for test in test_cases:
            evaluation = self.evaluate_recommendation(
                test['role'],
                test['ai_recommendation'],
                test['team_recommendation']
            )
            self.print_evaluation(evaluation)
        
        self.print_summary()
    
    def print_summary(self):
        """Skriv ut sammanfattning av alla tester"""
        if not self.results:
            print("\nInga testresultat att visa")
            return
        
        print("\n" + "="*60)
        print("📊 SAMMANFATTNING AV ALLA TESTER")
        print("="*60)
        
        ai_wins = 0
        team_wins = 0
        
        for result in self.results:
            scores = result.get('scores', {})
            
            # Räkna vem som vinner på CTR
            if 'ctr_accuracy' in scores:
                if scores['ctr_accuracy']['ai_error'] < scores['ctr_accuracy']['team_error']:
                    ai_wins += 1
                else:
                    team_wins += 1
            
            # Räkna vem som vinner på CPC
            if 'cpc_accuracy' in scores:
                if scores['cpc_accuracy']['ai_error'] < scores['cpc_accuracy']['team_error']:
                    ai_wins += 1
                else:
                    team_wins += 1
        
        total_competitions = ai_wins + team_wins
        if total_competitions > 0:
            print(f"\n🏆 Totala vinster:")
            print(f"  • AI: {ai_wins}/{total_competitions} ({ai_wins/total_competitions*100:.1f}%)")
            print(f"  • Team: {team_wins}/{total_competitions} ({team_wins/total_competitions*100:.1f}%)")
        
        print(f"\n📝 Totalt antal tester: {len(self.results)}")

def main():
    """Huvudfunktion för att köra utvärdering"""
    evaluator = RecommendationEvaluator()
    
    print("🤖 REKOMMENDATIONSMOTOR UTVÄRDERING")
    print("="*60)
    print("\nVälj ett alternativ:")
    print("1. Kör standardtester")
    print("2. Mata in egen jämförelse")
    print("3. Visa tidigare resultat")
    
    choice = input("\nDitt val (1-3): ").strip()
    
    if choice == '1':
        evaluator.run_test_suite()
    
    elif choice == '2':
        role = input("\nAnge roll: ")
        
        print("\nAI:s rekommendation:")
        ai_platforms = input("  Plattformar (kommaseparerat): ").split(',')
        ai_ctr = float(input("  Förväntad CTR (%): "))
        ai_cpc = float(input("  Förväntad CPC (SEK): "))
        
        print("\nTeamets rekommendation:")
        team_platforms = input("  Plattformar (kommaseparerat): ").split(',')
        team_ctr = float(input("  Förväntad CTR (%): "))
        team_cpc = float(input("  Förväntad CPC (SEK): "))
        
        ai_rec = {
            'platforms': [p.strip() for p in ai_platforms],
            'expected_ctr': ai_ctr,
            'expected_cpc': ai_cpc
        }
        
        team_rec = {
            'platforms': [p.strip() for p in team_platforms],
            'expected_ctr': team_ctr,
            'expected_cpc': team_cpc
        }
        
        evaluation = evaluator.evaluate_recommendation(role, ai_rec, team_rec)
        evaluator.print_evaluation(evaluation)
    
    elif choice == '3':
        evaluator.print_summary()
    
    else:
        print("Ogiltigt val")

if __name__ == "__main__":
    main()
