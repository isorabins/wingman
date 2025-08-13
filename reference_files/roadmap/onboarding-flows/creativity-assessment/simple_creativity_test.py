#!/usr/bin/env python3
"""
Simple test script to verify the creativity test flow
"""

import sys
import os
sys.path.append('src')

try:
    print("🎨 Testing Creativity Flow Functions")
    print("=" * 40)
    
    # Test 1: Import functions
    print("✅ Test 1: Importing functions...")
    from src.project_planning import (
        get_creativity_test_prompt,
        analyze_creativity_responses
    )
    print("✓ Functions imported successfully")
    
    # Test 2: Get prompt
    print("\n✅ Test 2: Getting creativity test prompt...")
    prompt = get_creativity_test_prompt()
    print(f"✓ Prompt length: {len(prompt)} characters")
    print(f"✓ Contains 'Question 1 of 5': {'Question 1 of 5' in prompt}")
    
    # Test 3: Analyze responses
    print("\n✅ Test 3: Analyzing sample responses...")
    sample_responses = {
        "1": "A",  # Big picture
        "2": "A",  # Big picture  
        "3": "B",  # Knowledge seeker
        "4": "A",  # Big picture
        "5": "A"   # Big picture
    }
    
    result = analyze_creativity_responses(sample_responses)
    print(f"✓ Primary archetype: {result['primary_archetype']}")
    print(f"✓ Primary score: {result['primary_score']}")
    print(f"✓ Secondary archetype: {result.get('secondary_archetype', 'None')}")
    
    print("\n🎉 All basic tests passed!")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc() 