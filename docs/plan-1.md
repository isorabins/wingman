# WingmanMatch MVP Product Requirements Document
## Complete Product Specification & Implementation Guide

---

## 1. PRODUCT VISION

### What is WingmanMatch?

WingmanMatch is a mobile-first web app that helps men overcome approach anxiety by connecting them with local accountability partners (wingmen) for real-world practice. Think of it as "workout buddies but for dating confidence."

**The Core Problem:** Men want to approach women but freeze up when alone. They need:
- Someone to go with them (accountability)
- Structured challenges to follow (progression)
- A coach who understands their specific fears (personalization)

**Our Solution:** 
- Match users with compatible wingmen nearby
- Provide graduated challenges (like Duolingo for dating)
- Offer 24/7 AI coaching from "Connell Barrett" (dating coach persona)

### Target User

**Primary Persona: "Anxious Alex"**
- Male, 22-35 years old
- Lives in urban/suburban area
- Has tried dating apps, wants real-world connections
- Goes to gym, understands accountability partners
- Income: $40-80K (can afford $15/month eventually)
- Pain point: "I know what to do, I just can't do it alone"

**Secondary Persona: "Mentor Mike"**
- Male, 28-40 years old  
- Has some dating success, wants to help others
- Enjoys coaching/mentoring
- Sees this as personal development
- May become paid coaches in future versions

---

## 2. CORE FUNCTIONALITY

### 2.1 User Journey Map

```
DISCOVER → ASSESS → MATCH → PLAN → EXECUTE → REFLECT
```

**1. DISCOVER (Landing Page)**
- User learns about the app
- Sees testimonials/success stories
- Understands the concept
- Signs up

**2. ASSESS (Onboarding)**
- Takes confidence assessment (12 questions)
- Gets confidence archetype result
- Completes wingman profile (8 topics)
- Allows location access

**3. MATCH (Find Wingman)**
- Sees nearby potential wingmen
-only igven the choice of one, so its an instant match, because we dont 
want it to be like a dating app where you're swiping. so we'll filter by 
location and vibe 
- Sends connection requests


**4. PLAN (Session Planning)**
- Matched wingmen coordinate meeting
- Choose venue (coffee shop, mall, bookstore)
- Select challenge level
    -only given one challenge for the day that they need to do 
- Set time and date

**5. EXECUTE (Live Session)**
- Check in at location
- Complete challenges together
-they both mark its complete for the other person
- Support each other
- Log attempts and outcomes

**6. REFLECT (Post-Session)**
- Rate the session
- Log what worked/didn't work
- Earn XP and level up
- Plan next session

### 2.2 Key Features for MVP

#### Feature 1: Confidence Assessment
**What it does:** 12-question quiz that determines user's "approach archetype"

**Archetypes:**
- **The Overthinker** - Analyzes every scenario, paralyzed by possibilities
- **The Sprinter** - High energy start, burns out quickly  
- **The Ghost** - Disappears when it's time to approach
- **The Scholar** - Knows all the theory, can't apply it
- **The Natural** - Has moments of confidence but inconsistent
- **The Protector** - Makes excuses to "protect" women from being bothered

**Purpose:** 
- Gives users identity/belonging
- Personalizes Connell's coaching
- Matches compatible wingman types

#### Feature 2: Wingman Matching
**What it does:** Connects users with compatible accountability partners nearby

**Matching Criteria (MVP):**
- Distance (within X miles)
- Availability (overlapping free times)
- Confidence level (similar or complementary)
- Goals (what they want to achieve)

**Match Flow:**
1. User sees list of potential wingmen
2. Views basic profile (first name, distance, level, bio)
3. Sends "Connect" request
4. If accepted, can message and plan session

#### Feature 3: Challenge System
**What it does:** Graduated challenges that build confidence progressively

**Challenge Levels:**
```
Level 1: Foundation (No approach required)
- Make eye contact with 5 people
- Smile at 3 strangers
- Say "good morning" to 3 people

Level 2: Warm-ups (Simple interactions)
- Ask 3 people for the time
- Give 3 genuine compliments
- Ask for directions

Level 3: Conversations (Extended interaction)
- Have a 2-minute conversation
- Make someone laugh
- Share something about yourself

Level 4: Connections (Approach skills)
- Start conversation with someone attractive
- Exchange contact information
- Suggest meeting again

Level 5: Mastery (Advanced)
- Approach in difficult situations
- Handle rejection gracefully
- Help wingman approach
```

**Progression Mechanics:**
- Must complete 3 challenges at current level to unlock next
- Can repeat challenges for practice
- Earn XP for each completion
- Bonus XP for helping wingman complete

#### Feature 4: Connell AI Coach
**What it does:** AI dating coach available 24/7 for advice and support

**Personality:** 
- Based on real dating coach Connell Barrett
- Direct, supportive, no-BS approach
- Focuses on authenticity over "pickup techniques"
- Remembers all previous conversations

**Use Cases:**
- Pre-session pep talks
- Post-rejection support
- Analyzing what went wrong/right
- Answering dating questions
- Accountability check-ins

**Sample Interactions:**
```
User: "I froze up again today"
Connell: "That's tough, brother. But here's the thing - you showed up. That's more than 90% of guys do. Tell me, what was going through your head right before you froze?"

User: "She's out of my league"
Connell: "League? We're not playing baseball here. You're creating a story in your head about her before she's said a word. Your job isn't to decide if you're good enough for her - it's to find out if she's interesting enough for you."
```

#### Feature 5: Session Coordination
**What it does:** Helps wingmen plan and execute practice sessions

**Session Flow:**
1. **Schedule:** Pick date, time, location
2. **Prepare:** Choose challenges, review tips
3. **Execute:** Check in at location, track progress
4. **Debrief:** Rate session, log learnings

**Session Types (MVP):**
- **Coffee Shop Session** - Low pressure, daytime
- **Bookstore Session** - Easy conversation starters
- **Mall Session** - High traffic, lots of practice
- **Bar Session** - Evening, social atmosphere (Phase 2)

---

## 3. DESIGN & USER INTERFACE

### 3.1 Design Principles

**Overall Aesthetic:** Clean, masculine, confidence-inspiring
- **NOT** like dating apps (no pink, no hearts, no romance imagery)
- **MORE** like fitness apps (achievement, progress, strength)

**Color Palette:**
```
Primary: #1a1a1a (Near black)
Secondary: #2563eb (Confident blue) 
Accent: #10b981 (Success green)
Warning: #ef4444 (Challenge red)
Background: #fafafa (Off white)
Text: #374151 (Dark gray)
```

**Typography:**
- Headers: Inter or SF Pro Display (clean, modern)
- Body: System fonts (fast loading)
- Emphasis: Bold weight for confidence

### 3.2 Key Screens

#### Screen 1: Dashboard (Home)
```
┌─────────────────────────────┐
│  Hi [Name] 👋               │
│  Level 3 Challenger          │
│  ━━━━━━━━━━━━━━━━━ 65%      │
│                              │
│  📍 3 wingmen nearby         │
│  🎯 Today's challenge ready  │
│  🔥 5 day streak            │
│                              │
│  ┌──────────────────────┐    │
│  │  Find Wingman        │    │
│  └──────────────────────┘    │
│                              │
│  ┌──────────────────────┐    │
│  │  Quick Challenge     │    │
│  └──────────────────────┘    │
│                              │
│  ┌──────────────────────┐    │
│  │  Talk to Connell     │    │
│  └──────────────────────┘    │
│                              │
│  [Bottom Nav Bar]            │
└─────────────────────────────┘
```

#### Screen 2: Find Wingman
```
┌─────────────────────────────┐
│  Nearby Wingmen              │
│  ─────────────────────────   │
│                              │
│  ┌──────────────────────┐    │
│  │ Jake                 │    │
│  │ 2.3 miles • Level 4  │    │
│  │ "Looking to practice │    │
│  │  at coffee shops"    │    │
│  │         [Connect]    │    │
│  └──────────────────────┘    │
│                              │
│  ┌──────────────────────┐    │
│  │ Marcus               │    │
│  │ 3.1 miles • Level 2  │    │
│  │ "New to this, need   │    │
│  │  accountability"     │    │
│  │         [Connect]    │    │
│  └──────────────────────┘    │
│                              │
│  ┌──────────────────────┐    │
│  │ David                │    │
│  │ 4.5 miles • Level 5  │    │
│  │ "Happy to mentor"    │    │
│  │         [Connect]    │    │
│  └──────────────────────┘    │
└─────────────────────────────┘
```

#### Screen 3: Active Session
```
┌─────────────────────────────┐
│  Session Active 🔴           │
│  Coffee Shop Challenge       │
│  ─────────────────────────   │
│                              │
│  You + Marcus                │
│  📍 Starbucks on Main St     │
│                              │
│  Today's Challenges:         │
│  ┌──────────────────────┐    │
│  │ ✓ Eye contact (5)    │    │
│  └──────────────────────┘    │
│  ┌──────────────────────┐    │
│  │ ⭕ Compliments (1/3) │    │
│  └──────────────────────┘    │
│  ┌──────────────────────┐    │
│  │ ⭕ Ask for time (0/3)│    │
│  └──────────────────────┘    │
│                              │
│  ┌──────────────────────┐    │
│  │   Need Pep Talk?     │    │
│  │   💬 Ask Connell     │    │
│  └──────────────────────┘    │
│                              │
│  [End Session]               │
└─────────────────────────────┘
```

#### Screen 4: Chat with Connell
```
┌─────────────────────────────┐
│  Connell 🎯                  │
│  ─────────────────────────   │
│                              │
│  ┌──────────────────────┐    │
│  │ Hey brother! Ready to │    │
│  │ build some confidence │    │
│  │ today?               │    │
│  │                      │    │
│  │ What's on your mind? │    │
│  └──────────────────────┘    │
│                              │
│  ┌──────────────────────┐    │
│  │ I get nervous when I │    │
│  │ see someone I want   │    │
│  │ to talk to           │    │
│  └──────────────────────┘    │
│                              │
│  ┌──────────────────────┐    │
│  │ That's completely    │    │
│  │ normal. Your brain   │    │
│  │ is trying to protect │    │
│  │ you from rejection.  │    │
│  │                      │    │
│  │ Here's the thing...  │    │
│  └──────────────────────┘    │
│                              │
│  [Type message...]           │
└─────────────────────────────┘
```

### 3.3 Navigation Structure

```
Bottom Tab Navigation:
├── Home (Dashboard)
├── Wingmen (Find/Manage)
├── Challenges (Browse/Track)
├── Chat (Connell)
└── Profile (Settings/Progress)
```

---

## 4. TECHNICAL ARCHITECTURE

### 4.1 System Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Next.js   │────▶│   Python    │────▶│  Supabase   │
│   Frontend  │     │   Backend   │     │  Database   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Claude AI  │
                    │  (Connell)  │
                    └─────────────┘
```

### 4.2 Tech Stack (Reusing F@4)

**Frontend:**
- Next.js 14 (existing)
- TypeScript (existing)
- Tailwind CSS (existing)
- Supabase Client (existing)

**Backend:**
- Python FastAPI (existing)
- Claude AI integration (existing)
- Redis for sessions (existing)
- Background jobs (existing)

**Database:**
- Supabase PostgreSQL (existing)
- Row Level Security (existing)
- Real-time subscriptions (existing)

**Infrastructure:**
- Vercel (frontend hosting)
- Railway/Render (backend hosting)
- Supabase (database & auth)
- Resend (email)

### 4.3 Database Schema

```sql
-- Users (modified creator_profiles)
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    
    -- New fields for WingmanMatch
    confidence_archetype VARCHAR(50),
    confidence_level INTEGER DEFAULT 1,
    location_lat DECIMAL(10, 8),
    location_lng DECIMAL(11, 8),
    city VARCHAR(100),
    max_travel_miles INTEGER DEFAULT 10,
    bio TEXT,
    availability JSONB, -- {monday: ["evening"], tuesday: ["morning", "evening"], ...}
    goals TEXT[],
    
    -- Stats
    sessions_completed INTEGER DEFAULT 0,
    challenges_completed INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    total_xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Wingman Matches
CREATE TABLE wingman_matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    requester_id UUID REFERENCES users(id),
    responder_id UUID REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'pending', -- pending, accepted, rejected, expired
    message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    responded_at TIMESTAMP,
    UNIQUE(requester_id, responder_id)
);

-- Challenges
CREATE TABLE challenges (
    id SERIAL PRIMARY KEY,
    level INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50), -- foundation, warmup, conversation, connection, mastery
    xp_reward INTEGER DEFAULT 10,
    tips TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- User Challenge Progress
CREATE TABLE user_challenges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    challenge_id INTEGER REFERENCES challenges(id),
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    session_id UUID,
    notes TEXT,
    difficulty_rating INTEGER, -- 1-5, how hard was it
    UNIQUE(user_id, challenge_id, session_id)
);

-- Sessions
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user1_id UUID REFERENCES users(id),
    user2_id UUID REFERENCES users(id),
    scheduled_for TIMESTAMP,
    location_name VARCHAR(200),
    location_lat DECIMAL(10, 8),
    location_lng DECIMAL(11, 8),
    status VARCHAR(20) DEFAULT 'scheduled', -- scheduled, active, completed, cancelled
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    user1_rating INTEGER,
    user2_rating INTEGER,
    user1_notes TEXT,
    user2_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Chat Messages (reuse existing)
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sender_id UUID REFERENCES users(id),
    recipient_id UUID REFERENCES users(id),
    content TEXT NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Confidence Assessment Results
CREATE TABLE assessment_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) UNIQUE,
    responses JSONB NOT NULL, -- {q1: "A", q2: "B", ...}
    archetype VARCHAR(50) NOT NULL,
    strengths TEXT[],
    growth_areas TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 4.4 API Endpoints

**Authentication (existing):**
- `POST /api/auth/signup`
- `POST /api/auth/login`
- `POST /api/auth/logout`

**User Profile:**
- `GET /api/user/profile`
- `PUT /api/user/profile`
- `POST /api/user/location`

**Assessment:**
- `POST /api/assessment/confidence`
- `GET /api/assessment/results`

**Wingman Matching:**
- `GET /api/wingmen/nearby?lat={lat}&lng={lng}&radius={radius}`
- `POST /api/wingmen/connect`
- `PUT /api/wingmen/respond`
- `GET /api/wingmen/matches`

**Challenges:**
- `GET /api/challenges`
- `GET /api/challenges/current`
- `POST /api/challenges/complete`
- `GET /api/challenges/history`

**Sessions:**
- `POST /api/sessions/create`
- `PUT /api/sessions/start`
- `PUT /api/sessions/end`
- `POST /api/sessions/rate`
- `GET /api/sessions/upcoming`
- `GET /api/sessions/history`

**AI Coach:**
- `POST /api/coach/message` (existing, update prompts)
- `GET /api/coach/history` (existing)

---

## 5. IMPLEMENTATION PLAN

### 5.1 File Structure Changes

```
fridays-at-four/                    → wingman-match/
├── src/
│   ├── agents/
│   │   ├── creativity_agent.py     → confidence_agent.py
│   │   ├── project_overview.py     → wingman_profile.py
│   │   └── chat_agent.py          (update prompts only)
│   ├── api/
│   │   ├── existing/              (keep all)
│   │   └── wingman/               (NEW)
│   │       ├── matching.py
│   │       ├── sessions.py
│   │       └── challenges.py
│   └── prompts.py                 (update Hai → Connell)
├── app/
│   ├── page.tsx                   (update copy)
│   ├── creativity-test/            → confidence-test/
│   ├── chat/                       (keep, update UI)
│   └── wingmen/                    (NEW)
│       ├── page.tsx
│       ├── [id]/page.tsx
│       └── session/page.tsx
└── components/
    ├── existing/                   (keep all)
    └── wingman/                    (NEW)
        ├── WingmanCard.tsx
        ├── ChallengeCard.tsx
        ├── SessionTracker.tsx
        └── ProgressBar.tsx
```

### 5.2 Development Phases

#### Week 1: Backend Foundation
**Day 1-2:**
- Fork F@4 repository
- Update database schema
- Create migration scripts

**Day 3-4:**
- Modify confidence_agent.py
- Modify wingman_profile.py
- Update prompts for Connell

**Day 5:**
- Create matching.py
- Create basic distance algorithm
- Test matching logic

#### Week 2: Frontend MVP
**Day 6-7:**
- Update homepage copy
- Create confidence test
- Add location permission

**Day 8-9:**
- Build wingman list page
- Create connection flow
- Add basic messaging

**Day 10:**
- Create session planning
- Add challenge tracking
- Update navigation

#### Week 3: Integration & Polish
**Day 11-12:**
- Integration testing
- Bug fixes
- Performance optimization

**Day 13-14:**
- User acceptance testing
- Final polish
- Deployment preparation

**Day 15:**
- Deploy to production
- Monitor and fix issues

---

## 6. MVP CONSTRAINTS & DECISIONS

### What We're Building (MVP)
✅ Basic location-based matching (simple distance calculation)
✅ Text-based profiles (no photos yet)
✅ Manual session coordination (no real-time)
✅ Self-reported challenge completion
✅ Simple chat between matched wingmen
✅ AI coach with basic persona

### What We're NOT Building (Yet)
❌ Photo uploads and verification
❌ Background checks
❌ Real-time location sharing
❌ Video chat
❌ Payment processing
❌ Push notifications
❌ Complex matching algorithm
❌ Social features (comments, likes)
❌ Gamification (badges, leaderboards)

### Key Technical Decisions

**Why No Native App:**
- Faster to build PWA
- No app store approval needed
- Can iterate quickly
- Works on all devices

**Why Simple Distance Matching:**
- PostGIS is overkill for MVP
- Haversine formula is sufficient
- Can upgrade later if needed

**Why No Real-time Features:**
- Adds complexity
- Not needed for core value prop
- Can use polling for MVP

**Why No Payments:**
- Test value proposition first
- Reduce legal complexity
- Add when we have product-market fit

---

## 7. METRICS & SUCCESS CRITERIA

### MVP Success Metrics (Month 1)

**User Acquisition:**
- 200 signups
- 100 completed assessments (50% conversion)
- 50 active users (25% activation)

**Engagement:**
- 30 matched pairs
- 20 completed sessions
- 100+ challenges completed
- 40% week 1 retention

**Quality:**
- Average session rating: 4+ stars
- 20+ positive testimonials
- <5% reported issues/conflicts

### Key Performance Indicators

**Daily Active Users (DAU):**
- Target: 20% of registered users
- Measurement: Unique daily logins

**Matching Success Rate:**
- Target: 60% of connection requests accepted
- Measurement: Accepted / Total Requests

**Challenge Completion Rate:**
- Target: 3+ challenges per active user per week
- Measurement: Total completions / Active users

**Session Success Rate:**
- Target: 80% of scheduled sessions completed
- Measurement: Completed / Scheduled

**Connell Engagement:**
- Target: 5+ messages per user per week
- Measurement: Total messages / Active users

---

## 8. RISKS & MITIGATIONS

### Technical Risks

**Risk:** Location permissions denied
**Mitigation:** Fall back to city-level matching via input

**Risk:** Low user density in cities
**Mitigation:** Start in one city (Austin), expand gradually

**Risk:** Inappropriate behavior between users
**Mitigation:** Reporting system, ban functionality

### Product Risks

**Risk:** Users don't show up to sessions
**Mitigation:** Reminder emails, karma/reputation system

**Risk:** Mismatch in skill levels
**Mitigation:** Clear level indicators, separate mentor mode

**Risk:** Users want romantic matching, not wingman
**Mitigation:** Clear positioning, onboarding education

### Legal Risks

**Risk:** Liability for in-person meetings
**Mitigation:** Strong Terms of Service, liability waivers

**Risk:** Users are minors
**Mitigation:** Age verification in signup (18+ only)

---

## 9. FUTURE ROADMAP

### Phase 2 (Month 2) - Trust & Safety
- Photo uploads with basic verification
- Reporting and moderation system
- Emergency contact feature
- Session check-in system

### Phase 3 (Month 3) - Engagement
- Gamification (XP, levels, badges)
- Streak tracking
- Leaderboards (city-level)
- Challenge creation by users

### Phase 4 (Month 4) - Monetization
- Premium subscription ($14.99/month)
  - Unlimited matches
  - See who wants to connect
  - Advanced filters
  - Priority support
- Verified badge ($4.99 one-time)
- Coaching sessions ($50/hour)

### Phase 5 (Month 5-6) - Scale
- Multi-city expansion
- Native mobile apps
- Video chat integration
- Group sessions
- Mentor marketplace

---

## 10. APPENDIX

### A. Confidence Assessment Questions

1. **You see someone attractive at a coffee shop. What typically happens?**
   - A) I create elaborate scenarios in my head but never move
   - B) I approach immediately before I lose nerve
   - C) I wait for the "perfect moment" that never comes
   - D) I try to make eye contact first and gauge interest

2. **Your friend says "just be yourself" before an approach. Your thought?**
   - A) But which version of myself?
   - B) That's all I need to hear, let's go
   - C) Easy for them to say
   - D) I need more specific advice than that

3. **After a rejection, you typically:**
   - A) Analyze what went wrong for hours
   - B) Immediately approach someone else to shake it off
   - C) Go home and avoid approaching for weeks
   - D) Feel bad for 5 minutes then move on

4. **Your biggest fear about approaching is:**
   - A) Saying the wrong thing
   - B) Running out of energy mid-conversation
   - C) The actual moment of walking up
   - D) Not knowing enough techniques

5. **In social situations, you're most comfortable:**
   - A) Observing and planning
   - B) Being the center of attention briefly
   - C) Blending into the background
   - D) Having deep one-on-one conversations

[... 7 more questions]

### B. Challenge Examples by Level

**Level 1: Foundation**
- Make eye contact and smile (5 people)
- Say "good morning" to strangers (3 people)
- Ask someone for the time
- Hold door open and make eye contact
- Give a genuine compliment to a cashier

**Level 2: Warm-ups**
- Ask for directions (even if you know the way)
- Comment on something in the environment
- Ask for a recommendation (coffee, book, etc.)
- Make small talk in an elevator
- Compliment someone's style choice

**Level 3: Conversations**
- Have a 2-minute conversation with a stranger
- Make someone laugh
- Share a personal story
- Ask follow-up questions
- Exchange names with someone new

[... continues for Levels 4-5]

### C. Connell AI Personality Guide

**Core Traits:**
- Direct but warm
- Uses "brother" occasionally
- Sports and gym metaphors
- No pickup artist terminology
- Focuses on inner confidence
- Calls out excuses compassionately

**Sample Responses:**

*User: "She's out of my league"*
"League? This isn't baseball, brother. You're creating a story about her before she's even spoken. Your job isn't to decide if you're good enough - it's to find out if she's interesting enough for YOU."

*User: "What should I say?"*
"Stop trying to find the perfect words. You know how to have conversations - you do it every day. The only difference here is you find her attractive. Say literally anything observational: 'That looks like a good book' or 'This coffee shop is packed today.' The words don't matter, the energy does."

*User: "I got rejected hard"*
"Good. You know what that means? You actually tried. Most guys are sitting at home swiping on apps. You're out here taking real action. Rejection stings for about 5 minutes. Regret lasts forever. Which would you rather have?"

---

## END OF PRD

This PRD represents a complete MVP specification for WingmanMatch, adapted from the Fridays at Four infrastructure. Total development time: 2-3 weeks. Total new code: ~20%. Risk level: Low.