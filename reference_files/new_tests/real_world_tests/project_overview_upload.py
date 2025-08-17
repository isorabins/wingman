#!/usr/bin/env python3
"""
Script to parse Hai's project plan output and insert into project_overview table
Usage: python parse_hai_output.py
"""

import re
import json
from datetime import datetime, timezone
from supabase import create_client, Client
import os
from typing import Dict, List, Any

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

def parse_hai_output(hai_text: str) -> Dict[str, Any]:
    """
    Parse Hai's structured output into database-ready format
    """
    
    # Initialize result dictionary
    result = {}
    
    # Extract project name (from title or Project Name section)
    project_name_match = re.search(r'PROJECT PLAN - (.+?)(?:\n|\*\*)', hai_text, re.IGNORECASE)
    if project_name_match:
        result['project_name'] = project_name_match.group(1).strip()
    else:
        # Fallback to Project Name section
        project_name_match = re.search(r'\*\*Project Name:\*\*\s*(.+?)(?:\n|\*\*)', hai_text, re.IGNORECASE)
        if project_name_match:
            result['project_name'] = project_name_match.group(1).strip()
        else:
            result['project_name'] = "Untitled Project"
    
    # Extract project type
    project_type_match = re.search(r'\*\*Project Type:\*\*\s*(.+?)(?:\n|\*\*)', hai_text, re.IGNORECASE)
    result['project_type'] = project_type_match.group(1).strip() if project_type_match else "Unknown"
    
    # Extract project description
    desc_match = re.search(r'\*\*Project Description:\*\*\s*(.+?)(?:\n\*\*|\n\n)', hai_text, re.IGNORECASE | re.DOTALL)
    result['description'] = desc_match.group(1).strip() if desc_match else ""
    
    # Extract goals (convert to array format)
    goals_match = re.search(r'\*\*Goals:\*\*\s*(.+?)(?:\n\*\*|\n\n)', hai_text, re.IGNORECASE | re.DOTALL)
    if goals_match:
        goals_text = goals_match.group(1).strip()
        # Split by numbered list or bullet points
        goals_list = re.findall(r'(?:^\d+\.|^-)\s*(.+?)(?=\n\d+\.|\n-|\n\*\*|\Z)', goals_text, re.MULTILINE | re.DOTALL)
        result['goals'] = [goal.strip() for goal in goals_list if goal.strip()]
    else:
        result['goals'] = []
    
    # Extract success metrics (as JSONB)
    metrics_match = re.search(r'\*\*Success Metrics:\*\*\s*(.+?)(?:\n\*\*|\n\n)', hai_text, re.IGNORECASE | re.DOTALL)
    if metrics_match:
        metrics_text = metrics_match.group(1).strip()
        # Convert to structured format
        metrics_list = re.findall(r'(?:^-)\s*(.+?)(?=\n-|\n\*\*|\Z)', metrics_text, re.MULTILINE | re.DOTALL)
        result['success_metrics'] = {
            "metrics": [metric.strip() for metric in metrics_list if metric.strip()],
            "raw_text": metrics_text
        }
    else:
        result['success_metrics'] = {}
    
    # Extract timeline (as JSONB)
    timeline_match = re.search(r'\*\*Timeline:\*\*\s*(.+?)(?:\n\*\*|\n\n)', hai_text, re.IGNORECASE | re.DOTALL)
    if timeline_match:
        timeline_text = timeline_match.group(1).strip()
        # Look for checkpoints section too
        checkpoints_match = re.search(r'\*\*Success Checkpoints:\*\*\s*(.+?)(?:\n\*\*|\n\n)', hai_text, re.IGNORECASE | re.DOTALL)
        
        timeline_data = {"main_timeline": timeline_text}
        if checkpoints_match:
            timeline_data["checkpoints"] = checkpoints_match.group(1).strip()
        
        result['timeline'] = timeline_data
    else:
        result['timeline'] = {}
    
    # Extract weekly commitment
    weekly_match = re.search(r'\*\*Weekly Commitment:\*\*\s*(.+?)(?:\n\*\*|\n\n)', hai_text, re.IGNORECASE | re.DOTALL)
    result['weekly_commitment'] = weekly_match.group(1).strip() if weekly_match else ""
    
    # Extract resources needed (as JSONB)
    resources_match = re.search(r'\*\*Resources Needed:\*\*\s*(.+?)(?:\n\*\*|\n\n)', hai_text, re.IGNORECASE | re.DOTALL)
    if resources_match:
        resources_text = resources_match.group(1).strip()
        resources_list = re.findall(r'(?:^-)\s*(.+?)(?=\n-|\n\*\*|\Z)', resources_text, re.MULTILINE | re.DOTALL)
        result['resources_needed'] = {
            "items": [resource.strip() for resource in resources_list if resource.strip()],
            "raw_text": resources_text
        }
    else:
        result['resources_needed'] = {}
    
    # Extract challenges (convert to array format)
    challenges_match = re.search(r'\*\*Potential Challenges:\*\*\s*(.+?)(?:\n\*\*|\n\n)', hai_text, re.IGNORECASE | re.DOTALL)
    if challenges_match:
        challenges_text = challenges_match.group(1).strip()
        # Extract numbered challenges with solutions
        challenges_list = re.findall(r'(?:^\d+\.|^-)\s*(.+?)(?=\n\d+\.|\n-|\n\*\*|\Z)', challenges_text, re.MULTILINE | re.DOTALL)
        result['challenges'] = [challenge.strip() for challenge in challenges_list if challenge.strip()]
    else:
        result['challenges'] = []
    
    # Extract working style
    style_match = re.search(r'\*\*Working Style:\*\*\s*(.+?)(?:\n\*\*|\n\n|\Z)', hai_text, re.IGNORECASE | re.DOTALL)
    result['working_style'] = style_match.group(1).strip() if style_match else ""
    
    return result

def insert_project_overview(supabase: Client, user_id: str, project_data: Dict[str, Any]) -> bool:
    """
    Insert parsed project data into project_overview table
    """
    try:
        # Add system fields
        project_data.update({
            'user_id': user_id,
            'current_phase': 'planning',
            'creation_date': datetime.now(timezone.utc).isoformat(),
            'last_updated': datetime.now(timezone.utc).isoformat()
        })
        
        # Insert into database
        response = supabase.table("project_overview").insert(project_data).execute()
        
        if response.data:
            print(f"✅ Successfully inserted project: {project_data['project_name']}")
            print(f"📊 Project ID: {response.data[0]['id']}")
            return True
        else:
            print("❌ No data returned from insert")
            return False
            
    except Exception as e:
        print(f"❌ Error inserting project: {e}")
        return False

def main():
    """
    Main function to run the parser
    """
    print("🤖 Hai Output Parser for Fridays at Four")
    print("=" * 50)
    
    # Get user ID
    print("\n👤 First, I need the user ID:")
    user_id = input("Enter user_id: ").strip()
    if not user_id:
        print("❌ User ID is required")
        return
    
    print(f"✅ Got user ID: {user_id}")
    
    # Get Hai's output
    print("\n📋 Now paste Hai's entire project plan output below:")
    print("   (Paste everything, then press Ctrl+D on Mac/Linux or Ctrl+Z on Windows)")
    print("-" * 60)
    
    # Read multi-line input
    hai_output = ""
    try:
        while True:
            line = input()
            hai_output += line + "\n"
    except EOFError:
        pass
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
        return
    
    if not hai_output.strip():
        print("❌ No content was pasted")
        return
    
    print(f"\n✅ Received {len(hai_output)} characters of input")
    
    # Parse the output
    print("\n🔍 Parsing Hai's output...")
    parsed_data = parse_hai_output(hai_output)
    
    # Show parsed data
    print(f"\n📋 Parsed Project Data:")
    print(f"   Name: {parsed_data['project_name']}")
    print(f"   Type: {parsed_data['project_type']}")
    print(f"   Goals: {len(parsed_data['goals'])} items")
    print(f"   Challenges: {len(parsed_data['challenges'])} items")
    print(f"   Working Style: {parsed_data['working_style'][:50]}...")
    
    # Confirm insertion
    confirm = input(f"\n💾 Insert this project for user {user_id}? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Cancelled")
        return
    
    # Initialize Supabase client
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ Missing Supabase environment variables")
        return
    
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # Insert into database
    success = insert_project_overview(supabase, user_id, parsed_data)
    
    if success:
        print("\n🎉 Project successfully added to database!")
    else:
        print("\n💥 Failed to add project to database")

if __name__ == "__main__":
    main()