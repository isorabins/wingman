#!/bin/bash

# Project Plan to SQL Generator
# Double-click this file to run

echo "🎯 Starting Project Plan to SQL Generator..."
echo "📁 Setting up temporary environment..."

# Create the Python script in /tmp
cat > /tmp/insert_project_plan.py << 'EOF'
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
    
    # First, clean the text and check if it looks like Python code
    if 'def ' in project_text or 'import ' in project_text or 'print(' in project_text:
        print("⚠️  WARNING: The text appears to contain Python code, not a project plan!")
        print("⚠️  Please make sure you paste your actual project plan, not code.")
        return project_data
    
    # Split text into sections - look for markdown-style headers
    lines = project_text.split('\n')
    current_section = None
    current_content = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for section headers (lines ending with :)
        if line.endswith(':') and not line.startswith('-'):
            # Process previous section
            if current_section and current_content:
                content = ' '.join(current_content).strip()
                
                if 'project name' in current_section.lower():
                    project_data['project_name'] = content
                elif 'project type' in current_section.lower():
                    project_data['project_type'] = content
                elif 'description' in current_section.lower():
                    project_data['description'] = content
                elif 'goal' in current_section.lower():
                    # Split on bullet points or line breaks
                    goals = [g.strip('- •').strip() for g in content.split('\n') if g.strip()]
                    project_data['goals'] = [g for g in goals if g and len(g) > 3]
                elif 'challenge' in current_section.lower():
                    challenges = [c.strip('- •').strip() for c in content.split('\n') if c.strip()]
                    project_data['challenges'] = [c for c in challenges if c and len(c) > 3]
                elif 'resource' in current_section.lower():
                    resources = [r.strip('- •').strip() for r in content.split('\n') if r.strip()]
                    project_data['resources_needed'] = [r for r in resources if r and len(r) > 3]
                elif 'commitment' in current_section.lower() or 'weekly' in current_section.lower():
                    project_data['weekly_commitment'] = content
                elif 'support' in current_section.lower():
                    project_data['support_style'] = content
                elif 'working' in current_section.lower() or 'work style' in current_section.lower():
                    project_data['working_style'] = content
                elif 'metric' in current_section.lower() or 'success' in current_section.lower():
                    project_data['success_metrics'] = {'success_definition': content}
            
            # Start new section
            current_section = line.replace(':', '').strip()
            current_content = []
        else:
            # Add to current section content
            current_content.append(line)
    
    # Process the last section
    if current_section and current_content:
        content = ' '.join(current_content).strip()
        
        if 'project name' in current_section.lower():
            project_data['project_name'] = content
        elif 'project type' in current_section.lower():
            project_data['project_type'] = content
        elif 'description' in current_section.lower():
            project_data['description'] = content
        elif 'goal' in current_section.lower():
            goals = [g.strip('- •').strip() for g in content.split('\n') if g.strip()]
            project_data['goals'] = [g for g in goals if g and len(g) > 3]
        elif 'challenge' in current_section.lower():
            challenges = [c.strip('- •').strip() for c in content.split('\n') if c.strip()]
            project_data['challenges'] = [c for c in challenges if c and len(c) > 3]
        elif 'resource' in current_section.lower():
            resources = [r.strip('- •').strip() for r in content.split('\n') if r.strip()]
            project_data['resources_needed'] = [r for r in resources if r and len(r) > 3]
        elif 'commitment' in current_section.lower() or 'weekly' in current_section.lower():
            project_data['weekly_commitment'] = content
        elif 'support' in current_section.lower():
            project_data['support_style'] = content
        elif 'working' in current_section.lower():
            project_data['working_style'] = content
    
    return project_data

def display_parsed_data(project_data: Dict[str, Any]):
    """Display the parsed project data for review"""
    
    print("\n" + "="*60)
    print("PARSED PROJECT DATA")
    print("="*60)
    
    print(f"\nProject Name: {project_data.get('project_name', 'Not specified')}")
    print(f"Project Type: {project_data.get('project_type', 'Not specified')}")
    print(f"Current Phase: {project_data.get('current_phase', 'planning')}")
    
    desc = project_data.get('description', 'Not specified')
    if len(desc) > 100:
        desc = desc[:100] + "..."
    print(f"Description: {desc}")
    
    print(f"Weekly Commitment: {project_data.get('weekly_commitment', 'Not specified')}")
    
    goals = project_data.get('goals', [])
    print(f"\nGoals ({len(goals)}):")
    for i, goal in enumerate(goals[:3], 1):
        goal_display = goal[:80] + "..." if len(goal) > 80 else goal
        print(f"  {i}. {goal_display}")
    
    challenges = project_data.get('challenges', [])
    print(f"\nChallenges ({len(challenges)}):")
    for i, challenge in enumerate(challenges[:3], 1):
        challenge_display = challenge[:80] + "..." if len(challenge) > 80 else challenge
        print(f"  {i}. {challenge_display}")
    
    resources = project_data.get('resources_needed', [])
    print(f"\nResources Needed ({len(resources)}):")
    for i, resource in enumerate(resources[:3], 1):
        resource_display = resource[:60] + "..." if len(resource) > 60 else resource
        print(f"  {i}. {resource_display}")
    
    support = project_data.get('support_style', 'Not specified')
    if len(support) > 60:
        support = support[:60] + "..."
    print(f"\nSupport Style: {support}")
    
    working = project_data.get('working_style', 'Not specified')
    if len(working) > 60:
        working = working[:60] + "..."
    print(f"Working Style: {working}")
    
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
    print("⚠️  IMPORTANT: Paste your PROJECT PLAN content, NOT Python code!")
    
    # Create a temporary file with better instructions
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as temp_file:
        temp_path = temp_file.name
        temp_file.write("""PASTE YOUR PROJECT PLAN HERE - DELETE THIS TEXT FIRST!

Example format:
Project Name: My Amazing Project
Project Type: Personal Development
Description: This project is about...

Goals:
- Goal 1
- Goal 2

Challenges:
- Challenge 1
- Challenge 2

Weekly Commitment: 5 hours per week

Resources Needed:
- Resource 1
- Resource 2

Support Style: How you like to be supported
""")
    
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
        print("1. DELETE ALL the placeholder text")
        print("2. Paste your ACTUAL PROJECT PLAN (not code!)")
        print("3. Save the file (Cmd+S)")
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
        if content.startswith("PASTE YOUR PROJECT PLAN HERE"):
            lines = content.split('\n')
            # Find where the placeholder ends
            for i, line in enumerate(lines):
                if line.strip() and not line.startswith("PASTE YOUR PROJECT") and not line.startswith("Example format") and not line.strip().startswith("Project Name:") and "My Amazing Project" not in line:
                    content = '\n'.join(lines[i:]).strip()
                    break
            else:
                content = ""
        
        print(f"📏 Received {len(content)} characters")
        
        # Validate content
        if len(content) < 50:
            print("⚠️  WARNING: Content seems very short. Make sure you pasted your full project plan.")
        
        if 'def ' in content or 'import ' in content:
            print("⚠️  WARNING: Content appears to contain code. Please paste your project plan instead.")
            
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
    
    # Create safe filename for SQL
    project_name = project_data.get('project_name', 'project')
    if len(project_name) > 20:  # Limit length
        project_name = project_name[:20]
    
    safe_name = project_name.lower().replace(' ', '_').replace('-', '_')
    safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '_')
    
    if not safe_name or len(safe_name) < 3:  # Fallback if name is too short/empty
        safe_name = "project"
    
    # Save to Desktop - works on any Mac
    desktop_path = os.path.expanduser("~/Desktop")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    sql_filename = os.path.join(desktop_path, f"insert_{safe_name}_{timestamp}.sql")
    
    # Write SQL file
    try:
        with open(sql_filename, 'w', encoding='utf-8') as f:
            f.write(sql_content)
        
        # Also save the original project plan for reference
        plan_filename = sql_filename.replace('.sql', '_plan.txt')
        with open(plan_filename, 'w', encoding='utf-8') as f:
            f.write(project_text)
        
        print(f"\n✅ SQL file generated: {os.path.basename(sql_filename)}")
        print(f"📁 Saved to Desktop: {sql_filename}")
        print(f"📄 Project plan saved: {os.path.basename(plan_filename)}")
        print("\n📋 Next steps:")
        print("1. Check your Desktop for the SQL file")
        print("2. Open the SQL file and copy its contents")
        print("3. Paste into Supabase SQL editor")
        print("4. Execute the query")
        print("\n🎉 Done!")
        
    except Exception as e:
        print(f"❌ Error writing SQL file: {str(e)}")
        # Try a simple fallback filename
        try:
            fallback_filename = os.path.join(desktop_path, f"project_sql_{timestamp}.sql")
            with open(fallback_filename, 'w', encoding='utf-8') as f:
                f.write(sql_content)
            print(f"✅ Saved with fallback name: {fallback_filename}")
        except Exception as e2:
            print(f"❌ Complete failure: {str(e2)}")
        return

if __name__ == "__main__":
    main() 
EOF

# Change to /tmp directory and run the Python script
cd /tmp

echo "🚀 Running Project Plan Generator..."
python3 insert_project_plan.py

# Clean up the temporary file
rm -f insert_project_plan.py

echo ""
echo "✨ Script completed!"
echo "Press Enter to close this window..."
read