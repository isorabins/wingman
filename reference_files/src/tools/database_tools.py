from supabase import Client
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseTools:
    """Database operations for agent state management and final result storage."""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    # === CREATIVITY TEST TOOLS ===

    async def save_creativity_answer(
        self,
        user_id: str,
        question_number: int,
        question_text: str,
        answer_text: str
    ) -> Dict[str, Any]:
        """
        Save a single creativity test answer and update progress.
        
        This tool saves individual question responses and tracks overall progress
        through the 7-question creativity assessment. It handles upsert logic
        to allow users to modify previous answers and provides progress tracking.
        
        Args:
            user_id: Unique identifier for the user taking the test
            question_number: Question sequence number (1-7)
            question_text: The exact question that was asked to the user
            answer_text: User's complete response to the question
            
        Returns:
            Dict with success status, current progress, and question count
        """
        try:
            # Get existing progress
            result = self.supabase.table('creativity_test_progress').select('*').eq('user_id', user_id).execute()
            
            if result.data:
                answers = result.data[0]['answers']
            else:
                answers = {}
            
            # Add new answer with metadata
            answers[f"q{question_number}"] = {
                "question": question_text,
                "answer": answer_text,
                "timestamp": datetime.now().isoformat(),
                "question_number": question_number
            }
            
            # Upsert progress
            upsert_result = self.supabase.table('creativity_test_progress').upsert({
                'user_id': user_id,
                'current_question': question_number,
                'answers': answers,
                'updated_at': datetime.now().isoformat()
            }).execute()
            
            logger.info(f"Saved creativity answer {question_number}/7 for user {user_id}")
            
            return {
                "success": True,
                "current_question": question_number,
                "total_questions": 7,
                "answers_count": len(answers),
                "progress_percentage": round((len(answers) / 7) * 100, 1)
            }
            
        except Exception as e:
            logger.error(f"Error saving creativity answer: {e}")
            return {
                "success": False,
                "error": f"Failed to save answer: {str(e)}",
                "current_question": question_number,
                "total_questions": 7
            }

    async def get_creativity_progress(self, user_id: str) -> Dict[str, Any]:
        """
        Load current creativity test progress for user.
        
        Retrieves the user's current position in the creativity test, including
        all previously answered questions and determines if the test is complete.
        Used for resuming interrupted test sessions and avoiding duplicate questions.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Dict with progress status, current question, answers, and completion status
        """
        try:
            result = self.supabase.table('creativity_test_progress').select('*').eq('user_id', user_id).execute()
            
            if not result.data:
                return {
                    "exists": False,
                    "current_question": 1,
                    "answers": {},
                    "is_complete": False,
                    "progress_percentage": 0.0
                }
            
            progress = result.data[0]
            answers = progress['answers']
            is_complete = len(answers) >= 7
            
            logger.info(f"Loaded creativity progress for user {user_id}: {len(answers)}/7 questions")
            
            return {
                "exists": True,
                "current_question": progress['current_question'],
                "answers": answers,
                "is_complete": is_complete,
                "progress_percentage": round((len(answers) / 7) * 100, 1),
                "last_updated": progress['updated_at']
            }
            
        except Exception as e:
            logger.error(f"Error loading creativity progress: {e}")
            return {
                "exists": False,
                "error": f"Failed to load progress: {str(e)}",
                "current_question": 1,
                "answers": {},
                "is_complete": False
            }

    async def complete_creativity_test(
        self,
        user_id: str,
        archetype: str,
        archetype_description: str,
        archetype_score: float,
        test_responses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Complete creativity test and store final results in your existing table.
        
        Saves the final creativity assessment results to creator_creativity_profiles
        and cleans up the progress tracking table. This tool should only be called
        after all 7 questions have been answered and the archetype has been calculated.
        
        Args:
            user_id: User identifier
            archetype: Calculated creativity archetype (Explorer, Innovator, Artist, Builder, Collaborator, Synthesizer)
            archetype_description: Detailed 2-3 sentence description of the archetype
            archetype_score: Confidence score for the archetype assignment (0.0-1.0)
            test_responses: Complete dictionary of all user responses for future reference
            
        Returns:
            Dict with completion status and archetype information
        """
        try:
            # Insert into your existing table structure
            result = self.supabase.table('creator_creativity_profiles').upsert({
                'user_id': user_id,
                'archetype': archetype,
                'archetype_score': archetype_score,
                'test_responses': test_responses,
                'created_at': datetime.now().isoformat()
            }).execute()
            
            # Clean up progress table
            self.supabase.table('creativity_test_progress').delete().eq('user_id', user_id).execute()
            
            logger.info(f"Completed creativity test for user {user_id}: {archetype} ({archetype_score:.2f})")
            
            return {
                "success": True,
                "archetype": archetype,
                "archetype_score": archetype_score,
                "message": f"Creativity test completed! You are a {archetype}."
            }
            
        except Exception as e:
            logger.error(f"Error completing creativity test: {e}")
            return {
                "success": False,
                "error": f"Failed to complete test: {str(e)}"
            }

    # === PROJECT OVERVIEW TOOLS ===

    async def save_project_topic(
        self,
        user_id: str,
        topic_number: int,
        topic_name: str,
        response_text: str
    ) -> Dict[str, Any]:
        """
        Save project planning topic response and update progress.
        
        Stores individual topic responses during the 8-topic project planning session.
        Handles upsert logic for topic modifications and tracks overall planning progress.
        Each topic represents a key aspect of project planning (description, goals, timeline, etc.).
        
        Args:
            user_id: Unique identifier for the user
            topic_number: Topic sequence number (1-8)
            topic_name: Name of the topic (e.g., 'Project Description', 'Goals', 'Timeline')
            response_text: User's detailed response about this topic
            
        Returns:
            Dict with success status, current progress, and topic completion count
        """
        try:
            # Get existing data
            result = self.supabase.table('project_overview_progress').select('*').eq('user_id', user_id).execute()
            
            if result.data:
                data = result.data[0]['collected_data']
            else:
                data = {}
            
            # Add new topic data with metadata
            data[f"topic_{topic_number}"] = {
                "name": topic_name,
                "response": response_text,
                "timestamp": datetime.now().isoformat(),
                "topic_number": topic_number
            }
            
            # Upsert progress
            upsert_result = self.supabase.table('project_overview_progress').upsert({
                'user_id': user_id,
                'current_topic': topic_number,
                'collected_data': data,
                'updated_at': datetime.now().isoformat()
            }).execute()
            
            logger.info(f"Saved project topic {topic_number}/8 for user {user_id}: {topic_name}")
            
            return {
                "success": True,
                "current_topic": topic_number,
                "total_topics": 8,
                "topics_completed": len(data),
                "progress_percentage": round((len(data) / 8) * 100, 1)
            }
            
        except Exception as e:
            logger.error(f"Error saving project topic: {e}")
            return {
                "success": False,
                "error": f"Failed to save topic: {str(e)}",
                "current_topic": topic_number,
                "total_topics": 8
            }

    async def get_project_progress(self, user_id: str) -> Dict[str, Any]:
        """
        Load current project overview progress for user.
        
        Retrieves the user's current position in the project planning process,
        including all previously completed topics and determines completion status.
        Used for resuming interrupted planning sessions and building on previous work.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Dict with progress status, current topic, collected data, and completion status
        """
        try:
            result = self.supabase.table('project_overview_progress').select('*').eq('user_id', user_id).execute()
            
            if not result.data:
                return {
                    "exists": False,
                    "current_topic": 1,
                    "collected_data": {},
                    "is_complete": False,
                    "progress_percentage": 0.0
                }
            
            progress = result.data[0]
            collected_data = progress['collected_data']
            is_complete = len(collected_data) >= 8
            
            logger.info(f"Loaded project progress for user {user_id}: {len(collected_data)}/8 topics")
            
            return {
                "exists": True,
                "current_topic": progress['current_topic'],
                "collected_data": collected_data,
                "is_complete": is_complete,
                "progress_percentage": round((len(collected_data) / 8) * 100, 1),
                "last_updated": progress['updated_at']
            }
            
        except Exception as e:
            logger.error(f"Error loading project progress: {e}")
            return {
                "exists": False,
                "error": f"Failed to load progress: {str(e)}",
                "current_topic": 1,
                "collected_data": {},
                "is_complete": False
            }

    async def complete_project_overview(
        self,
        user_id: str,
        project_name: str,
        project_type: str,
        description: str,
        goals: Dict[str, Any],
        challenges: Dict[str, Any],
        success_metrics: str
    ) -> Dict[str, Any]:
        """
        Complete project overview and store final results in your existing table.
        
        Extracts structured data from the 8-topic planning session and stores it
        in the project_overview table using your existing schema. Cleans up the
        progress tracking table after successful completion.
        
        Args:
            user_id: User identifier
            project_name: Clear, concise name for the project
            project_type: Category (writing, design, business, technology, etc.)
            description: Comprehensive description of what they're creating
            goals: Dictionary containing structured goals and milestones
            challenges: Dictionary containing anticipated challenges and solutions
            success_metrics: How they'll measure project success
            
        Returns:
            Dict with completion status and project information
        """
        try:
            # Insert into your existing table structure
            result = self.supabase.table('project_overview').upsert({
                'user_id': user_id,
                'project_name': project_name,
                'project_type': project_type,
                'description': description,
                'goals': goals,
                'challenges': challenges,
                'success_metrics': success_metrics,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }).execute()
            
            # Clean up progress table
            self.supabase.table('project_overview_progress').delete().eq('user_id', user_id).execute()
            
            project_id = result.data[0]['id'] if result.data else None
            
            logger.info(f"Completed project overview for user {user_id}: {project_name}")
            
            return {
                "success": True,
                "project_id": project_id,
                "project_name": project_name,
                "message": f"Project overview completed for '{project_name}'!"
            }
            
        except Exception as e:
            logger.error(f"Error completing project overview: {e}")
            return {
                "success": False,
                "error": f"Failed to complete project: {str(e)}"
            } 