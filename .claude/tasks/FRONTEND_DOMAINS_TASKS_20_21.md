# Frontend Domains Implementation Plan - Tasks 20 & 21

## Mission Statement
Implement complete frontend domain ownership for safety moderation features (Task 20) and location privacy controls (Task 21) in parallel, using domain-based agent workflow with Next.js + Chakra UI patterns.

## Domain Architecture Analysis

### **Task 20 Domain: Safety & Moderation Frontend**
- **Scope**: Complete safety UI system with user protection features
- **Components**: Safety tips modal, report/block UI, admin moderation interface
- **Integration Points**: User onboarding flow, chat system, admin dashboard
- **Security Focus**: Professional moderation tools, user safety feedback
- **Patterns**: Modal systems, table interfaces, action feedback

### **Task 21 Domain: Location Privacy Frontend**
- **Scope**: Complete location privacy control system
- **Components**: Privacy toggles, settings documentation, preference management
- **Integration Points**: Profile setup flow, settings page, preference storage
- **Privacy Focus**: Clear privacy controls, user education, granular permissions
- **Patterns**: Toggle controls, settings pages, preference forms

## Technical Architecture Foundation

### **Existing Patterns to Follow**
```typescript
// From app/profile-setup/page.tsx - Form patterns
- React Hook Form + Zod validation
- Chakra UI Card layouts with sections
- Progressive enhancement (auth guards → form → submission)
- Error handling with toast notifications
- Loading states with CircularProgress

// From app/confidence-test/page.tsx - Modal patterns  
- Multi-screen flows with state management
- Progress indicators and navigation
- Card-based question/answer interfaces
- Professional UI with brand colors

// From components/LocationCapture.tsx - Toggle patterns
- Switch components with helper text
- Privacy mode explanations
- Alert components for status feedback
- Tooltip documentation for features
```

### **Established Design System**
```typescript
// Brand Colors (from existing codebase)
brand.50, brand.100, brand.400, brand.900 // Primary palette
gray.200, gray.500, gray.600 // Neutral palette

// Component Patterns
Card + CardBody (p={8}) // Main content containers
VStack spacing={6} // Vertical layouts
HStack // Horizontal layouts with icons
Button colorScheme="brand" bg="brand.900" // Primary actions
Alert status="error|success|info" // Status feedback
Badge variant="solid|outline" // Status indicators
```

## Task 20: Safety & Moderation Frontend Domain

### **1. Safety Tips Modal System**
```typescript
// Component: components/SafetyTipsModal.tsx
interface SafetyTipsModalProps {
  isOpen: boolean
  onClose: () => void
  onComplete: () => void
  showBeforeFirstSession?: boolean
}

// Features:
- Multi-step safety education flow
- First-time user targeting
- Progress tracking through tips
- Integration with session creation flow
- Professional, non-alarming tone
```

### **2. Report & Block UI Components**
```typescript
// Component: components/ReportBlockActions.tsx  
interface ReportBlockActionsProps {
  targetUserId: string
  targetType: 'user' | 'message' | 'session'
  onReportSuccess: () => void
  onBlockSuccess: () => void
}

// Features:
- Quick report button with reason selection
- Block user functionality with confirmation
- Integration with chat and profile pages
- Toast feedback for actions taken
- Clear escalation paths
```

### **3. Admin Moderation Interface**
```typescript
// Page: app/admin/moderation/page.tsx
// Component: components/admin/ModerationTable.tsx

// Features:
- Report review table with filtering
- User action history timeline
- Bulk moderation actions
- Status tracking (pending → reviewed → resolved)
- Admin-only access with role verification
```

### **4. User Safety Feedback System**
```typescript
// Component: components/SafetyFeedbackWidget.tsx

// Features:
- Post-action confirmation messages
- Educational content delivery
- Safety resource links
- Follow-up action suggestions
```

## Task 21: Location Privacy Frontend Domain

### **1. Enhanced Profile Setup Privacy Controls**
```typescript
// Update: app/profile-setup/page.tsx
// Component: components/EnhancedLocationPrivacy.tsx

// Features:
- Extended LocationCapture with more granular controls
- "Use precise location" vs "Use city-only centroid" options
- Adjustable radius preferences with privacy implications
- Visual privacy impact indicators
```

### **2. Settings Page Privacy Documentation**
```typescript
// Page: app/settings/privacy/page.tsx
// Components: components/settings/LocationPrivacySettings.tsx

// Features:
- Comprehensive privacy settings interface
- Location data usage explanations
- Historical location data management
- Privacy policy integration
- Data export/deletion options
```

### **3. Profile Privacy Toggle Integration**
```typescript
// Update: components/LocationCapture.tsx
// Add: components/LocationPrivacyExplainer.tsx

// Features:
- Enhanced privacy mode switching
- Real-time privacy impact feedback
- Location accuracy trade-off visualization
- Educational tooltips and help text
```

### **4. Preference Management System**
```typescript
// Component: components/LocationPreferences.tsx

// Features:
- Radius adjustment with privacy implications
- Location sharing preferences
- Match quality vs privacy trade-offs
- Saved preference profiles
```

## Implementation Strategy - Domain-Based Approach

### **Phase 1: Foundation Components (Parallel Development)**

**Safety Domain Agent Tasks:**
```typescript
1. SafetyTipsModal.tsx - Multi-step safety education
2. ReportBlockActions.tsx - User reporting interface
3. SafetyFeedbackWidget.tsx - Action confirmation system
4. Safety context provider and hooks
```

**Location Privacy Domain Agent Tasks:**
```typescript
1. EnhancedLocationPrivacy.tsx - Extended privacy controls
2. LocationPrivacySettings.tsx - Settings page component
3. LocationPrivacyExplainer.tsx - Educational component
4. Privacy preferences management system
```

### **Phase 2: Page Integration (Parallel Development)**

**Safety Domain Integration:**
```typescript
1. app/admin/moderation/page.tsx - Admin interface
2. Integration with chat pages for reporting
3. Integration with profile pages for blocking
4. Safety modal integration with onboarding
```

**Location Privacy Integration:**
```typescript
1. app/settings/privacy/page.tsx - Privacy settings page
2. Enhanced profile-setup integration
3. Settings navigation and page structure
4. Profile privacy status indicators
```

### **Phase 3: System Integration & Testing**

**Cross-Domain Integration Points:**
```typescript
1. Auth context integration for both domains
2. Toast notification system coordination
3. Database operation alignment
4. Error handling consistency
5. Mobile responsive verification
```

## Quality Requirements Implementation

### **Accessibility Standards (WCAG 2.1 AA)**
```typescript
// All components must include:
- Proper ARIA labels and roles
- Keyboard navigation support
- Screen reader compatibility
- Color contrast compliance
- Focus management in modals
```

### **Professional UI/UX Standards**
```typescript
// Safety-critical features require:
- Non-alarming, supportive tone
- Clear action feedback
- Professional moderation interface
- User-friendly privacy explanations
- Consistent with existing brand theme
```

### **Mobile-Responsive Design**
```typescript
// All components must work across:
- Mobile phones (320px+)
- Tablets (768px+) 
- Desktop (1024px+)
- Using Chakra UI responsive patterns
```

## Integration Points & Dependencies

### **Authentication Context**
```typescript
// Both domains require:
- User authentication verification
- Role-based access control (admin features)
- User session management
- Permission validation
```

### **Database Operations**
```typescript
// Safety domain database needs:
- User reports table operations
- Block list management
- Moderation action logging
- Safety tip completion tracking

// Privacy domain database needs:
- User preference storage
- Location privacy settings
- Historical privacy choices
- Settings change audit trail
```

### **Backend API Coordination**
```typescript
// Safety APIs:
POST /api/safety/report - Report user/content
POST /api/safety/block - Block user
GET /api/admin/reports - Get reports (admin)
PUT /api/admin/reports/{id} - Update report status

// Privacy APIs:
PUT /api/user/privacy/location - Update location privacy
GET /api/user/privacy/settings - Get privacy settings
POST /api/user/privacy/export - Export user data
DELETE /api/user/privacy/data - Delete location data
```

## Success Criteria & Deliverables

### **Task 20 Deliverables:**
1. ✅ Complete safety tips modal system
2. ✅ Professional admin moderation interface
3. ✅ User report/block UI integrated in chat/profile
4. ✅ Safety feedback system with user education
5. ✅ Mobile-responsive design across all safety features

### **Task 21 Deliverables:**
1. ✅ Enhanced location privacy controls in profile setup
2. ✅ Comprehensive settings page with privacy documentation
3. ✅ Granular location preference management
4. ✅ Educational privacy impact explanations
5. ✅ Integration with existing profile setup flow

### **Cross-Domain Success Metrics:**
1. ✅ WCAG 2.1 AA accessibility compliance
2. ✅ 100% mobile responsive across all screen sizes
3. ✅ Consistent with existing Chakra UI patterns
4. ✅ Professional UI/UX for safety-critical features
5. ✅ Complete integration with authentication and backend APIs

## Development Timeline

### **Week 1: Foundation (Parallel)**
- Safety domain: Core modal and report components
- Privacy domain: Enhanced privacy controls and settings

### **Week 2: Integration (Parallel)**
- Safety domain: Admin interface and system integration
- Privacy domain: Settings page and preference management

### **Week 3: Polish & Testing**
- Cross-domain integration testing
- Accessibility compliance verification
- Mobile responsive testing
- User experience validation

## Technical Debt Prevention

### **Code Quality Standards**
```typescript
// All components must include:
- TypeScript strict mode compliance
- Comprehensive JSDoc documentation
- Unit test coverage (Jest/React Testing Library)
- Integration test scenarios
- Performance optimization (React.memo, useCallback)
```

### **Architecture Principles**
```typescript
// Follow established patterns:
- Component composition over inheritance
- Custom hooks for shared logic
- Context providers for cross-component state
- Consistent error boundary implementation
- Proper loading state management
```

This plan ensures complete frontend domain ownership for both safety moderation and location privacy features, delivered in parallel using the proven domain-based agent workflow approach while maintaining the high quality standards established in the existing codebase.