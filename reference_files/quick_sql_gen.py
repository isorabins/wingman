#!/usr/bin/env python3

import sys
import os
sys.path.append('scripts')

from insert_project_plan import parse_project_plan, generate_sql

# Read the existing project file
project_file = "docs/user-project-overviews/project_plan_christine_sarikas_20250707_095222.txt"

with open(project_file, 'r') as f:
    project_text = f.read()

# Parse the project
project_data = parse_project_plan(project_text)

# Generate SQL
user_id = "6de78e0b-86bc-4585-b991-910b2b2b7a3b"
email = "christine.sarikas@gmail.com"

sql = generate_sql(user_id, email, project_data)

# Save SQL file
output_file = "docs/user-project-overviews/insert_project_jungle_witch_20250707.sql"
with open(output_file, 'w') as f:
    f.write(sql)

print(f"✅ SQL generated: {output_file}")
print("🎯 Ready to paste into Supabase SQL editor!") 