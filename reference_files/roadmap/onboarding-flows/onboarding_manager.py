from supabase import Client
from typing import Dict, List, Optional
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class OnboardingManager:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    async def update_creator_profile(self, user_id: str, slack_id: str) -> bool:
        try:
            self.supabase.table('creator_profiles')\
                .update({"slack_id": slack_id})\
                .eq('id', user_id)\
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error updating creator profile: {str(e)}")
            return False

    async def create_project_overview(
        self,
        user_id: str,
        project_name: str,
        project_type: str,
        description: str,
        goals: List[Dict],
        challenges: List[Dict],
        success_metrics: Dict,
        current_phase: str = 'planning'
    ) -> Optional[str]:
        try:
            result = self.supabase.table('project_overview').insert({
                "user_id": user_id,
                "project_name": project_name,
                "project_type": project_type,
                "description": description,
                "current_phase": current_phase,
                "goals": goals,
                "challenges": challenges,
                "success_metrics": success_metrics,
                "creation_date": datetime.now(timezone.utc).isoformat(),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }).execute()

            return result.data[0]["id"] if result.data else None

        except Exception as e:
            logger.error(f"Error creating project overview: {str(e)}")
            return None