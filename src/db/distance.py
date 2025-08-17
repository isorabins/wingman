"""
Simple distance calculation utilities for WingmanMatch buddy matching
Just checks if users are within 20 miles of each other based on static locations
"""

import logging
from typing import List, Optional
from dataclasses import dataclass

from src.database import SupabaseFactory

logger = logging.getLogger(__name__)

@dataclass
class BuddyCandidate:
    """Simple buddy candidate within travel radius"""
    user_id: str
    city: str
    distance_miles: float
    experience_level: str
    confidence_archetype: str

async def find_candidates_within_radius(
    user_id: str,
    radius_miles: int = 20
) -> List[BuddyCandidate]:
    """
    Find buddy candidates within specified radius of user's location
    
    Args:
        user_id: User looking for buddies
        radius_miles: Maximum distance in miles (default 20)
        
    Returns:
        List of BuddyCandidate objects
    """
    try:
        client = SupabaseFactory.get_service_client()
        
        # Get user's location first
        user_location = client.table('user_locations')\
            .select('lat, lng, city')\
            .eq('user_id', user_id)\
            .execute()
        
        if not user_location.data:
            logger.warning(f"No location found for user {user_id}")
            return []
        
        user_lat = user_location.data[0]['lat']
        user_lng = user_location.data[0]['lng']
        user_city = user_location.data[0]['city']
        
        if not user_lat or not user_lng or user_lat == 0 or user_lng == 0:
            logger.warning(f"User {user_id} has incomplete location data: lat={user_lat}, lng={user_lng}")
            return []
        
        # Find other users and calculate distances using the existing haversine_miles function
        query = f"""
        SELECT 
            ul.user_id,
            ul.city,
            up.experience_level,
            up.confidence_archetype,
            public.haversine_miles({user_lat}, {user_lng}, ul.lat, ul.lng) as distance_miles
        FROM public.user_locations ul
        JOIN public.user_profiles up ON ul.user_id = up.id
        WHERE 
            ul.user_id != '{user_id}'
            AND ul.lat IS NOT NULL 
            AND ul.lng IS NOT NULL
            AND up.experience_level IS NOT NULL
            AND up.confidence_archetype IS NOT NULL
            AND public.haversine_miles({user_lat}, {user_lng}, ul.lat, ul.lng) <= {radius_miles}
        ORDER BY distance_miles ASC
        LIMIT 10
        """
        
        # Try to execute the query - if it fails, fall back to simple approach
        try:
            # Use a simple table query since we can't easily execute raw SQL
            all_locations = client.table('user_locations')\
                .select('user_id, lat, lng, city, user_profiles!inner(experience_level, confidence_archetype)')\
                .neq('user_id', user_id)\
                .execute()
            
            logger.info(f"Query returned {len(all_locations.data)} total locations")
            
            candidates = []
            
            for location in all_locations.data:
                # Skip users with incomplete profiles
                profile = location['user_profiles']
                if not profile.get('experience_level') or not profile.get('confidence_archetype'):
                    continue
                
                # Skip users with placeholder coordinates (0,0) - city-only mode
                if float(location['lat']) == 0.0 and float(location['lng']) == 0.0:
                    continue
                
                # Simple distance calculation (approximate)
                lat_diff = abs(float(user_lat) - float(location['lat']))
                lng_diff = abs(float(user_lng) - float(location['lng']))
                
                # Rough distance approximation: 1 degree ≈ 69 miles
                distance_miles = ((lat_diff * 69) ** 2 + (lng_diff * 69) ** 2) ** 0.5
                
                if distance_miles <= radius_miles:
                    candidates.append(BuddyCandidate(
                        user_id=location['user_id'],
                        city=location['city'] or 'Unknown',
                        distance_miles=round(distance_miles, 1),
                        experience_level=profile['experience_level'],
                        confidence_archetype=profile['confidence_archetype']
                    ))
            
            # Sort by distance and return
            candidates.sort(key=lambda c: c.distance_miles)
            logger.info(f"Found {len(candidates)} candidates within {radius_miles} miles of {user_city}")
            return candidates[:10]  # Limit to 10 candidates
            
        except Exception as query_error:
            logger.error(f"Database query failed: {query_error}")
            return []
        
    except Exception as e:
        logger.error(f"Error finding candidates for user {user_id}: {e}")
        return []

async def get_distance_between_users(user1_id: str, user2_id: str) -> Optional[float]:
    """
    Calculate distance between two users
    
    Args:
        user1_id: First user ID
        user2_id: Second user ID
        
    Returns:
        Distance in miles or None if error
    """
    try:
        client = SupabaseFactory.get_service_client()
        
        # Get both user locations
        locations = client.table('user_locations')\
            .select('user_id, lat, lng, city')\
            .in_('user_id', [user1_id, user2_id])\
            .execute()
        
        if len(locations.data) != 2:
            logger.warning(f"Could not find locations for both users: {user1_id}, {user2_id}")
            return None
        
        # Extract coordinates
        user1_data = next(loc for loc in locations.data if loc['user_id'] == user1_id)
        user2_data = next(loc for loc in locations.data if loc['user_id'] == user2_id)
        
        if not all([user1_data['lat'], user1_data['lng'], user2_data['lat'], user2_data['lng']]):
            logger.warning("One or both users have incomplete location data")
            return None
        
        # Simple distance calculation
        lat_diff = abs(float(user1_data['lat']) - float(user2_data['lat']))
        lng_diff = abs(float(user1_data['lng']) - float(user2_data['lng']))
        
        distance_miles = ((lat_diff * 69) ** 2 + (lng_diff * 69) ** 2) ** 0.5
        
        logger.info(f"Distance between {user1_data['city']} and {user2_data['city']}: {distance_miles:.1f} miles")
        return round(distance_miles, 1)
        
    except Exception as e:
        logger.error(f"Error calculating distance between users: {e}")
        return None