#!/usr/bin/env python3
"""
Project Plan to SQL Generator Script
Prompts for user details and project plan, then generates SQL file for manual insertion
"""

import json
import sys
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any

def parse_project_plan(project_text: str) -> Dict[str, Any]:
    """Parse project plan text into structured data"""
    
    # Initialize default structure matching actual database schema
    project_data = {
        'project_name': '',
        'project_type': '',
        'description': '',
        'current_phase': 'planning',
        'goals': [],
        'challenges': [],
        'success_metrics': {},
        'timeline': {},
        'weekly_commitment': '',
        'resources_needed': [],
        'working_style': '',
        'support_style': '',
        'motivation': ''
    }
    
    # Split text into lines and process
    lines = project_text.replace('\n', ' ').split('**')
    
    current_section = None
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Check if this is a section header
        if ':' in line and not line.startswith('-'):
            current_section = line.lower().replace(':', '').strip()
            # Get content after the colon or from next section
            content = ''
            if ':' in line:
                content = line.split(':', 1)[1].strip()
            if not content and i + 1 < len(lines):
                content = lines[i + 1].strip()
            
            # Map sections to data structure
            if 'project name' in current_section:
                project_data['project_name'] = content
            elif 'project type' in current_section:
                project_data['project_type'] = content
            elif 'project description' in current_section:
                project_data['description'] = content
            elif 'goals' in current_section:
                # Parse goals from bullet points
                goals = []
                goal_text = content
                # Look for bullet points with - or •
                for goal_line in goal_text.split('-'):
                    goal_line = goal_line.strip()
                    if goal_line and not goal_line.startswith('**'):
                        goals.append(goal_line)
                project_data['goals'] = goals
            elif 'success metrics' in current_section:
                # Parse success metrics
                metrics = []
                for metric_line in content.split('-'):
                    metric_line = metric_line.strip()
                    if metric_line and not metric_line.startswith('**'):
                        metrics.append(metric_line)
                project_data['success_metrics'] = {
                    'key_metrics': metrics,
                    'success_definition': content
                }
            elif 'timeline' in current_section:
                # Parse timeline information
                timeline_info = {}
                if 'year' in content.lower():
                    timeline_info['overall'] = content
                if 'weekly' in content.lower():
                    # Extract weekly commitment
                    parts = content.split('Weekly Commitment:')
                    if len(parts) > 1:
                        project_data['weekly_commitment'] = parts[1].strip()
                project_data['timeline'] = timeline_info
            elif 'weekly commitment' in current_section:
                project_data['weekly_commitment'] = content
            elif 'resources needed' in current_section:
                resources = []
                for resource_line in content.split('-'):
                    resource_line = resource_line.strip()
                    if resource_line and not resource_line.startswith('**'):
                        resources.append(resource_line)
                project_data['resources_needed'] = resources
            elif 'potential challenges' in current_section or 'challenges' in current_section:
                challenges = []
                for challenge_line in content.split('-'):
                    challenge_line = challenge_line.strip()
                    if challenge_line and not challenge_line.startswith('**'):
                        challenges.append(challenge_line)
                project_data['challenges'] = challenges
            elif 'support style' in current_section:
                project_data['support_style'] = content
            elif 'working style' in current_section or 'motivation' in current_section:
                if 'working style' in current_section:
                    project_data['working_style'] = content
                else:
                    project_data['motivation'] = content
    
    return project_data

def display_parsed_data(project_data: Dict[str, Any]):
    """Display the parsed project data for review"""
    
    print("\n" + "="*60)
    print("PARSED PROJECT DATA")
    print("="*60)
    
    print(f"\nProject Name: {project_data.get('project_name', 'Not specified')}")
    print(f"Project Type: {project_data.get('project_type', 'Not specified')}")
    print(f"Current Phase: {project_data.get('current_phase', 'planning')}")
    print(f"Description: {project_data.get('description', 'Not specified')[:100]}...")
    print(f"Weekly Commitment: {project_data.get('weekly_commitment', 'Not specified')}")
    
    print(f"\nGoals ({len(project_data.get('goals', []))}):")
    for i, goal in enumerate(project_data.get('goals', [])[:3], 1):
        print(f"  {i}. {goal[:80]}...")
    
    print(f"\nChallenges ({len(project_data.get('challenges', []))}):")
    for i, challenge in enumerate(project_data.get('challenges', [])[:3], 1):
        print(f"  {i}. {challenge[:80]}...")
    
    print(f"\nResources Needed ({len(project_data.get('resources_needed', []))}):")
    for i, resource in enumerate(project_data.get('resources_needed', [])[:3], 1):
        print(f"  {i}. {resource[:60]}...")
    
    print(f"\nSupport Style: {project_data.get('support_style', 'Not specified')[:60]}...")
    print(f"Working Style: {project_data.get('working_style', 'Not specified')[:60]}...")
    
    print("\n" + "="*60)

def escape_sql_string(value: str) -> str:
    """Escape single quotes in SQL strings"""
    if value is None:
        return "NULL"
    return value.replace("'", "''")

def format_jsonb_array_for_sql(items: List[str]) -> str:
    """Format a list of strings as PostgreSQL jsonb[] array"""
    if not items:
        return "ARRAY[]::jsonb[]"
    
    # Each item needs to be valid JSON (quoted string) then cast to jsonb
    escaped_items = [f"'\"{escape_sql_string(item)}\"'::jsonb" for item in items]
    return f"ARRAY[{', '.join(escaped_items)}]"

def generate_sql(user_id: str, email: str, project_data: Dict[str, Any]) -> str:
    """Generate SQL INSERT statement with correct PostgreSQL types"""
    
    # Generate a UUID for the project
    project_id = str(uuid.uuid4())
    
    # Build success_metrics JSON object
    success_metrics = {}
    
    # Add timeline if present
    if project_data.get('timeline') or project_data.get('weekly_commitment'):
        timeline_text = ""
        if project_data.get('timeline', {}).get('overall'):
            timeline_text = project_data['timeline']['overall']
        elif project_data.get('weekly_commitment'):
            timeline_text = f"Weekly commitment: {project_data['weekly_commitment']}"
        
        if timeline_text:
            success_metrics['timeline'] = timeline_text
    
    # Add key metrics from success metrics
    if project_data.get('success_metrics', {}).get('key_metrics'):
        success_metrics['key_metrics'] = project_data['success_metrics']['key_metrics']
    
    # Add working style
    if project_data.get('support_style'):
        success_metrics['working_style'] = project_data['support_style']
    
    # Add resources needed
    if project_data.get('resources_needed'):
        success_metrics['resources_needed'] = project_data['resources_needed']
    
    # Add weekly commitment
    if project_data.get('weekly_commitment'):
        success_metrics['weekly_commitment'] = project_data['weekly_commitment']
    
    # Add success definition from parsed metrics
    if project_data.get('success_metrics', {}).get('success_definition'):
        success_metrics['success_definition'] = project_data['success_metrics']['success_definition']
    
    # Generate SQL with correct PostgreSQL types
    sql = f"""-- Project Overview Insert for {email}
-- Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

-- Verify user exists first
SELECT id, slack_email FROM creator_profiles WHERE id = '{user_id}';

-- Insert project overview
INSERT INTO "public"."project_overview" (
    "id",
    "user_id",
    "project_name", 
    "project_type",
    "description",
    "current_phase",
    "goals",
    "challenges",
    "success_metrics",
    "creation_date",
    "last_updated",
    "timeline",
    "weekly_commitment",
    "resources_needed",
    "working_style"
) VALUES (
    '{project_id}',
    '{user_id}',
    '{escape_sql_string(project_data.get('project_name', ''))}',
    '{escape_sql_string(project_data.get('project_type', ''))}',
    '{escape_sql_string(project_data.get('description', ''))}',
    '{escape_sql_string(project_data.get('current_phase', 'planning'))}',
    {format_jsonb_array_for_sql(project_data.get('goals', []))},
    {format_jsonb_array_for_sql(project_data.get('challenges', []))},
    '{escape_sql_string(json.dumps(success_metrics))}'::jsonb,
    NOW(),
    NOW(),
    '{{}}'::jsonb,
    {f"'{escape_sql_string(project_data.get('weekly_commitment', ''))}'" if project_data.get('weekly_commitment') else 'null'},
    '{{}}'::jsonb,
    {f"'{escape_sql_string(project_data.get('support_style', ''))}'" if project_data.get('support_style') else 'null'}
);

-- Verify insertion
SELECT 
    project_name,
    project_type,
    current_phase,
    array_length(goals, 1) as goals_count,
    array_length(challenges, 1) as challenges_count,
    weekly_commitment,
    creation_date
FROM project_overview 
WHERE user_id = '{user_id}' 
ORDER BY creation_date DESC 
LIMIT 1;
"""
    
    return sql

def get_multiline_input(prompt: str) -> str:
    """Get project plan input from user via temporary file"""
    import tempfile
    import subprocess
    import platform
    
    print(f"\n{prompt}")
    print("📝 Creating a temporary file for you to paste your project plan...")
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as temp_file:
        temp_path = temp_file.name
        temp_file.write("# Paste your project plan here, then save and close this file\n\n")
    
    print(f"📁 Temporary file created: {temp_path}")
    
    # Open the file in the default text editor
    try:
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.call(["open", "-t", temp_path])
        elif system == "Windows":
            subprocess.call(["notepad", temp_path])
        else:  # Linux
            subprocess.call(["xdg-open", temp_path])
        
        print("📝 A text editor should have opened with the temporary file.")
        print("📋 Steps:")
        print("1. Delete the placeholder text")
        print("2. Paste your entire project plan")
        print("3. Save the file")
        print("4. Close the editor")
        print("5. Come back here and press Enter")
        
        input("\n⏳ Press Enter when you've finished editing and saved the file...")
        
        # Read the content back
        with open(temp_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Clean up - remove the temp file
        import os
        os.unlink(temp_path)
        
        # Remove the placeholder text if it's still there
        if content.startswith("# Paste your project plan here"):
            lines = content.split('\n')
            content = '\n'.join(lines[2:]).strip()
        
        print(f"📏 Received {len(content)} characters")
        return content
        
    except Exception as e:
        print(f"❌ Error opening editor: {e}")
        print("📝 Fallback: Please manually edit the file and paste your content:")
        print(f"📁 File location: {temp_path}")
        input("⏳ Press Enter when you've finished editing the file...")
        
        try:
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            import os
            os.unlink(temp_path)
            return content
        except Exception as e2:
            print(f"❌ Error reading file: {e2}")
            return None

def main():
    """Main function to run the interactive project plan insertion"""
    
    print("🎯 Project Plan to SQL Generator")
    print("=" * 40)
    
    # Get user information
    user_id = input("\n👤 Enter user ID: ").strip()
    if not user_id:
        print("❌ User ID is required")
        return
    
    user_email = input("📧 Enter user email (for verification): ").strip()
    if not user_email:
        print("❌ User email is required")
        return
    
    # Get project plan content directly from terminal
    project_text = get_multiline_input("📋 Project Plan Input")
    if not project_text:
        print("❌ No project plan content provided")
        return
    
    # Parse the project plan
    print("\n🔄 Parsing project plan...")
    project_data = parse_project_plan(project_text)
    
    # Display parsed data for confirmation
    print("\n📊 Parsed Project Data:")
    display_parsed_data(project_data)
    
    # Confirm before generating SQL
    confirm = input("\n❓ Generate SQL file? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ SQL generation cancelled")
        return
    
    # Generate SQL
    print("\n🔄 Generating SQL...")
    sql_content = generate_sql(user_id, user_email, project_data)
    
    # Create filename for SQL
    safe_name = project_data.get('project_name', 'project').lower().replace(' ', '_').replace('-', '_')
    safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '_')
    
    # Create output directory
    output_dir = os.path.join('docs', 'user-project-overviews')
    os.makedirs(output_dir, exist_ok=True)
    
    sql_filename = os.path.join(output_dir, f"insert_project_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql")
    
    # Write SQL file
    try:
        with open(sql_filename, 'w', encoding='utf-8') as f:
            f.write(sql_content)
        
        # Also save the original project plan for reference
        plan_filename = sql_filename.replace('.sql', '_plan.txt')
        with open(plan_filename, 'w', encoding='utf-8') as f:
            f.write(project_text)
        
        print(f"\n✅ SQL file generated: {sql_filename}")
        print(f"📁 Location: {os.path.abspath(sql_filename)}")
        print(f"📄 Project plan saved: {plan_filename}")
        print("\n📋 Next steps:")
        print("1. Review the SQL file")
        print("2. Copy the SQL content")
        print("3. Paste into Supabase SQL editor")
        print("4. Execute the query")
        print("\n🎉 Done!")
        
    except Exception as e:
        print(f"❌ Error writing SQL file: {str(e)}")
        return

if __name__ == "__main__":
    main() 