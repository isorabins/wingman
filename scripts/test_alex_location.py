#!/usr/bin/env python3
"""
Test Alex's location data to debug buddy matching
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database import SupabaseFactory

def test_alex_location():
    client = SupabaseFactory.get_service_client()
    
    alex_id = "186e9cab-ff37-4a8e-b750-8160565096b7"
    
    # Get Alex's location
    result = client.table('user_locations')\
        .select('*')\
        .eq('user_id', alex_id)\
        .execute()
    
    print(f"Alex's location data:")
    if result.data:
        location = result.data[0]
        for key, value in location.items():
            print(f"  {key}: {value}")
    else:
        print("  No location data found!")
    
    # Get Alex's profile
    profile_result = client.table('user_profiles')\
        .select('*')\
        .eq('id', alex_id)\
        .execute()
    
    print(f"\nAlex's profile data:")
    if profile_result.data:
        profile = profile_result.data[0]
        for key, value in profile.items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    test_alex_location()