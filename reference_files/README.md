# 🎨 Fridays at Four
### AI-Powered Creative Project Management Platform

[![Production Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)](https://app.fridaysatfour.co)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-blue)](https://fridays-at-four-c9c6b7a513be.herokuapp.com/health)
[![Frontend](https://img.shields.io/badge/Frontend-Next.js%2014-black)](https://app.fridaysatfour.co)
[![AI](https://img.shields.io/badge/AI-Claude%20API-orange)](https://www.anthropic.com/claude)

> Transform your creative dreams into reality with AI-powered coaching and human accountability partnerships.

**Fridays at Four** is a revolutionary platform that helps creative professionals like writers, designers, and entrepreneurs turn their passion projects into completed realities. Combining intelligent AI coaching with thoughtful human partnerships, we provide the structure, support, and accountability that creative minds need to thrive.

---

## ✨ Why Fridays at Four?

### 🎯 **The Creative Professional's Dilemma**
- **Tool Overwhelm**: Drowning in productivity apps that don't understand creative work
- **Isolation**: Working alone without peer support or accountability  
- **Inconsistent Momentum**: Starting projects but struggling to maintain progress
- **Generic Support**: One-size-fits-all solutions that miss the nuances of creative work

### 💡 **Our Solution: Human + AI Partnership**
- **Hai (AI Coach)**: Intelligent, context-aware creative partner with persistent memory
- **Human Accountability**: Weekly partner calls with fellow creatives
- **Project-Focused**: One meaningful project at a time, not endless task lists
- **Creative-Native**: Built specifically for the rhythms and challenges of creative work

---

## 🌟 Key Features

### 🤖 **Intelligent AI Coaching (Hai)**
- **Real-Time Streaming Conversations**: Modern chat experience with immediate feedback
- **Persistent Memory**: Remembers your project details, preferences, and progress across all sessions
- **Project-Aware Context**: Understands your specific creative challenges and goals
- **Natural Language**: Conversation-based interaction, not forms or complex UIs

### 🎪 **Streamlined Onboarding**
- **8-Topic Guided Conversation**: Professional project planning in ~10 minutes
- **Automatic Project Creation**: AI extracts structured project data from natural conversation
- **Progress Tracking**: Clear "Topic X of 8" indicators for user experience
- **Completion Detection**: Intelligent flow management with seamless transitions

### 🤝 **Human Accountability Partners**
- **Weekly 30-Minute Calls**: Scheduled accountability sessions
- **Thoughtful Matching**: Paired with fellow creatives based on project types and personalities
- **Flexible Communication**: Support for scheduling and conversation facilitation
- **Shared Understanding**: Partners who get the creative process and its unique challenges

### 📊 **Progress Intelligence**
- **Visual Momentum Tracking**: See your progress patterns over time
- **Milestone Recognition**: Celebrate achievements and maintain motivation
- **Pattern Insights**: AI identifies what works best for your creative rhythm
- **Long-term Visualization**: Track project evolution from conception to completion

---

## 🏗️ Architecture & Tech Stack

### **Backend** 
- **FastAPI** with Python 3.10+ (async-first architecture)
- **Direct Claude API Integration** (migrated from LangChain for 40-60% performance improvement)
- **Real-Time Streaming** with Server-Sent Events (SSE)
- **Enhanced Project APIs** with status tracking and task management
- **Supabase PostgreSQL** with auto-dependency creation patterns
- **JWT Authentication** with secure session management

### **Frontend**
- **Next.js 14** with React and TypeScript
- **Real-Time Chat Interface** with authentic streaming responses
- **Responsive Design** supporting desktop and mobile viewports
- **Supabase Auth Integration** with profile management
- **Modern UI/UX** optimized for creative workflows

### **AI & Intelligence**
- **Anthropic Claude API** for natural language processing
- **Conversation Memory System** with context persistence
- **Nightly Summarization** with automated daily processing
- **Map-Reduce Summarization** for large conversation processing  
- **Structured Project Updates** with JSON formatting for frontend integration
- **Intelligent Flow Detection** for onboarding completion
- **Auto-Dependency Creation** preventing database errors

### **Infrastructure**
- **Heroku Deployment** with manual release management
- **Dual Environment Setup**: Production and development isolation
- **GitHub Actions CI/CD** with automated testing
- **Environment Variable Management** via Heroku config
- **CORS Configuration** for secure cross-origin requests

---

## 🚀 Quick Start

### **Prerequisites**
- Python 3.10+
- Node.js 18+
- Supabase account
- Anthropic API key

### **1. Clone & Setup**
```bash
git clone https://github.com/your-org/fridays-at-four.git
cd fridays-at-four

# Backend setup
pip install -r requirements.txt
cp .env.example .env
# Add your API keys to .env
```

### **2. Environment Configuration**
```bash
# Required environment variables
ANTHROPIC_API_KEY=your_anthropic_key
SUPABASE_URL=your_supabase_url  
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_key
```

### **3. Database Setup**
```bash
# Install Supabase CLI
npm install -g supabase

# Run migrations
supabase db reset
```

### **4. Start Development**
```bash
# Backend (Terminal 1)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (Terminal 2) 
cd frontend  # or wherever your package.json is
npm install
npm run dev
```

### **5. Design Iteration Tool** 🎨
```bash
# Initialize the design iteration tool
python scripts/design_iteration_tool.py --init

# Start development with automatic screenshots
python scripts/design_iteration_tool.py --serve
```

---

## 📁 Project Structure

```
fridays-at-four/
├── 📂 src/                     # FastAPI backend
│   ├── main.py                 # FastAPI app & endpoints  
│   ├── claude_client_simple.py # Claude API integration
│   ├── simple_memory.py        # Conversation persistence
│   ├── project_planning.py     # Onboarding flow logic
│   ├── sql_tools.py           # Database utilities
│   └── prompts.py             # AI prompts & templates
│
├── 📂 memory-bank/             # Project intelligence docs
│   ├── projectbrief.md        # Foundation requirements  
│   ├── userJourney.md         # Complete UX intelligence
│   ├── systemPatterns.md      # Architecture patterns
│   └── progress.md            # Current status & milestones
│
├── 📂 test-suite/             # Comprehensive test coverage
│   ├── api/                   # API integration tests
│   ├── core/                  # Core functionality tests  
│   ├── db/                    # Database operation tests
│   └── integrations/          # End-to-end test flows
│
├── 📂 scripts/                # Development & deployment tools
│   ├── design_iteration_tool.py # Visual development workflow
│   └── prd.txt               # Product requirements document
│
├── 📂 supabase/               # Database schema & migrations  
│   └── migrations/           # SQL migration files
│
├── 📂 frontend/               # Next.js frontend (separate repo)
└── 📂 design_iterations/     # Visual development tracking
```

---

## 🧪 Testing & Quality

### **Test Coverage**
- **100% Real-World Verification**: All core functionality tested against production APIs
- **7 Comprehensive Test Suites**: From basic Claude integration to full user journeys  
- **18-Message Onboarding Simulation**: Complete user flow validation
- **Migration Verification**: LangChain → Claude API transition validated

### **Key Test Suites**
```bash
# Run all real-world tests
python -m pytest real_world_tests/ -v

# Specific test categories
python real_world_tests/test_onboarding_conversation.py    # Full user journey
python real_world_tests/test_claude_agent_integration.py  # AI integration  
python real_world_tests/test_database_integration.py      # Database operations
```

### **Performance Metrics**
- **Response Times**: <3 seconds for streaming first chunk
- **Database Operations**: Auto-dependency creation prevents foreign key errors
- **Memory Management**: Efficient conversation storage and retrieval
- **Error Handling**: Zero uncaught exceptions in production testing

---

## 🎯 Current Status: Backend Production Ready ✅

### **🏆 Major Milestones Completed**
- ✅ **Real-Time Streaming Integration**: Modern Claude API streaming fully operational
- ✅ **Professional Onboarding Flow**: 8-topic guided conversation system
- ✅ **Project Overview System**: AI-generated project planning with enhanced APIs
- ✅ **Daily Summarization**: Automated nightly conversation processing
- ✅ **Structured Project Updates**: JSON-formatted data for frontend integration
- ✅ **Backend Architecture**: Robust FastAPI system with Claude integration
- ✅ **Database Design**: Auto-dependency creation and relationship management
- ✅ **Memory System**: Conversation persistence with intelligent context management
- ✅ **100% Test Coverage**: All real-world test suites passing (49/49 tests)

### **🔄 In Progress**
- **RAG File Search**: Vector search + prompt caching architecture implementation
- **Project Build Flows**: User-guided project construction workflows
- **Welcome Flows**: User onboarding optimization and experience enhancement
- **Archetype Integration**: Personality-based AI adaptation system

### **⏳ Planned Features**
- **Partner Matching System**: Human accountability partner automation
- **Creativity Personality Test**: Viral user acquisition feature
- **Analytics Dashboard**: Progress tracking and insights visualization
- **Advanced Archetype Features**: Three-dimensional personalization system
- **Hai Evolution System**: Four natural relationship progression stages
- **Global Insights**: Cross-user AI learning and pattern recognition
- **Mobile Application**: Native iOS/Android apps with full feature parity

---

## 🛠️ Development Workflow

### **Using the Design Iteration Tool**
```bash
# Start development mode (servers + browser)
python scripts/design_iteration_tool.py --serve

# Capture design iterations
python scripts/design_iteration_tool.py --screenshot "homepage-v2"

# List all iterations  
python scripts/design_iteration_tool.py --list
```

### **Task Management**
This project uses [Task Master AI](https://github.com/iamserda/task-master-ai) for development workflow:

```bash
# View current tasks
task-master list

# Get next task to work on  
task-master next

# Start working on a task
task-master set-status --id=15 --status=in-progress

# Mark task complete
task-master set-status --id=15 --status=done
```

### **Memory Bank System**
Critical project intelligence is maintained in the `memory-bank/` directory:
- **Read these files first** when starting any development session
- **Auto-update protocol**: AI assistants must update Memory Bank after significant changes
- **Single source of truth** for project patterns, user insights, and technical decisions

---

## 📊 User Experience Intelligence

### **Target User Profile**
- **Demographics**: Late 20s to mid 40s, liberal arts background, tech-savvy but AI-ambivalent
- **Emotional State**: Successful but unfulfilled, seeking creative expression
- **Pain Points**: Tool overwhelm, isolation, inconsistent momentum, generic support
- **Success Metrics**: Project completion with emotional satisfaction and creative growth

### **Magic Moments We Preserve**
- **First Interaction**: AI asks about feelings and motivations, not just tasks
- **Memory Demonstration**: Hai remembers specific project details across sessions  
- **Partner Connection**: Shared creative struggles with professional support
- **Progress Recognition**: Small wins celebrated, patterns recognized, momentum visible

### **Design Principles**
- **Keep It Human**: Natural conversation, emotional expression, authentic moments
- **Show Progress**: Visible momentum, meaningful metrics, milestone celebration  
- **Maintain Flexibility**: Adapt to rhythms, allow goal adjustment, multiple paths
- **Preserve Magic**: Personal touches, AI naturalness, discovery moments

---

## 🤝 Contributing

### **Development Setup**
1. Read the **Memory Bank** files in `memory-bank/` (essential for context)
2. Follow the **Task Master workflow** for structured development
3. Use the **Design Iteration Tool** for UI/UX changes
4. Maintain **100% test coverage** for new features
5. Update **Memory Bank** files after significant changes

### **Code Quality Standards**
- **Type hints** throughout Python codebase
- **Comprehensive error logging** with context
- **Async/await** for all I/O operations  
- **Environment isolation** (never hardcode secrets)
- **Real-world testing** against production APIs

### **Pull Request Process**
1. Create feature branch from `dev`
2. Implement changes with tests
3. Update relevant Memory Bank documentation
4. Submit PR with comprehensive description
5. Ensure all CI/CD checks pass

---

## 📞 Connect & Support

### **Live Platform**
- **Production**: [app.fridaysatfour.co](https://app.fridaysatfour.co)
- **Development**: [dev.fridaysatfour.co](https://dev.fridaysatfour.co)
- **Backend API**: [fridays-at-four-c9c6b7a513be.herokuapp.com](https://fridays-at-four-c9c6b7a513be.herokuapp.com)

### **Project Links**
- **GitHub**: [Organization Repository](https://github.com/your-org/fridays-at-four)
- **Documentation**: See `memory-bank/` directory for comprehensive project intelligence
- **Issues**: GitHub Issues for bug reports and feature requests

---

## 📜 License

This project is proprietary software. All rights reserved.

---

<div align="center">

**🎨 Fridays at Four** • *Where Creative Dreams Become Reality*

*Built with ❤️ for the creative community*

[![Production](https://img.shields.io/badge/🚀-Live%20Production-brightgreen)](https://app.fridaysatfour.co)
[![API Health](https://img.shields.io/badge/⚡-API%20Healthy-blue)](https://fridays-at-four-c9c6b7a513be.herokuapp.com/health)

</div>

