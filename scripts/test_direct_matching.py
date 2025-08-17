#!/usr/bin/env python3
"""
Direct test of buddy matching without going through the async API
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database import SupabaseFactory
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_direct_matching():
    """Test buddy matching logic directly"""
    
    client = SupabaseFactory.get_service_client()
    user_id = "186e9cab-ff37-4a8e-b750-8160565096b7"  # Alex
    radius_miles = 35
    
    print(f"=== Testing Direct Matching for User {user_id} ===")
    
    # Step 1: Get user's location
    print("Step 1: Getting user location...")
    user_location = client.table('user_locations')\
        .select('lat, lng, city')\
        .eq('user_id', user_id)\
        .execute()
    
    if not user_location.data:
        print("ERROR: No location found for user")
        return
    
    user_lat = user_location.data[0]['lat']
    user_lng = user_location.data[0]['lng']
    user_city = user_location.data[0]['city']
    
    print(f"User location: {user_city} ({user_lat}, {user_lng})")
    
    if not user_lat or not user_lng or user_lat == 0 or user_lng == 0:
        print(f"ERROR: User has incomplete location data: lat={user_lat}, lng={user_lng}")
        return
    
    # Step 2: Query other users
    print("\nStep 2: Querying other users...")
    try:
        all_locations = client.table('user_locations')\
            .select('user_id, lat, lng, city, user_profiles!inner(experience_level, confidence_archetype)')\
            .neq('user_id', user_id)\
            .execute()
        
        print(f"Query returned {len(all_locations.data)} total locations")
        
        # Step 3: Process candidates
        print("\nStep 3: Processing candidates...")
        candidates = []
        processed_count = 0
        skipped_incomplete = 0
        skipped_city_only = 0
        
        for i, location in enumerate(all_locations.data):
            processed_count += 1
            
            print(f"\nProcessing location {i+1}/{len(all_locations.data)}:")
            print(f"  User ID: {location['user_id']}")
            print(f"  City: {location['city']}")
            print(f"  Coordinates: ({location['lat']}, {location['lng']})")
            print(f"  Profile: {location['user_profiles']}")
            
            # Skip users with incomplete profiles
            profile = location['user_profiles']
            if not profile.get('experience_level') or not profile.get('confidence_archetype'):
                skipped_incomplete += 1
                print(f"  → SKIPPED: Incomplete profile")
                continue
            
            # Skip users with placeholder coordinates (0,0) - city-only mode
            if float(location['lat']) == 0.0 and float(location['lng']) == 0.0:
                skipped_city_only += 1
                print(f"  → SKIPPED: City-only mode (0,0 coordinates)")
                continue
            
            # Calculate distance
            lat_diff = abs(float(user_lat) - float(location['lat']))
            lng_diff = abs(float(user_lng) - float(location['lng']))
            
            # Rough distance approximation: 1 degree ≈ 69 miles
            distance_miles = ((lat_diff * 69) ** 2 + (lng_diff * 69) ** 2) ** 0.5
            
            print(f"  → Distance: {distance_miles:.1f} miles")
            
            if distance_miles <= radius_miles:
                candidates.append({
                    'user_id': location['user_id'],
                    'city': location['city'],
                    'distance_miles': round(distance_miles, 1),
                    'experience_level': profile['experience_level'],
                    'confidence_archetype': profile['confidence_archetype']
                })
                print(f"  → ADDED: Within {radius_miles} mile radius!")
            else:
                print(f"  → Outside {radius_miles} mile radius")
        
        print(f"\n=== SUMMARY ===")
        print(f"Processed {processed_count} locations")
        print(f"Skipped {skipped_incomplete} incomplete profiles") 
        print(f"Skipped {skipped_city_only} city-only users")
        print(f"Found {len(candidates)} candidates within {radius_miles} miles")
        
        if candidates:
            print(f"\n=== CANDIDATES ===")
            candidates.sort(key=lambda c: c['distance_miles'])
            for candidate in candidates:
                print(f"  - {candidate['city']}: {candidate['distance_miles']} miles")
                print(f"    Experience: {candidate['experience_level']}, Archetype: {candidate['confidence_archetype']}")
                
    except Exception as e:
        print(f"ERROR in query: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_matching()