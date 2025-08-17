"""
Agents module for Fridays at Four

Contains the DB-driven agent system that replaces expensive agent manager calls
with fast database queries for 50-95% performance improvement.
"""

from .db_chat_handler import (
    check_intro_done,
    check_creativity_done, 
    check_project_done,
    get_flow_status,
    reset_flows,
    chat,
    handle_intro
)

from .creativity_agent import CreativityTestAgent
from .project_overview_agent import ProjectOverviewAgent
from .agent_manager import AgentManager
from .base_agent import BaseAgent

__all__ = [
    'check_intro_done',
    'check_creativity_done',
    'check_project_done', 
    'get_flow_status',
    'reset_flows',
    'chat',
    'handle_intro',
    'CreativityTestAgent',
    'ProjectOverviewAgent',
    'AgentManager',
    'BaseAgent'
] 