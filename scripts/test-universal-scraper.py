#!/usr/bin/env python3
"""
Test script for the universal scraper configuration
Tests specific sources to validate selectors and strategies
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.universal_scraper import UniversalScraper
import json

def test_priority_sources():
    """Test the 3 priority sources mentioned in the requirements"""
    priority_sources = [
        'hoco_council_granicus',
        'hcpss_board_calendar', 
        'hcls_events'
    ]
    
    print("🧪 Testing Priority Sources for Howard County Newsletter")
    print("=" * 60)
    
    scraper = UniversalScraper()
    
    for source_id in priority_sources:
        print(f"\n📋 Testing source: {source_id}")
        print("-" * 40)
        
        try:
            results = scraper.scrape_all_sources([source_id])
            
            if results['sources_scraped']:
                source_result = results['sources_scraped'][0]
                
                if source_result['status'] == 'success':
                    print(f"✅ SUCCESS: Found {source_result['items_found']} items")
                    
                    # Show sample items
                    for i, item in enumerate(source_result.get('items', [])[:2]):
                        print(f"   Sample {i+1}: {item.get('title', 'No title')[:60]}...")
                        
                else:
                    print(f"❌ FAILED: {source_result.get('error', 'Unknown error')}")
                    
            if results['errors']:
                for error in results['errors']:
                    print(f"🚨 Error: {error['error']}")
                    
        except Exception as e:
            print(f"💥 EXCEPTION: {str(e)}")
    
    print(f"\n📊 Test Complete")
    print("=" * 60)

def test_selector_validation():
    """Test if selectors are finding elements on pages"""
    print("\n🔍 Testing Selector Validation")
    print("-" * 40)
    
    scraper = UniversalScraper()
    
    # Test one HTML list source
    test_sources = ['hoco_health_news', 'hoco_police_news']
    
    for source_id in test_sources:
        print(f"\n🎯 Testing selectors for: {source_id}")
        
        source_config = None
        for src in scraper.config.get('sources', []):
            if src['id'] == source_id:
                source_config = src
                break
        
        if not source_config:
            print(f"❌ Source {source_id} not found in config")
            continue
        
        try:
            results = scraper.scrape_all_sources([source_id])
            
            if results['sources_scraped']:
                result = results['sources_scraped'][0]
                
                if result['items_found'] > 0:
                    print(f"✅ Selectors working: {result['items_found']} items found")
                else:
                    print("⚠️ No items found - selectors may need adjustment")
                    print(f"   Check debug HTML in data/universal/debug/")
                    
        except Exception as e:
            print(f"❌ Error testing {source_id}: {e}")

if __name__ == "__main__":
    # Test priority sources
    test_priority_sources()
    
    # Test selector validation
    test_selector_validation()
    
    print(f"\n🎉 All tests completed!")
    print(f"Check data/universal/ for output files")
    print(f"Check logs/ for detailed logs")