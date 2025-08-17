#!/usr/bin/env python3
"""
Create sample user data for WingmanMatch buddy matching functionality testing
Generates 5 sample users in SF Bay Area with realistic data following existing schema patterns
"""

import uuid
import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone

# Import the existing database factory
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database import SupabaseFactory

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample user data with SF Bay Area locations (as requested)
SAMPLE_USERS = [
    {
        "id": str(uuid.uuid4()),
        "email": "alex.chen@example.com",
        "first_name": "Alex",
        "last_name": "Chen",
        "bio": "Software engineer looking to build confidence in social situations. Love hiking and board games.",
        "experience_level": "beginner",
        "confidence_archetype": "Analyzer",
        "location": {
            "lat": 37.7749,
            "lng": -122.4194,
            "city": "San Francisco",
            "max_travel_miles": 25,
            "privacy_mode": "precise"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "email": "marcus.johnson@example.com", 
        "first_name": "Marcus",
        "last_name": "Johnson",
        "bio": "Marketing professional who wants to improve dating confidence. Enjoys cooking and live music.",
        "experience_level": "intermediate",
        "confidence_archetype": "Naturalist", 
        "location": {
            "lat": 37.8044,
            "lng": -122.2712,
            "city": "Oakland",
            "max_travel_miles": 20,
            "privacy_mode": "precise"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "email": "david.kim@example.com",
        "first_name": "David", 
        "last_name": "Kim",
        "bio": "Tech startup founder working on social anxiety. Love coffee shops and weekend road trips.",
        "experience_level": "beginner",
        "confidence_archetype": "Scholar",
        "location": {
            "lat": 37.3382,
            "lng": -122.0922,
            "city": "San Jose", 
            "max_travel_miles": 30,
            "privacy_mode": "city_only"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "email": "ryan.patel@example.com",
        "first_name": "Ryan",
        "last_name": "Patel", 
        "bio": "Graduate student learning to approach dating authentically. Into rock climbing and indie films.",
        "experience_level": "intermediate",
        "confidence_archetype": "Sprinter",
        "location": {
            "lat": 37.8715,
            "lng": -122.2730,
            "city": "Berkeley",
            "max_travel_miles": 15,
            "privacy_mode": "precise"
        }
    },
    {
        "id": str(uuid.uuid4()),
        "email": "james.nguyen@example.com",
        "first_name": "James",
        "last_name": "Nguyen",
        "bio": "Product manager seeking to build genuine connections. Passionate about photography and travel.",
        "experience_level": "advanced",
        "confidence_archetype": "Protector",
        "location": {
            "lat": 37.4419,
            "lng": -122.1430,
            "city": "Palo Alto",
            "max_travel_miles": 35,
            "privacy_mode": "precise"
        }
    }
]

async def check_existing_users() -> List[Dict[str, Any]]:
    """Check if any users already exist in the database"""
    try:
        client = SupabaseFactory.get_service_client()
        result = client.table('user_profiles').select('id, email').execute()
        return result.data
    except Exception as e:
        logger.error(f"Error checking existing users: {e}")
        return []

async def create_user_profile(user_data: Dict[str, Any]) -> bool:
    """Create a user profile in the user_profiles table"""
    try:
        client = SupabaseFactory.get_service_client()
        
        profile_data = {
            "id": user_data["id"],
            "email": user_data["email"],
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"], 
            "bio": user_data["bio"],
            "experience_level": user_data["experience_level"],
            "confidence_archetype": user_data["confidence_archetype"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = client.table('user_profiles').insert(profile_data).execute()
        
        if result.data:
            logger.info(f"Created user profile: {user_data['first_name']} {user_data['last_name']} ({user_data['email']})")
            return True
        else:
            logger.error(f"Failed to create user profile for {user_data['email']}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating user profile for {user_data['email']}: {e}")
        return False

async def create_user_location(user_data: Dict[str, Any]) -> bool:
    """Create a user location in the user_locations table"""
    try:
        client = SupabaseFactory.get_service_client()
        
        location = user_data["location"]
        location_data = {
            "user_id": user_data["id"],
            "max_travel_miles": location["max_travel_miles"],
            "privacy_mode": location["privacy_mode"],
            "city": location["city"],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Handle privacy mode for coordinates
        if location["privacy_mode"] == "precise":
            location_data["lat"] = location["lat"]
            location_data["lng"] = location["lng"] 
        else:
            # City-only mode: store placeholder coordinates
            location_data["lat"] = 0.0
            location_data["lng"] = 0.0
            
        result = client.table('user_locations').insert(location_data).execute()
        
        if result.data:
            privacy_info = f"precise coords" if location["privacy_mode"] == "precise" else "city-only"
            logger.info(f"Created user location: {location['city']} ({privacy_info}) for {user_data['first_name']}")
            return True
        else:
            logger.error(f"Failed to create user location for {user_data['email']}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating user location for {user_data['email']}: {e}")
        return False

async def create_sample_users():
    """Create all sample users with their profiles and locations"""
    
    logger.info("Starting sample user creation for buddy matching tests...")
    
    # Check existing users first
    existing_users = await check_existing_users()
    if existing_users:
        logger.info(f"Found {len(existing_users)} existing users in database:")
        for user in existing_users:
            logger.info(f"  - {user['email']} ({user['id']})")
        
        # Check if running interactively
        import sys
        if sys.stdin.isatty():
            response = input("\nDo you want to continue adding sample users? (y/n): ")
            if response.lower() != 'y':
                logger.info("Sample user creation cancelled")
                return
        else:
            logger.info("Running in non-interactive mode, proceeding with sample user creation...")
    
    successful_profiles = 0
    successful_locations = 0
    
    for i, user_data in enumerate(SAMPLE_USERS, 1):
        logger.info(f"\nCreating user {i}/{len(SAMPLE_USERS)}: {user_data['first_name']} {user_data['last_name']}")
        
        # Create user profile
        if await create_user_profile(user_data):
            successful_profiles += 1
            
            # Create user location
            if await create_user_location(user_data):
                successful_locations += 1
            else:
                logger.warning(f"User profile created but location failed for {user_data['email']}")
        else:
            logger.error(f"Failed to create user profile for {user_data['email']}")
    
    logger.info(f"\n=== Sample User Creation Complete ===")
    logger.info(f"Profiles created: {successful_profiles}/{len(SAMPLE_USERS)}")
    logger.info(f"Locations created: {successful_locations}/{len(SAMPLE_USERS)}")
    
    if successful_profiles > 0:
        logger.info(f"\n✅ Sample users ready for buddy matching tests!")
        logger.info(f"Users are located in: San Francisco, Oakland, San Jose, Berkeley, Palo Alto")
        logger.info(f"Experience levels: {set(user['experience_level'] for user in SAMPLE_USERS)}")
        logger.info(f"Confidence archetypes: {set(user['confidence_archetype'] for user in SAMPLE_USERS)}")
    
    return successful_profiles, successful_locations

async def verify_sample_data():
    """Verify that sample data was created correctly"""
    try:
        client = SupabaseFactory.get_service_client()
        
        # Check user profiles
        profiles_result = client.table('user_profiles')\
            .select('id, first_name, last_name, email, experience_level, confidence_archetype')\
            .execute()
        
        # Check user locations
        locations_result = client.table('user_locations')\
            .select('user_id, city, lat, lng, max_travel_miles, privacy_mode')\
            .execute()
            
        logger.info(f"\n=== Database Verification ===")
        logger.info(f"User profiles in database: {len(profiles_result.data)}")
        logger.info(f"User locations in database: {len(locations_result.data)}")
        
        if profiles_result.data:
            logger.info("\nUser Profiles:")
            for profile in profiles_result.data:
                logger.info(f"  - {profile['first_name']} {profile['last_name']}: {profile['experience_level']}, {profile['confidence_archetype']}")
                
        if locations_result.data:
            logger.info("\nUser Locations:")
            for location in locations_result.data:
                coord_info = f"({location['lat']}, {location['lng']})" if location['lat'] != 0 else "city-only"
                logger.info(f"  - {location['city']}: {coord_info}, {location['max_travel_miles']} miles, {location['privacy_mode']}")
        
        return len(profiles_result.data), len(locations_result.data)
        
    except Exception as e:
        logger.error(f"Error verifying sample data: {e}")
        return 0, 0

async def test_buddy_matching_endpoint(test_user_id: str):
    """Test the buddy matching endpoint with a sample user"""
    try:
        logger.info(f"\n=== Testing Buddy Matching Endpoint ===")
        logger.info(f"Testing with user ID: {test_user_id}")
        
        # We'll use the existing distance calculation module
        from src.db.distance import find_candidates_within_radius
        
        # Test with different radius values
        for radius in [15, 25, 50]:
            logger.info(f"\nTesting radius: {radius} miles")
            candidates = await find_candidates_within_radius(test_user_id, radius)
            
            logger.info(f"Found {len(candidates)} candidates within {radius} miles:")
            for candidate in candidates:
                logger.info(f"  - User {candidate.user_id}: {candidate.city} "
                          f"({candidate.distance_miles:.1f} miles away) "
                          f"- {candidate.experience_level}, {candidate.confidence_archetype}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing buddy matching endpoint: {e}")
        return False

if __name__ == "__main__":
    async def main():
        try:
            # Create sample users
            profiles_created, locations_created = await create_sample_users()
            
            if profiles_created > 0:
                # Verify the data
                await verify_sample_data()
                
                # Test buddy matching with the first user
                if SAMPLE_USERS:
                    first_user_id = SAMPLE_USERS[0]["id"]
                    await test_buddy_matching_endpoint(first_user_id)
                    
                logger.info(f"\n🎯 Sample data creation complete! Ready for buddy matching tests.")
                logger.info(f"Use any of these user IDs to test the matching API:")
                for user in SAMPLE_USERS[:profiles_created]:
                    logger.info(f"  - {user['first_name']} ({user['location']['city']}): {user['id']}")
            else:
                logger.error("No sample users were created successfully")
                
        except Exception as e:
            logger.error(f"Error in main execution: {e}")
    
    # Run the async main function
    asyncio.run(main())