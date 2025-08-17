# 🚀 Fridays at Four - Developer Setup Guide

## 🎯 Quick Start for New Developers

This guide will get you set up to develop, test, and contribute to Fridays at Four locally without production deployment access.

## 📋 Prerequisites

- **Python 3.10+** installed
- **Git** configured with your GitHub account
- **Code editor** (VS Code recommended)
- **Terminal/Command line** access

## 🔧 Environment Setup

### 1. Clone the Repository
```bash
git clone https://github.com/[your-org]/fridays-at-four.git
cd fridays-at-four
```

### 2. Set Up Environment Variables
```bash
# Copy the developer environment template
cp developer-env-template.txt .env

# Edit the .env file to update local paths
# Change BASE_DIR to your actual project path
```

### 3. Install Dependencies
```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all required packages
pip install -r requirements.txt
```

### 4. Verify Setup
```bash
# Test that all imports work
python src/test_imports.py

# Run health check
python -c "from src.config import get_config; print('✅ Config loaded successfully')"
```

## 🏃‍♂️ Running the Application Locally

### Start the Development Server
```bash
uvicorn src.main:app --reload --host localhost --port 8000
```

### Verify It's Working
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Main Chat Endpoint**: http://localhost:8000/query

## 🧪 Testing Your Setup

### Run the Test Suite
```bash
# Run all real-world integration tests
python new_tests/real_world_tests/run_all_tests.py

# Test specific functionality
python new_tests/real_world_tests/test_live_endpoints.py
python new_tests/real_world_tests/test_onboarding_conversation.py
```

### Clean Test Data
```bash
# Clean up any test user data
python new_tests/real_world_tests/cleanup_test_user.py
```

## 🔄 Development Workflow

### 1. Create Feature Branch
```bash
git checkout -b feat/your-feature-name
```

### 2. Make Your Changes
- Edit code in the `src/` directory
- Follow existing code patterns
- Add tests for new functionality

### 3. Test Locally
```bash
# Test your specific changes
python new_tests/real_world_tests/test_live_endpoints.py

# Run full test suite
python new_tests/real_world_tests/run_all_tests.py
```

### 4. Submit Pull Request
```bash
# Push your branch
git push origin feat/your-feature-name

# Create PR through GitHub interface
# Maintainers will review and merge
```

### 5. After Merge
```bash
# Switch back to main and pull latest
git checkout main
git pull origin main

# Delete your feature branch
git branch -d feat/your-feature-name
```

## 📁 Key Files & Directories

### Core Application
- `src/main.py` - FastAPI application and endpoints
- `src/claude_agent.py` - AI conversation handling
- `src/simple_memory.py` - Conversation persistence
- `src/config.py` - Environment configuration

### Testing
- `new_tests/real_world_tests/` - Integration tests
- `test-suite/` - Unit tests
- `cleanup_test_user.py` - Test data cleanup

### Documentation
- `memory-bank/` - Project intelligence and context
- `docs/` - Technical documentation
- `DEVELOPER_SETUP_GUIDE.md` - This file

## 🛠️ Common Development Tasks

### Adding a New API Endpoint
1. Add endpoint function to `src/main.py`
2. Add any new database operations to appropriate modules
3. Create tests in `new_tests/real_world_tests/`
4. Test locally before submitting PR

### Modifying AI Behavior
1. Update prompts in `src/prompts.py`
2. Modify agent logic in `src/claude_agent.py`
3. Test with `test_onboarding_conversation.py`
4. Verify memory persistence works correctly

### Database Changes
1. **DO NOT** modify database schema directly
2. Discuss schema changes with maintainers first
3. Test with existing data structure
4. Use test user IDs for development

## 🔍 Debugging Tips

### Check Logs
```bash
# View application logs
tail -f logs/app.log  # If logging to file

# Check Heroku logs (read-only for developers)
# Ask maintainers for log access if needed
```

### Test Specific Components
```bash
# Test AI integration
python -c "from src.claude_agent import get_agent; print('✅ AI agent working')"

# Test database connection
python -c "from src.simple_memory import get_supabase_client; print('✅ Database connected')"

# Test environment variables
python -c "import os; print('✅ Anthropic key:', 'present' if os.getenv('ANTHROPIC_API_KEY') else 'missing')"
```

### Common Issues

**Import Errors**: Make sure you're in the project root and virtual environment is activated

**Database Connection**: Verify your `.env` file has correct Supabase credentials

**AI API Errors**: Check that `ANTHROPIC_API_KEY` is set correctly in `.env`

**Port Already in Use**: Kill existing processes or use a different port:
```bash
uvicorn src.main:app --reload --host localhost --port 8001
```

## 🚫 What Developers CANNOT Do

- **Deploy to production Heroku** (restricted to maintainers)
- **Modify production database schema** (discuss changes first)
- **Access production environment variables** (development only)
- **Push directly to main branch** (PRs required)

## 🤝 Getting Help

### Documentation
- Read the `memory-bank/` files for project context
- Check `docs/` for technical details
- Review existing tests for examples

### Communication
- Create GitHub issues for bugs or questions
- Use PR comments for code-specific discussions
- Ask maintainers for access to additional resources

### Testing Resources
- Use test user ID: `test-user-[your-name]`
- Clean up test data regularly
- Don't use production user data for testing

## ✅ Ready to Develop!

Once you've completed this setup:

1. ✅ Local server running on http://localhost:8000
2. ✅ Tests passing
3. ✅ Environment variables configured
4. ✅ Git workflow understood

You're ready to start contributing to Fridays at Four! 🎉

---

**Questions?** Create a GitHub issue or reach out to the maintainers.

**Security Reminder**: Never commit your `.env` file or share API keys publicly. 