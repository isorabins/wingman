#!/usr/bin/env python3
"""
Needle in Haystack Caching Test

Tests Claude's ability to find specific information (needles) embedded in 
large documentation contexts (haystacks) while measuring caching performance.
"""

import os
import sys
import asyncio
import uuid
import time
import random
from datetime import datetime, timezone

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from supabase import create_client
from src.simple_memory import SimpleMemory
from src.config import Config
from src.context_formatter import format_static_context_for_caching, get_cache_control_header
from anthropic import AsyncAnthropic
import json

# Needle facts to embed in the haystack
NEEDLES = [
    {
        "fact": "The secret API rate limit for premium users is exactly 847 requests per minute.",
        "question": "What is the secret API rate limit for premium users?",
        "expected": "847 requests per minute"
    },
    {
        "fact": "The hidden database optimization flag is set to 'turbo_mode_delta_7'.",
        "question": "What is the hidden database optimization flag?",
        "expected": "turbo_mode_delta_7"
    },
    {
        "fact": "The emergency contact for system failures is Sarah Chen at extension 4472.",
        "question": "Who is the emergency contact for system failures and what is their extension?",
        "expected": "Sarah Chen at extension 4472"
    },
    {
        "fact": "The backup server cluster is located in datacenter zone 'Phoenix-Alpha-Nine'.",
        "question": "Where is the backup server cluster located?",
        "expected": "Phoenix-Alpha-Nine"
    },
    {
        "fact": "The special authentication token prefix for internal tools is 'FRID_INT_2025_'.",
        "question": "What is the special authentication token prefix for internal tools?",
        "expected": "FRID_INT_2025_"
    }
]

def create_haystack_content():
    """Create a large haystack of documentation with embedded needles"""
    
    # Base documentation content
    base_content = """
# Fridays at Four - Complete Technical Documentation

## System Architecture Overview
Fridays at Four is built on a modern, scalable architecture designed for creative professionals.
Our platform combines AI-powered conversation management with robust project tracking capabilities.

### Core Components
- **Frontend**: Next.js 14 with TypeScript and Tailwind CSS
- **Backend**: FastAPI with Python 3.11+ 
- **Database**: Supabase (PostgreSQL) with real-time subscriptions
- **AI Integration**: Claude Sonnet 3.5 with prompt caching optimization
- **Authentication**: Supabase Auth with JWT tokens
- **File Storage**: Supabase Storage for media and documents

### Database Schema Details
The system uses a carefully designed schema to support conversation memory,
project tracking, and user profile management. Key tables include:

#### Core Tables
- `creator_profiles`: User profile information and preferences
- `conversations`: All user-AI interactions with metadata
- `memory`: Structured conversation memory with relevance scoring
- `project_overview`: High-level project information and goals
- `project_updates`: Timestamped project progress entries
- `longterm_memory`: Summarized conversation history

#### Performance Optimizations
Our database layer implements several performance optimizations:
- Indexed queries on user_id and created_at fields
- Materialized views for complex aggregations  
- Connection pooling through Supabase
- Automated cleanup of old conversation data
"""

    # Generate filler content sections
    filler_sections = []
    
    # Add development workflow section with first needle
    filler_sections.append(f"""
## Development Workflow
The development process follows modern best practices with comprehensive testing.
We use GitHub Actions for CI/CD, automated testing, and deployment pipelines.
All code changes require peer review and must pass our test suite.

### System Configuration
{NEEDLES[0]['fact']}

### Testing Strategy
- Unit tests for individual components
- Integration tests for API endpoints
- End-to-end tests for user workflows
- Performance tests for optimization validation
- Security scans for vulnerability detection
""")

    # Add API documentation with second needle
    filler_sections.append(f"""
## API Documentation
Our FastAPI backend exposes several key endpoints for frontend integration.
All endpoints require proper authentication and follow RESTful conventions.

### Performance Settings
{NEEDLES[1]['fact']}

### Authentication Endpoints
- POST /auth/login - User authentication
- POST /auth/refresh - Token refresh
- POST /auth/logout - Session termination

### Conversation Endpoints  
- POST /chat - Send message to AI assistant
- POST /query_stream - Streaming conversation endpoint
- GET /chat-history/{{user_id}} - Retrieve conversation history
""")

    # Add operations section with third needle
    filler_sections.append(f"""
## Operations and Support
Our platform requires 24/7 monitoring and support capabilities.
We maintain comprehensive documentation for all operational procedures.

### Emergency Procedures
{NEEDLES[2]['fact']}

### Monitoring and Alerting
- Real-time security monitoring
- Automated threat detection
- Incident response procedures
- Regular backup verification

### Performance Optimization
The platform is optimized for speed and scalability across all components.
We continuously monitor and improve performance metrics.
""")

    # Add infrastructure section with fourth needle
    filler_sections.append(f"""
## Infrastructure and Deployment
Our platform is deployed across multiple regions for reliability and performance.
We maintain redundant systems and automated failover capabilities.

### Server Infrastructure
{NEEDLES[3]['fact']}

### Deployment Pipeline
- Automated CI/CD through GitHub Actions
- Blue-green deployment strategy
- Automated rollback capabilities
- Health check monitoring
""")

    # Add authentication section with fifth needle
    filler_sections.append(f"""
## Authentication and Security
Comprehensive security measures protect user data and system integrity.
We implement multiple layers of authentication and authorization.

### Internal Tool Access
{NEEDLES[4]['fact']}

### Security Protocols
- Multi-factor authentication required
- Regular security audits and penetration testing
- Encrypted data transmission and storage
- Role-based access control (RBAC)
""")

    # Add more filler content
    more_filler = """
## Security Considerations
Security is paramount in our platform design. We implement multiple layers
of protection to ensure user data remains safe and private.

### Data Protection
- All data encrypted at rest and in transit
- Regular security audits and penetration testing
- GDPR compliance for European users
- SOC 2 Type II certification in progress

### Access Controls
- Role-based access control (RBAC)
- Multi-factor authentication support
- Session timeout and refresh mechanisms
- API rate limiting and abuse prevention

## User Experience Design
Our UX design focuses on simplicity and effectiveness for creative professionals.
Every interaction is carefully crafted to support the creative process.

### Design Principles
- Minimal cognitive load
- Clear visual hierarchy
- Consistent interaction patterns
- Accessibility compliance (WCAG 2.1)

### User Research Insights
- Creative professionals value focused tools
- AI assistance should feel collaborative, not directive
- Progress visibility increases motivation
- Flexibility in workflow is essential

## Troubleshooting Guide
Common issues and their solutions for development and production environments.

### Database Connection Issues
- Verify Supabase credentials
- Check network connectivity
- Validate SSL certificates
- Review connection pool settings

### AI Integration Problems
- Confirm API key validity
- Check rate limit status
- Verify model availability
- Review prompt formatting

### Frontend Build Errors
- Clear node_modules and reinstall
- Update dependency versions
- Check TypeScript configuration
- Validate environment variables

## Future Roadmap
Planned enhancements and new features for the platform.

### Short-term Goals (Q1-Q2 2025)
- Enhanced AI conversation capabilities
- Improved project tracking features
- Mobile app development
- Advanced analytics dashboard

### Long-term Vision (2025-2026)
- Multi-language support
- Enterprise collaboration features
- Advanced AI model integration
- Marketplace for creative tools
"""
    
    return base_content + "\n".join(filler_sections) + more_filler

async def test_needle_haystack():
    """Test needle-in-haystack performance with caching"""
    
    print("🔍 Starting Needle-in-Haystack Caching Test")
    print(f"⏰ Test started at: {datetime.now()}")
    
    # Create test user
    test_user_id = str(uuid.uuid4())
    supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
    
    try:
        # Create memory handler and ensure profile exists
        memory_handler = SimpleMemory(supabase_client, test_user_id)
        await memory_handler.ensure_creator_profile(test_user_id)
        
        # Generate haystack content
        print("📚 Generating haystack content...")
        haystack_content = create_haystack_content()
        print(f"📊 Haystack size: {len(haystack_content):,} characters")
        
        # Create rich project overview with haystack
        project_data = {
            'user_id': test_user_id,
            'project_name': 'Fridays at Four - Technical Documentation Test',
            'project_type': 'Software Development',
            'description': haystack_content,
            'goals': ['Test needle-in-haystack performance', 'Validate caching efficiency'],
            'challenges': ['Information retrieval accuracy', 'Response time optimization'],
            'success_metrics': {'accuracy': '95%+', 'response_time': '<3s'},
            'current_phase': 'Testing Phase',
            'timeline': '2025 Q1',
            'working_style': 'Agile development with continuous testing'
        }
        
        print("💾 Storing project overview...")
        supabase_client.table('project_overview').insert(project_data).execute()
        
        # Initialize Claude client
        client = AsyncAnthropic(api_key=Config.ANTHROPIC_API_KEY)
        
        # Test each needle
        results = []
        
        for i, needle in enumerate(NEEDLES, 1):
            print(f"\n🎯 Testing Needle {i}/{len(NEEDLES)}: {needle['question']}")
            
            # Get formatted context (same way as claude_agent.py)
            caching_context = await memory_handler.get_caching_optimized_context("needle-test-thread")
            static_context = format_static_context_for_caching(caching_context["static_context"])
            
            # First call - should create cache
            start_time = time.time()
            
            response1 = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[
                    {
                        "role": "user", 
                        "content": [
                            {
                                "type": "text",
                                "text": static_context,
                                "cache_control": {"type": "ephemeral"}
                            },
                            {
                                "type": "text",
                                "text": f"Based on the documentation provided, please answer this question: {needle['question']}"
                            }
                        ]
                    }
                ],
                extra_headers=get_cache_control_header()
            )
            
            first_call_time = time.time() - start_time
            first_response = response1.content[0].text
            
            # Track cache metrics
            cache_creation = getattr(response1.usage, 'cache_creation_input_tokens', 0)
            cache_reads = getattr(response1.usage, 'cache_read_input_tokens', 0)
            
            print(f"   ⏱️  First call: {first_call_time:.2f}s")
            print(f"   🧠 Cache created: {cache_creation:,} tokens")
            print(f"   📖 Cache read: {cache_reads:,} tokens")
            print(f"   💬 Response preview: {first_response[:150]}...")
            
            # Second call - should use cache
            start_time = time.time()
            
            response2 = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[
                    {
                        "role": "user", 
                        "content": [
                            {
                                "type": "text",
                                "text": static_context,
                                "cache_control": {"type": "ephemeral"}
                            },
                            {
                                "type": "text",
                                "text": f"Based on the documentation provided, please answer this question: {needle['question']}"
                            }
                        ]
                    }
                ],
                extra_headers=get_cache_control_header()
            )
            
            second_call_time = time.time() - start_time
            second_response = response2.content[0].text
            
            cache_creation2 = getattr(response2.usage, 'cache_creation_input_tokens', 0)
            cache_reads2 = getattr(response2.usage, 'cache_read_input_tokens', 0)
            
            print(f"   ⏱️  Second call: {second_call_time:.2f}s")
            print(f"   🧠 Cache created: {cache_creation2:,} tokens")
            print(f"   📖 Cache read: {cache_reads2:,} tokens")
            print(f"   💬 Response preview: {second_response[:150]}...")
            
            # Analyze accuracy
            expected = needle['expected'].lower()
            found_in_first = expected in first_response.lower()
            found_in_second = expected in second_response.lower()
            
            performance_improvement = ((first_call_time - second_call_time) / first_call_time) * 100
            
            result = {
                'needle': needle['question'],
                'expected': needle['expected'],
                'first_call_time': first_call_time,
                'second_call_time': second_call_time,
                'performance_improvement': performance_improvement,
                'accuracy_first': found_in_first,
                'accuracy_second': found_in_second,
                'cache_creation': cache_creation,
                'cache_reads_total': cache_reads + cache_reads2,
                'first_response': first_response,
                'second_response': second_response
            }
            
            results.append(result)
            
            print(f"   ✅ Accuracy: First={found_in_first}, Second={found_in_second}")
            print(f"   🚀 Performance improvement: {performance_improvement:.1f}%")
            
            # Small delay between tests
            await asyncio.sleep(1)
        
        # Summary report
        print(f"\n🎉 Needle-in-Haystack Test Complete!")
        print(f"📊 Overall Results:")
        
        avg_first_time = sum(r['first_call_time'] for r in results) / len(results)
        avg_second_time = sum(r['second_call_time'] for r in results) / len(results)
        avg_improvement = sum(r['performance_improvement'] for r in results) / len(results)
        accuracy_first = sum(r['accuracy_first'] for r in results) / len(results) * 100
        accuracy_second = sum(r['accuracy_second'] for r in results) / len(results) * 100
        
        print(f"   ⏱️  Average first call time: {avg_first_time:.2f}s")
        print(f"   ⏱️  Average second call time: {avg_second_time:.2f}s")
        print(f"   🚀 Average performance improvement: {avg_improvement:.1f}%")
        print(f"   🎯 First call accuracy: {accuracy_first:.1f}%")
        print(f"   🎯 Second call accuracy: {accuracy_second:.1f}%")
        
        return results
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        # Cleanup
        print("🧹 Cleaning up test data...")
        cleanup_tables = [
            ('memory', 'user_id'),
            ('conversations', 'user_id'), 
            ('longterm_memory', 'user_id'),
            ('project_overview', 'user_id'),
            ('project_updates', 'user_id'),
            ('creator_profiles', 'id')
        ]
        
        for table, id_column in cleanup_tables:
            try:
                supabase_client.table(table).delete().eq(id_column, test_user_id).execute()
            except Exception as e:
                print(f"Cleanup error for {table}: {e}")

if __name__ == "__main__":
    asyncio.run(test_needle_haystack()) 