"""
Test script for campaign name parser
"""

from campaign_parser import CampaignNameParser

def test_parser():
    """Test the campaign name parser with sample data"""
    
    parser = CampaignNameParser()
    
    # Test cases from your BigQuery data
    test_campaigns = [
        "LRF Media AB - Grafisk formgivare till LRF Media - Stockholm - Boost Plus (Tjänstemän) - Position ID: (63963) - SIMON [28941262453]",
        "Uppsala kommun - Fastighetsansvarig förskolan - Uppsala - Boost Plus: Utökad Radie - Position ID: (64261) - AGNES [28957252192]",
        "TioHundra AB - Vice VD/sjukhuschef till Norrtälje sjukhus - Norrtälje - Boost Plus - Web ID: () - AGNES [28944106526]",
        "Hertin / Mankert - Projektuthyrare till NCC Property Development - Stockholm - Stockholm - Boost Plus - Web ID: () - SIMON [28947715487]",
        "Chefspoolen i Sverige AB - Chef till enheten för socialjuridik - Stockholm - Boost Plus - Web ID: () - SIMON [29028085372]"
    ]
    
    print("🧪 Testing Campaign Name Parser\n")
    print("=" * 80)
    
    for i, campaign in enumerate(test_campaigns, 1):
        print(f"\n📋 Test Case {i}:")
        print(f"Campaign: {campaign}")
        print("-" * 60)
        
        result = parser.parse_campaign_name(campaign)
        
        print(f"✅ Company: {result['company']}")
        print(f"👔 Job Role: {result['job_role']}")
        print(f"📍 Location: {result['location']}")
        print(f"📦 Package: {result['package_type']}")
        print(f"🎯 Confidence: {result['confidence_score']:.2f}")
        
        if result['confidence_score'] < 0.6:
            print("⚠️  Low confidence - may need manual review")
    
    print("\n" + "=" * 80)
    print("✅ Parser testing complete!")

if __name__ == "__main__":
    test_parser()
