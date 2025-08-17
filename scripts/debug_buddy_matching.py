#!/usr/bin/env python3
"""
Debug script to check buddy matching functionality with sample data
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database import SupabaseFactory
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_buddy_matching():
    """Debug buddy matching by checking database state"""
    
    client = SupabaseFactory.get_service_client()
    
    # Get all user profiles with sample data
    print("=== User Profiles ===")
    profiles = client.table('user_profiles')\
        .select('id, first_name, last_name, email, experience_level, confidence_archetype')\
        .like('email', '%@example.com')\
        .execute()
    
    for profile in profiles.data:
        print(f"{profile['first_name']} {profile['last_name']}: {profile['experience_level']}, {profile['confidence_archetype']}")
        print(f"  ID: {profile['id']}")
        print(f"  Email: {profile['email']}")
    
    print(f"\nTotal sample profiles: {len(profiles.data)}")
    
    # Get all user locations for sample data
    print("\n=== User Locations ===")
    locations = client.table('user_locations')\
        .select('user_id, city, lat, lng, max_travel_miles, privacy_mode')\
        .in_('user_id', [p['id'] for p in profiles.data])\
        .execute()
    
    for location in locations.data:
        coords = f"({location['lat']}, {location['lng']})" if location['lat'] != 0 else "city-only"
        print(f"{location['city']}: {coords}, {location['max_travel_miles']} miles, {location['privacy_mode']}")
        print(f"  User ID: {location['user_id']}")
    
    print(f"\nTotal sample locations: {len(locations.data)}")
    
    if profiles.data and locations.data:
        # Find a user with location data (Alex)
        test_user_profile = None
        for profile in profiles.data:
            if any(loc['user_id'] == profile['id'] for loc in locations.data):
                if profile['first_name'] != 'User':  # Skip test users
                    test_user_profile = profile
                    break
        
        if not test_user_profile:
            print("No valid test user found with location data")
            return
            
        test_user_id = test_user_profile['id']
        test_user_name = f"{test_user_profile['first_name']} {test_user_profile['last_name']}"
        
        print(f"\n=== Testing Buddy Matching for {test_user_name} ===")
        print(f"Test User ID: {test_user_id}")
        
        # Get this user's location
        user_location = [loc for loc in locations.data if loc['user_id'] == test_user_id][0]
        print(f"User Location: {user_location['city']} ({user_location['lat']}, {user_location['lng']})")
        
        # Manual distance calculation to other users
        print(f"\nManual distance calculations:")
        for loc in locations.data:
            if loc['user_id'] != test_user_id:
                user_profile = next(p for p in profiles.data if p['id'] == loc['user_id'])
                
                if user_location['lat'] != 0 and user_location['lng'] != 0 and loc['lat'] != 0 and loc['lng'] != 0:
                    # Calculate distance
                    lat_diff = abs(float(user_location['lat']) - float(loc['lat']))
                    lng_diff = abs(float(user_location['lng']) - float(loc['lng']))
                    distance_miles = ((lat_diff * 69) ** 2 + (lng_diff * 69) ** 2) ** 0.5
                    
                    print(f"  {user_profile['first_name']} in {loc['city']}: {distance_miles:.1f} miles")
                else:
                    print(f"  {user_profile['first_name']} in {loc['city']}: city-only mode, cannot calculate precise distance")
        
        # Test the actual API query
        print(f"\n=== Testing Database Query ===")
        try:
            all_locations = client.table('user_locations')\
                .select('user_id, lat, lng, city, user_profiles!inner(experience_level, confidence_archetype)')\
                .neq('user_id', test_user_id)\
                .execute()
            
            print(f"Query returned {len(all_locations.data)} locations")
            
            # Filter out null coordinates
            valid_locations = [loc for loc in all_locations.data 
                             if loc['lat'] is not None and loc['lng'] is not None 
                             and loc['lat'] != 0 and loc['lng'] != 0]
            
            print(f"Valid locations with precise coordinates: {len(valid_locations)}")
            
            for loc in valid_locations:
                lat_diff = abs(float(user_location['lat']) - float(loc['lat']))
                lng_diff = abs(float(user_location['lng']) - float(loc['lng']))
                distance_miles = ((lat_diff * 69) ** 2 + (lng_diff * 69) ** 2) ** 0.5
                print(f"  {loc['city']}: {distance_miles:.1f} miles - {loc['user_profiles']['experience_level']}, {loc['user_profiles']['confidence_archetype']}")
                
        except Exception as e:
            print(f"Database query error: {e}")

if __name__ == "__main__":
    debug_buddy_matching()