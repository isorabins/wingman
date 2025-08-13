# WingmanMatch Database Schema Summary
**Generated**: August 13, 2025  
**Source**: schema_9_13.json + migrations analysis

## 📊 **Core Tables Overview**

### **User Management**
- `user_profiles` - Main user table with bio, photo_url, experience_level, confidence_archetype
- `user_locations` - Geographic data with lat/lng, city, max_travel_miles, privacy_mode
- `dating_goals` - User goals, preferred venues, comfort levels

### **Confidence Assessment System**
- `confidence_test_results` - Assessment results with test_responses (JSONB), archetype_scores (JSONB), assigned_archetype, experience_level
- `confidence_test_progress` - Session tracking with thread_id, flow_step, current_responses (JSONB), completion_percentage

### **Buddy Matching System**
- `wingman_matches` - Buddy partnerships with user1_id, user2_id, status, reputation scores
- `approach_challenges` - Available challenges by difficulty level (beginner/intermediate/advanced)
- `wingman_sessions` - Meetup sessions with challenge_ids, venue_name, completion status

## 🔗 **Foreign Key Relationships**

```
user_profiles (1) → (many) dating_goals
user_profiles (1) → (many) confidence_test_results  
user_profiles (1) → (many) user_locations
user_profiles (1) → (many) wingman_matches (as user1 or user2)

wingman_matches (1) → (many) wingman_sessions
approach_challenges (1) → (many) wingman_sessions (as user1/user2 challenges)
```

## ✅ **Task 7 Implementation Status**

### **Fully Operational:**
- ✅ `user_profiles` table with bio and photo_url fields
- ✅ `user_locations` table with privacy_mode column added
- ✅ Supabase Storage bucket 'profile-photos' with RLS policies
- ✅ Complete profile setup API and frontend

### **Ready for Implementation:**
- 🟡 `wingman_matches` - Ready for buddy matching algorithm (Task 8)
- 🟡 `approach_challenges` - Ready for challenge system (Task 9)
- 🟡 `wingman_sessions` - Ready for session coordination (Task 10)

## 🗃️ **Storage Configuration**

### **Supabase Storage Buckets:**
- `profile-photos` - User profile images with RLS policies
  - Path structure: `{user_id}/{timestamp}_{random}.{ext}`
  - Size limit: 5MB per file
  - Allowed types: image/jpeg, image/png, image/webp, image/gif
  - Security: User-scoped access with RLS policies

## 🔐 **Security Features**

### **Row Level Security (RLS):**
- ✅ All tables have RLS enabled
- ✅ User-scoped access policies (users can only access their own data)
- ✅ Wingman match participants can view each other's profiles
- ✅ Storage bucket policies prevent cross-user access

### **Data Privacy:**
- ✅ Location privacy_mode: 'precise' vs 'city_only'
- ✅ PII detection in bio validation
- ✅ File upload security with MIME type validation

## 📋 **Migration History**

1. **001_add_wingman_tables.sql** - Core WingmanMatch tables and indexes
2. **002_add_confidence_test_progress.sql** - Assessment progress tracking  
3. **003_add_storage_setup.sql** - Storage bucket and privacy_mode column

## 🚀 **Next Steps for Testing**

With your current database setup, you can now:

1. **Test Profile Setup** - Complete profiles with photo upload
2. **Test Confidence Assessment** - 12-question assessment flow
3. **Deploy to Production** - Heroku backend + Vercel frontend
4. **Implement Buddy Matching** - Use geographic data from user_locations

---

**Database Health**: ✅ All tables operational with proper RLS policies  
**API Integration**: ✅ Profile completion endpoint ready  
**Frontend**: ✅ Complete profile setup page functional  
**Storage**: ✅ Photo upload system with security validation