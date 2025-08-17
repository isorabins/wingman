# WingmanMatch Tasks 25, 26, 28 - Infrastructure Foundation Implementation Plan
## Phase 1: Domain-Based Coordination Strategy

**Date**: August 17, 2025  
**Agent**: performance-optimizer  
**Scope**: Infrastructure foundation for Tasks 25, 26, and 28  
**Approach**: Domain-based coordination with automated configuration  

## Executive Summary

This plan establishes the infrastructure foundation required for WingmanMatch Tasks 25 (Beta Operations), 26 (Supabase Provisioning), and 28 (CI Guards). Using domain-based coordination, we focus on creating production-ready automation and configuration files that enable the Backend and Frontend domains to work in parallel during Phase 2.

## Task Analysis & Prioritization

### **Task 26 - Supabase Project Provisioning (PRIORITY 1)**
- **Dependencies**: Tasks 1, 3 (complete)
- **Complexity**: High - Production database and security infrastructure
- **Approach**: Document manual steps, create migration automation
- **Deliverables**: Complete Supabase setup procedures and configuration files

### **Task 28 - CI Guards Implementation (PRIORITY 2)**  
- **Dependencies**: Tasks 1, 3 (complete)
- **Complexity**: Medium - CI/CD workflow and validation automation
- **Approach**: Complete GitHub Actions and local tooling implementation
- **Deliverables**: Production-ready CI guards and validation systems

### **Task 25 - Beta Operations (DEFERRED TO PHASE 2)**
- **Dependencies**: Tasks 17, 23, 24 (complete)
- **Complexity**: High - Full-stack feature implementation
- **Approach**: Requires Backend + Frontend domain coordination
- **Reason for Deferral**: Phase 1 focuses on infrastructure; Phase 2 handles feature development

## Implementation Strategy

### **Phase 1 Scope (This Plan)**
Focus on infrastructure and automation that can be implemented by performance-optimizer:

1. **Documentation Infrastructure** - Complete Supabase setup procedures
2. **Migration Automation** - Database migration files and verification scripts  
3. **Environment Configuration** - Template files and security patterns
4. **CI/CD Automation** - Complete GitHub Actions workflows
5. **Local Tooling** - Validation scripts and pre-commit hooks
6. **Security Infrastructure** - RLS policies and access control patterns

### **Phase 2 Scope (Backend + Frontend Domains)**
Full-stack development requiring domain coordination:

1. **Backend Domain**: APIs, business logic, database operations
2. **Frontend Domain**: UI components, user experience, integration
3. **Task 25 Implementation**: Beta features, feedback systems, analytics

## Technical Implementation Plan

### **TASK 26: Supabase Project Provisioning**

#### **1. Documentation Structure Creation**
```
ops/
├── supabase/
│   ├── README.md                    # Complete setup guide
│   ├── staging-setup.md             # Staging environment procedures  
│   ├── production-setup.md          # Production environment procedures
│   └── troubleshooting.md           # Common issues and solutions
```

#### **2. Environment Configuration Templates**
```
.env.example                         # Template with all required variables
.env.local.example                   # Frontend-specific template
.env.staging.example                 # Staging environment template
.env.production.example              # Production environment template
```

#### **3. Database Migration Infrastructure**
```
supabase/migrations_wm/
├── 001_add_wingman_tables.sql       # ✅ Existing
├── 002_add_confidence_test_progress.sql # ✅ Existing  
├── 003_add_storage_setup.sql        # ✅ Existing
├── 004_storage_policies.sql         # 🆕 NEW - Storage RLS policies
├── 005_enhance_wingman_sessions_rls.sql # ✅ Existing
└── 006_add_dating_goals_enhancements.sql # ✅ Existing
```

#### **4. Security Configuration**
```sql
-- Storage RLS Policies (004_storage_policies.sql)
CREATE POLICY "Users can upload to their own profile folder" 
ON storage.objects FOR INSERT 
TO authenticated 
WITH CHECK (bucket_id = 'profile-photos' AND (storage.foldername(name))[1] = auth.uid()::text);

CREATE POLICY "Users can view their own profile photos" 
ON storage.objects FOR SELECT 
TO authenticated 
USING (bucket_id = 'profile-photos' AND (storage.foldername(name))[1] = auth.uid()::text);

CREATE POLICY "Public can view approved profile photos" 
ON storage.objects FOR SELECT 
TO anon 
USING (bucket_id = 'profile-photos' AND metadata->>'public' = 'true');
```

#### **5. Verification and Testing Scripts**
```bash
scripts/db/verify_supabase_setup.sql  # Comprehensive verification
scripts/test_supabase_connection.py   # Connection testing
scripts/validate_migrations.py        # Migration validation
```

### **TASK 28: CI Guards Implementation**

#### **1. GitHub Actions Workflow**
```yaml
# .github/workflows/ci-guards.yml
name: CI Guards - Reference Files & Tasks Validation

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]

jobs:
  reference-files-protection:
    name: Protect Reference Files
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Check for Reference Files Changes
        run: |
          if git diff --name-only ${{ github.event.before || 'HEAD~1' }} ${{ github.sha }} | grep -q "^reference_files/"; then
            echo "❌ ERROR: Changes detected in reference_files/ directory"
            echo "📁 Affected files:"
            git diff --name-only ${{ github.event.before || 'HEAD~1' }} ${{ github.sha }} | grep "^reference_files/" | sed 's/^/  - /'
            echo ""
            echo "🚫 Reference files should not be modified. Please revert these changes."
            exit 1
          fi
          echo "✅ No changes detected in reference_files/ directory"

  tasks-json-validation:
    name: Validate Tasks JSON
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Validate tasks.json Syntax
        run: |
          echo "🔍 Validating tasks.json syntax..."
          if [ -f "tasks/tasks.json" ]; then
            node -e "
              try {
                const data = JSON.parse(require('fs').readFileSync('tasks/tasks.json', 'utf-8'));
                console.log('✅ tasks.json is valid JSON');
                console.log('📊 Found ' + data.tasks.length + ' tasks');
              } catch (e) {
                console.error('❌ Invalid JSON:', e.message);
                process.exit(1);
              }
            "
          else
            echo "⚠️  tasks.json not found, skipping validation"
          fi

  taskmaster-lint:
    name: Taskmaster Validation
    runs-on: ubuntu-latest
    continue-on-error: true
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install Dependencies
        run: |
          if [ -f "package.json" ]; then
            npm ci
          else
            echo "⚠️  No package.json found, skipping npm install"
          fi
      
      - name: Run Taskmaster Lint
        run: |
          if command -v taskmaster &> /dev/null; then
            echo "🔍 Running Taskmaster lint..."
            taskmaster lint || echo "⚠️  Taskmaster lint completed with warnings"
          else
            echo "⚠️  Taskmaster not available, skipping lint"
          fi
```

#### **2. Local Validation Scripts**
```javascript
// scripts/validate-tasks-json.js
#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

function validateTasksJson() {
  const tasksPath = path.join(__dirname, '../tasks/tasks.json');
  
  try {
    console.log('🔍 Validating tasks.json...');
    
    if (!fs.existsSync(tasksPath)) {
      console.log('⚠️  tasks.json not found at:', tasksPath);
      return true; // Not an error if file doesn't exist
    }
    
    const tasksContent = fs.readFileSync(tasksPath, 'utf8');
    const tasksData = JSON.parse(tasksContent);
    
    console.log('✅ tasks.json is valid JSON');
    console.log('📊 Found', tasksData.tasks?.length || 0, 'tasks');
    
    // Basic structure validation
    if (!tasksData.tasks || !Array.isArray(tasksData.tasks)) {
      throw new Error('tasks.json must contain a "tasks" array');
    }
    
    // Validate each task has required fields
    const requiredFields = ['id', 'title', 'description', 'status'];
    tasksData.tasks.forEach((task, index) => {
      requiredFields.forEach(field => {
        if (!task[field]) {
          throw new Error(`Task ${index + 1} is missing required field: ${field}`);
        }
      });
    });
    
    console.log('✅ All tasks have required fields');
    return true;
    
  } catch (error) {
    console.error('❌ Error validating tasks.json:', error.message);
    return false;
  }
}

if (require.main === module) {
  const isValid = validateTasksJson();
  process.exit(isValid ? 0 : 1);
}

module.exports = { validateTasksJson };
```

#### **3. Pre-commit Hook Template**
```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "🔍 Running pre-commit checks..."

# Check for changes in reference_files/
if git diff --cached --name-only | grep -q "^reference_files/"; then
  echo "❌ ERROR: You're attempting to commit changes to the reference_files/ directory."
  echo "📁 These files should not be modified. Please unstage these changes:"
  git diff --cached --name-only | grep "^reference_files/" | sed 's/^/  - /'
  echo ""
  echo "💡 To unstage: git reset HEAD reference_files/"
  exit 1
fi

# Validate tasks.json if it's being changed
if git diff --cached --name-only | grep -q "tasks/tasks.json"; then
  echo "🔍 Validating tasks.json..."
  if [ -f "scripts/validate-tasks-json.js" ]; then
    node scripts/validate-tasks-json.js
    if [ $? -ne 0 ]; then
      echo "❌ ERROR: Invalid tasks.json. Please fix before committing."
      exit 1
    fi
  fi
fi

echo "✅ Pre-commit checks passed"
exit 0
```

## Security Considerations

### **Database Security**
- **Row Level Security (RLS)**: Enabled globally on all environments
- **JWT Secrets**: Custom secrets for staging and production (never reuse)
- **Service Role Keys**: Rotated after initial setup and team handoff
- **Storage Policies**: Owner-only writes with public read for approved photos
- **File Type Restrictions**: PNG/JPG/JPEG only using storage.extension() validation

### **Environment Security**
- **Secret Management**: All credentials stored securely, never committed
- **Environment Isolation**: Staging and production completely separated
- **Access Control**: Least privilege principle for all team members
- **Backup Security**: PITR enabled with encrypted backups and access logging

### **CI/CD Security**
- **Branch Protection**: Main branch protected with required CI checks
- **Secret Masking**: All CI variables properly masked in logs
- **Reference File Protection**: Automated prevention of accidental modifications
- **Validation Security**: Tasks.json syntax and structure validation

## Implementation Timeline

### **Phase 1: Infrastructure Foundation (This Implementation)**
**Duration**: 1-2 hours
**Deliverables**:
- ✅ Complete Supabase setup documentation
- ✅ Migration files with storage policies  
- ✅ Environment configuration templates
- ✅ GitHub Actions CI guards workflow
- ✅ Local validation scripts and pre-commit hooks
- ✅ Updated README.md with CI Guards documentation

### **Phase 2: Backend + Frontend Domain Implementation** 
**Duration**: 4-6 hours (parallel execution)
**Approach**: Domain-based coordination with tech-lead-orchestrator
**Scope**: Task 25 beta operations features and remaining integration work

## Quality Assurance

### **Testing Strategy**
1. **Migration Testing**: Verify all migrations execute cleanly on staging
2. **Storage Testing**: Validate RLS policies prevent cross-user access
3. **CI Testing**: Create test PRs to verify guard functionality  
4. **Security Testing**: Attempt unauthorized access to validate restrictions
5. **Environment Testing**: Verify staging/production isolation

### **Success Criteria**
- ✅ All Supabase migrations execute without errors
- ✅ Storage RLS policies prevent unauthorized access
- ✅ CI guards block reference_files/ modifications
- ✅ Tasks.json validation catches syntax errors
- ✅ Environment variables properly templated and documented
- ✅ All team members can follow setup procedures successfully

## Risk Mitigation

### **Technical Risks**
- **Migration Failures**: All migrations tested on staging first
- **RLS Policy Issues**: Comprehensive testing with unauthorized access attempts
- **CI/CD Failures**: Fallback to manual validation if GitHub Actions fails
- **Environment Conflicts**: Clear separation between staging and production

### **Operational Risks**  
- **Secret Exposure**: Automated scanning and validation for committed secrets
- **Documentation Drift**: All procedures documented with verification steps
- **Team Access Issues**: Least privilege with clear escalation procedures
- **Backup Failures**: Regular backup testing and restoration procedures

## Conclusion

This infrastructure foundation provides:

1. **Production-Ready Database Infrastructure**: Complete Supabase setup with security hardening
2. **Automated CI/CD Protection**: Guards against accidental modifications and validation failures  
3. **Scalable Environment Management**: Proper staging/production separation with security controls
4. **Team Onboarding**: Clear documentation and procedures for all team members
5. **Security-First Approach**: RLS policies, access controls, and secret management
6. **Foundation for Phase 2**: Enables Backend and Frontend domains to work efficiently

The implementation focuses on automation and documentation, enabling the development team to focus on feature development rather than infrastructure management.
