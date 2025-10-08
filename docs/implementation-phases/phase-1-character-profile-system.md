# Phase 1: Character & Profile System

**Timeline:** Weeks 1-2 (14 days)
**Status:** 🔄 IN PROGRESS - Day 2 Complete
**Started:** October 6, 2025
**Current Progress:** 2/10 steps complete (40%)

---

## 📊 Progress Overview

| Step | Status | Completion |
|------|--------|------------|
| Step 1: Database Setup | ✅ COMPLETE | 100% |
| Step 2: Backend API Endpoints | ✅ COMPLETE | 100% |
| Step 3: Character Selection UI | 🔄 STARTING NOW | 0% |
| Step 4: Profile Creation & Management | ⏳ Pending | 0% |
| Step 5: XP & Progression System | ⏳ Pending | 0% |
| Step 6: Achievement System | ⏳ Pending | 0% |
| Step 7: Social Features | ⏳ Pending | 0% |
| Step 8: Password Reset Flow | ⏳ Pending | 0% |
| Step 9: Onboarding Flow | ⏳ Pending | 0% |
| Step 10: Integration & Testing | ⏳ Pending | 0% |

**Overall Phase 1 Progress:** 40% Complete

---

## 🎯 Completed Work

### ✅ Step 1: Database Setup (100% Complete) - Oct 6

- Database schema with 9 tables
- Alembic migrations configured
- 63 achievements seeded (33,625 XP available)
- Connection pooling and health checks
- Comprehensive documentation

### ✅ Step 2: Backend API (100% Complete) - Oct 6-8

**All 23 API endpoints operational:**

**Auth Routes (6 endpoints):**
- POST `/api/auth/register` - Create user + character
- POST `/api/auth/login` - JWT authentication
- POST `/api/auth/logout` - Client-side invalidation
- GET `/api/auth/me` - Current user info
- POST `/api/auth/forgot-password` - Request reset token
- POST `/api/auth/reset-password` - Complete password reset

**User Routes (4 endpoints):**
- GET `/api/users/profile` - Get profile
- PUT `/api/users/profile` - Update profile (display name, bio, avatar)
- DELETE `/api/users/account` - Soft delete (deactivate)
- GET `/api/users/stats` - XP, level, achievements stats

**Character Routes (4 endpoints):**
- GET `/api/characters/list` - All 5 character types with bonuses
- GET `/api/characters/info/{type}` - Single character details
- POST `/api/characters/change` - Change character (Level 5+ only)
- GET `/api/characters/my-character` - Current user's character

**Achievement Routes (3 endpoints):**
- GET `/api/achievements` - List all 63 achievements
- GET `/api/achievements/user` - User's progress (completed + in-progress)
- POST `/api/achievements/unlock` - Unlock + award XP + level check

**Social Routes (4 endpoints):**
- POST `/api/social/friend-request` - Send friend request
- PUT `/api/social/friend-request/{id}/accept` - Accept request
- DELETE `/api/social/friend/{username}` - Remove friend
- GET `/api/social/friends` - Friends list with profiles
- GET `/api/social/friend-requests` - Sent + received requests

**Leaderboard Routes (3 endpoints):**
- GET `/api/leaderboard/overall` - Overall rankings by total XP
- GET `/api/leaderboard/character/{type}` - Character-specific rankings
- GET `/api/leaderboard/my-rank` - User's rank + percentiles

**Technical Implementation:**
- SQLAlchemy models for all 9 tables
- Pydantic schemas for validation
- JWT authentication with bcrypt password hashing
- FastAPI dependencies (get_current_user, get_current_user_profile)
- Proper error handling and logging
- XP awarding logic with level-up calculations

---

## Overview

Phase 1 establishes the foundation of the trading game by implementing the character selection system and user profile management. This phase creates the initial user experience and sets up the progression framework that will carry through all 100 levels.

---

## Objectives

1. ✅ Create engaging character selection interface
2. ✅ Implement user profile system with database persistence
3. ✅ Build XP and level progression mechanics
4. ✅ Design initial onboarding flow
5. ✅ Set up achievement tracking infrastructure

---

## Character Archetypes

### 1. **The Analyst** 📊

**Personality:** Data-driven, methodical, research-focused

**Starting Bonuses:**

- +10% XP from educational content
- Unlock "Research Tools" earlier (Level 5 instead of 10)
- Starting bonus: Free access to "Technical Analysis 101" lesson

**Character Traits:**

- Prefers fundamental and technical analysis
- Lower risk tolerance initially
- Gains bonus XP for completing research tasks

**Visual Design:**

- Professional attire (suit/business casual)
- Glasses, clipboard or tablet
- Color scheme: Blue/Navy (trust, intelligence)

---

### 2. **The Risk Taker** 🚀

**Personality:** Aggressive, high-reward seeking, momentum trader

**Starting Bonuses:**

- +15% potential returns in paper trading (with +15% potential losses)
- Unlock "Options Trading" lesson earlier (Level 15 instead of 20)
- Starting bonus: 2x volatility exposure in mock portfolio

**Character Traits:**

- Attracted to high-growth stocks and crypto
- Higher risk tolerance
- Gains bonus XP for making bold trades

**Visual Design:**

- Casual/streetwear style
- Confident posture
- Color scheme: Red/Orange (energy, risk)

---

### 3. **The Conservative** 🛡️

**Personality:** Safety-first, long-term focused, diversification advocate

**Starting Bonuses:**

- -20% volatility in portfolio (smoother learning curve)
- Unlock "Index Funds & ETFs" lesson earlier (Level 3 instead of 8)
- Starting bonus: Pre-diversified mock portfolio

**Character Traits:**

- Prefers bonds, index funds, dividend stocks
- Lower risk tolerance
- Gains bonus XP for maintaining diversification

**Visual Design:**

- Traditional/classic style
- Calm demeanor
- Color scheme: Green/Forest (stability, growth)

---

### 4. **The Day Trader** ⚡

**Personality:** Fast-paced, technical pattern focused, active trader

**Starting Bonuses:**

- +5% XP from making trades (encourages practice)
- Unlock "Chart Patterns" lesson earlier (Level 6 instead of 12)
- Starting bonus: Advanced charting tools unlocked

**Character Traits:**

- Focuses on short-term price movements
- Medium risk tolerance
- Gains bonus XP for completing trades

**Visual Design:**

- Athletic/active wear
- Multiple monitors in background
- Color scheme: Purple/Violet (creativity, intensity)

---

### 5. **The HODLer** 💎

**Personality:** Patient, conviction-driven, long-term investor

**Starting Bonuses:**

- +10% returns for positions held >30 days (in paper trading)
- Unlock "Warren Buffett Strategy" lesson earlier (Level 7 instead of 15)
- Starting bonus: "Diamond Hands" achievement unlocked

**Character Traits:**

- Buy and hold strategy
- Medium risk tolerance
- Gains bonus XP for holding positions long-term

**Visual Design:**

- Relaxed/comfortable style
- Zen-like calm
- Color scheme: Cyan/Teal (patience, wisdom)

---

## Database Schema

### `users` Table

```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);
```

### `user_profiles` Table

```sql
CREATE TABLE user_profiles (
    profile_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    character_type VARCHAR(50) NOT NULL, -- 'analyst', 'risk_taker', 'conservative', 'day_trader', 'hodler'
    display_name VARCHAR(100),
    avatar_url VARCHAR(500),
    bio TEXT,
    current_level INTEGER DEFAULT 1,
    current_xp INTEGER DEFAULT 0,
    total_xp INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `user_progression` Table

```sql
CREATE TABLE user_progression (
    progression_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    level INTEGER NOT NULL,
    xp_gained INTEGER NOT NULL,
    xp_source VARCHAR(100), -- 'lesson_complete', 'trade_executed', 'achievement_unlocked', etc.
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB -- Additional context about the XP gain
);
```

### `achievements` Table

```sql
CREATE TABLE achievements (
    achievement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    achievement_code VARCHAR(100) UNIQUE NOT NULL, -- 'first_trade', 'paper_millionaire', etc.
    name VARCHAR(200) NOT NULL,
    description TEXT,
    icon_url VARCHAR(500),
    xp_reward INTEGER DEFAULT 0,
    category VARCHAR(50), -- 'education', 'trading', 'social', 'milestones'
    rarity VARCHAR(20) DEFAULT 'common', -- 'common', 'rare', 'epic', 'legendary'
    unlock_criteria JSONB -- Conditions to unlock this achievement
);
```

### `user_achievements` Table

```sql
CREATE TABLE user_achievements (
    user_achievement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    achievement_id UUID REFERENCES achievements(achievement_id),
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    progress INTEGER DEFAULT 0, -- For multi-step achievements
    completed BOOLEAN DEFAULT false,
    UNIQUE(user_id, achievement_id)
);
```

### `character_stats` Table

```sql
CREATE TABLE character_stats (
    stat_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    stat_name VARCHAR(100) NOT NULL, -- 'risk_tolerance', 'research_skill', 'trading_speed', etc.
    stat_value DECIMAL(10, 2) DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `friendships` Table

```sql
CREATE TABLE friendships (
    friendship_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    friend_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'accepted', 'blocked'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, friend_id),
    CHECK (user_id != friend_id)
);
```

### `leaderboard_cache` Table

```sql
CREATE TABLE leaderboard_cache (
    cache_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    username VARCHAR(50),
    display_name VARCHAR(100),
    character_type VARCHAR(50),
    current_level INTEGER,
    total_xp INTEGER,
    total_trades INTEGER DEFAULT 0,
    total_profit DECIMAL(15, 2) DEFAULT 0,
    achievement_count INTEGER DEFAULT 0,
    rank_overall INTEGER,
    rank_by_character INTEGER,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_leaderboard_overall ON leaderboard_cache(total_xp DESC);
CREATE INDEX idx_leaderboard_character ON leaderboard_cache(character_type, total_xp DESC);
CREATE INDEX idx_leaderboard_profit ON leaderboard_cache(total_profit DESC);
```

### `password_reset_tokens` Table

```sql
CREATE TABLE password_reset_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reset_token ON password_reset_tokens(token) WHERE used = false;
```

---

## XP & Leveling System

### XP Requirements Per Level (Levels 1-25)

| Level | XP Required | Cumulative XP | Milestone |
|-------|-------------|---------------|-----------|
| 1     | 0           | 0             | Character Creation |
| 2     | 100         | 100           | |
| 3     | 150         | 250           | |
| 4     | 200         | 450           | |
| 5     | 300         | 750           | First Achievement Unlocked |
| 6     | 400         | 1,150         | |
| 7     | 500         | 1,650         | |
| 8     | 600         | 2,250         | |
| 9     | 700         | 2,950         | |
| 10    | 800         | 3,750         | **Module 1 Complete** |
| 11    | 900         | 4,650         | |
| 12    | 1,000       | 5,650         | |
| 13    | 1,100       | 6,750         | |
| 14    | 1,200       | 7,950         | |
| 15    | 1,300       | 9,250         | Mid-Education Checkpoint |
| 16    | 1,400       | 10,650        | Broker Education Starts |
| 17    | 1,500       | 12,150        | |
| 18    | 1,600       | 13,750        | |
| 19    | 1,700       | 15,450        | |
| 20    | 1,800       | 17,250        | **Broker Education Complete** |
| 21    | 1,900       | 19,150        | |
| 22    | 2,000       | 21,150        | |
| 23    | 2,100       | 23,250        | |
| 24    | 2,200       | 25,450        | |
| 25    | 2,500       | 27,950        | **Education Phase Complete** |

### XP Sources

| Action | Base XP | Notes |
|--------|---------|-------|
| Complete Lesson | 100-500 XP | Based on lesson complexity |
| Pass Quiz (100%) | +50 XP | Bonus for perfect score |
| Pass Quiz (80-99%) | +25 XP | Partial bonus |
| Complete Module | 500 XP | Milestone bonus |
| First Trade (Paper) | 200 XP | One-time bonus |
| Execute Trade | 10-50 XP | Based on trade complexity |
| Profitable Trade | +20 XP | Bonus for gains |
| Hold Position 30+ Days | 100 XP | HODLer bonus |
| Unlock Achievement | 50-1000 XP | Based on achievement rarity |
| Daily Login | 10 XP | Engagement reward |
| 7-Day Streak | 100 XP | Consistency bonus |

### Character-Specific XP Multipliers

- **The Analyst:** 1.1x XP from lessons, 1.0x from trades
- **The Risk Taker:** 1.0x XP from lessons, 1.15x from volatile trades
- **The Conservative:** 1.05x XP from lessons, 1.1x from diversification
- **The Day Trader:** 1.0x XP from lessons, 1.05x from trades
- **The HODLer:** 1.0x XP from lessons, 1.1x from long holds

---

## User Interface Design

### Character Selection Screen

**Layout:**

```bash
┌─────────────────────────────────────────────────────────┐
│                  CHOOSE YOUR PATH                       │
│                                                         │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐        │
│  │  📊  │  │  🚀  │  │  🛡️  │  │  ⚡  │  │  💎  │        │
│  │Analyst│ │Risk  │ │Conser│ │Day   │ │HODLer│        │
│  │      │  │Taker │ │vative│ │Trader│ │      │        │
│  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘        │
│                                                         │
│  Selected: The Analyst                                  │
│                                                         │
│  📊 Data-driven, methodical, research-focused          │
│                                                         │
│  Starting Bonuses:                                      │
│  • +10% XP from educational content                     │
│  • Unlock Research Tools at Level 5                     │
│  • Free: Technical Analysis 101 lesson                  │
│                                                         │
│              [Continue with The Analyst]                │
└─────────────────────────────────────────────────────────┘
```

**Interaction:**

- Hover over character to see details
- Click to select
- Animated character preview
- Tooltip with full stats

### Profile Creation Form

**Fields:**

```bash
Username: __________________ (3-20 characters, unique)
Email: ____________________ (valid email, unique)
Password: _________________ (min 8 chars, 1 number, 1 special)
Confirm: __________________

Display Name: ______________ (optional, can differ from username)
Bio: ______________________ (optional, 280 char max)
          ______________________

Avatar: [Upload] or [Choose from library]

[ ] I agree to Terms of Service
[ ] I want to receive trading tips (optional)

              [Create My Profile]
```

### Dashboard Overview (Post-Creation)

**Top Section:**

```bash
┌─────────────────────────────────────────────────────────┐
│  👤 Luke (The Analyst)                    Level 1        │
│  ████░░░░░░░░░░░░░░░░░░░ 100/100 XP                     │
│                                                          │
│  🏆 Achievements: 1/50    📚 Lessons: 0/100              │
│  💰 Portfolio: $100,000 (Paper)    📈 P&L: $0.00         │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Steps

### Step 1: Database Setup (Day 1)

- [ ] Create PostgreSQL database schema
- [ ] Set up Alembic for migrations
- [ ] Create seed data for achievements
- [ ] Test database connections
- [ ] Set up environment variables for DB credentials

**Files to create:**

- `src/database/schema.sql`
- `src/database/migrations/001_initial_schema.py`
- `src/database/seeds/achievements.sql`
- `src/database/connection.py`

### Step 2: Backend API Endpoints (Days 2-3)

**Authentication & User Management:**

- [ ] POST `/api/auth/register` - Create new user
- [ ] POST `/api/auth/login` - Authenticate user
- [ ] POST `/api/auth/logout` - Logout user
- [ ] GET `/api/user/profile` - Get user profile
- [ ] PUT `/api/user/profile` - Update profile
- [ ] DELETE `/api/user/account` - Delete account

**Character System:**

- [ ] GET `/api/characters` - List all character types
- [ ] POST `/api/user/character` - Select character
- [ ] PUT `/api/user/character` - Change character (Level 5 only)

**XP & Progression:**

- [ ] GET `/api/user/progression` - Get XP and level data
- [ ] POST `/api/user/xp` - Award XP (internal)
- [ ] GET `/api/user/progression/history` - XP history

**Achievements:**

- [ ] GET `/api/achievements` - List all achievements
- [ ] GET `/api/user/achievements` - Get user's achievements
- [ ] POST `/api/user/achievements/unlock` - Unlock achievement (internal)

**Social Features:**

- [ ] GET `/api/leaderboard/overall` - Overall leaderboard
- [ ] GET `/api/leaderboard/character/:type` - Leaderboard by character
- [ ] GET `/api/leaderboard/profit` - Profit leaderboard
- [ ] GET `/api/friends` - Get user's friends list
- [ ] POST `/api/friends/request` - Send friend request
- [ ] PUT `/api/friends/:id/accept` - Accept friend request
- [ ] DELETE `/api/friends/:id` - Remove friend
- [ ] GET `/api/friends/:id/compare` - Compare stats with friend

**Password Reset:**

- [ ] POST `/api/auth/forgot-password` - Request password reset
- [ ] POST `/api/auth/reset-password` - Complete password reset
- [ ] GET `/api/auth/verify-reset-token` - Verify reset token

**Files to create:**

- `src/api/routes/auth.py`
- `src/api/routes/users.py`
- `src/api/routes/characters.py`
- `src/api/routes/achievements.py`
- `src/api/routes/social.py`
- `src/api/routes/leaderboard.py`
- `src/api/routes/password_reset.py`
- `src/api/models/user.py`
- `src/api/models/character.py`
- `src/api/models/achievement.py`
- `src/api/models/friendship.py`
- `src/api/services/auth_service.py`
- `src/api/services/xp_service.py`
- `src/api/services/leaderboard_service.py`
- `src/api/services/friend_service.py`
- `src/api/services/email_service.py`

### Step 3: Character Selection UI (Days 4-5)

- [ ] Create character selection page in Streamlit
- [ ] Design character cards with hover effects
- [ ] Implement character detail view
- [ ] Add character comparison feature
- [ ] Create visual assets for each character
- [ ] Add animations and transitions

**Files to create:**

- `src/dashboard/pages/character_selection.py`
- `src/dashboard/components/character_card.py`
- `src/dashboard/assets/characters/analyst.png`
- `src/dashboard/assets/characters/risk_taker.png`
- (etc. for all characters)

### Step 4: Profile Creation & Management (Days 6-7)

- [ ] Create registration form
- [ ] Implement form validation
- [ ] Add avatar upload functionality
- [ ] Create profile editing page
- [ ] Display character stats on profile
- [ ] Add profile picture library

**Files to create:**

- `src/dashboard/pages/register.py`
- `src/dashboard/pages/profile.py`
- `src/dashboard/components/profile_form.py`
- `src/dashboard/utils/validators.py`
- `src/dashboard/utils/avatar_upload.py`

### Step 5: XP & Progression System (Days 8-9)

- [ ] Implement XP calculation engine
- [ ] Create level-up logic
- [ ] Build XP award system
- [ ] Add progression tracking
- [ ] Create XP history view
- [ ] Implement character-specific XP multipliers

**Files to create:**

- `src/game/xp_engine.py`
- `src/game/level_calculator.py`
- `src/game/progression_tracker.py`
- `src/dashboard/components/xp_bar.py`
- `src/dashboard/components/level_up_modal.py`

### Step 6: Achievement System (Days 10-11)

- [ ] Create achievement unlock logic
- [ ] Implement achievement tracker
- [ ] Build achievement display UI
- [ ] Add achievement notifications
- [ ] Create achievement progress bars
- [ ] Implement rarity system (common → legendary)

**Files to create:**

- `src/game/achievements/achievement_engine.py`
- `src/game/achievements/achievement_tracker.py`
- `src/dashboard/pages/achievements.py`
- `src/dashboard/components/achievement_card.py`
- `src/dashboard/components/achievement_notification.py`

### Step 7: Social Features (Days 10-11)

- [ ] Create leaderboard system (overall, by character, by profit)
- [ ] Build leaderboard cache refresh job
- [ ] Implement friend request system
- [ ] Create friends list page
- [ ] Add friend comparison view
- [ ] Build leaderboard UI with filters
- [ ] Add social notifications

**Files to create:**

- `src/api/routes/social.py`
- `src/api/routes/leaderboard.py`
- `src/api/services/leaderboard_service.py`
- `src/api/services/friend_service.py`
- `src/dashboard/pages/leaderboard.py`
- `src/dashboard/pages/friends.py`
- `src/dashboard/components/leaderboard_table.py`
- `src/dashboard/components/friend_card.py`
- `src/jobs/leaderboard_refresh.py`

### Step 8: Password Reset Flow (Day 11)

- [ ] POST `/api/auth/forgot-password` - Request reset
- [ ] POST `/api/auth/reset-password` - Complete reset
- [ ] Email service integration (SendGrid or similar)
- [ ] Create password reset email template
- [ ] Build reset password UI page
- [ ] Add token expiration logic (24 hours)

**Files to create:**

- `src/api/routes/password_reset.py`
- `src/api/services/email_service.py`
- `src/dashboard/pages/forgot_password.py`
- `src/dashboard/pages/reset_password.py`
- `src/templates/emails/password_reset.html`

### Step 9: Onboarding Flow (Day 12)

- [ ] Create welcome screen
- [ ] Build interactive tutorial
- [ ] Add tooltips and guidance
- [ ] Implement progress indicators
- [ ] Create "Getting Started" checklist
- [ ] Add skip tutorial option

**Files to create:**

- `src/dashboard/pages/welcome.py`
- `src/dashboard/pages/tutorial.py`
- `src/dashboard/components/onboarding_checklist.py`
- `src/dashboard/components/tooltip.py`

### Step 10: Integration & Testing (Days 13-14)

- [ ] Connect frontend to backend APIs
- [ ] Test all user flows
- [ ] Fix bugs and edge cases
- [ ] Performance testing
- [ ] Security audit (password hashing, SQL injection prevention)
- [ ] Cross-browser testing
- [ ] Mobile responsiveness check

**Testing checklist:**

**Authentication & Profile:**

- [ ] User registration works
- [ ] Email validation works
- [ ] Password strength requirements enforced
- [ ] Character selection persists
- [ ] Character change works at Level 5 (and is blocked otherwise)
- [ ] Profile updates save correctly
- [ ] Avatar upload works (10 library avatars available)
- [ ] Login/logout works
- [ ] Session management works
- [ ] Account deletion works

**XP & Progression:**

- [ ] XP awards correctly based on actions
- [ ] Character-specific XP multipliers apply
- [ ] Level-ups trigger properly
- [ ] Level-up rewards granted
- [ ] XP history displays correctly

**Achievements:**

- [ ] Achievements unlock based on criteria
- [ ] Achievement notifications appear
- [ ] Achievement XP bonuses award correctly
- [ ] Rarity system works (common → legendary)

**Social Features:**

- [ ] Overall leaderboard displays top 100 users
- [ ] Character-specific leaderboards work
- [ ] Profit leaderboard ranks correctly
- [ ] Friend requests send and receive
- [ ] Friend requests accept/decline
- [ ] Friends list displays correctly
- [ ] Friend comparison view works
- [ ] Leaderboard cache refreshes hourly

**Password Reset:**

- [ ] Forgot password email sends
- [ ] Reset token validates correctly
- [ ] Expired tokens are rejected
- [ ] Password reset completes successfully
- [ ] Old password becomes invalid after reset
- [ ] Used tokens cannot be reused

**Security & Validation:**

- [ ] SQL injection prevented
- [ ] XSS attacks prevented
- [ ] Password hashing uses bcrypt
- [ ] JWT tokens expire appropriately
- [ ] Data validation prevents bad inputs
- [ ] Unique username/email enforced
- [ ] Unique display name enforced

---

## Visual Design Specifications

### Color Palette (Dark Theme)

- **Background:** #0F172A (Dark navy)
- **Card Background:** #1E293B (Lighter navy)
- **Primary Accent:** #6366F1 (Indigo)
- **Success:** #10B981 (Green)
- **Warning:** #F59E0B (Amber)
- **Error:** #EF4444 (Red)
- **Text Primary:** #F8FAFC (Off-white)
- **Text Secondary:** #94A3B8 (Gray)

### Character Card Design

```css
.character-card {
    background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
    border: 2px solid transparent;
    border-radius: 16px;
    padding: 24px;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
}

.character-card:hover {
    border-color: #6366F1;
    transform: translateY(-8px);
    box-shadow: 0 20px 40px rgba(99, 102, 241, 0.3);
}

.character-card.selected {
    border-color: #10B981;
    background: linear-gradient(135deg, #1E293B 0%, #10B981 100%);
}
```

### XP Bar Design

```css
.xp-bar-container {
    background: rgba(30, 41, 59, 0.8);
    border-radius: 12px;
    padding: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.xp-bar {
    height: 24px;
    background: linear-gradient(90deg, #6366F1 0%, #8B5CF6 100%);
    border-radius: 8px;
    transition: width 0.5s ease;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

.xp-text {
    font-weight: 600;
    color: #F8FAFC;
    font-size: 14px;
}
```

---

## Success Metrics

### Week 1 Goals

- ✅ Database schema implemented and tested
- ✅ Authentication system working
- ✅ Character selection interface complete
- ✅ Profile creation functional
- ✅ Basic XP system operational

### Week 2 Goals

- ✅ Achievement system fully implemented
- ✅ Onboarding flow complete
- ✅ All UI components polished
- ✅ Integration testing passed
- ✅ Ready for Phase 2 (Educational Content)

### Key Performance Indicators (KPIs)

- User registration completion rate > 80%
- Character selection abandonment rate < 10%
- Profile creation time < 3 minutes
- XP system accuracy: 100%
- Achievement unlock reliability: 100%
- Page load time < 2 seconds

---

## Risk Mitigation

### Potential Issues & Solutions

**Issue:** User registration failures due to email validation

- **Solution:** Implement robust email validation + verification flow
- **Fallback:** Allow username-only registration with email optional

**Issue:** XP calculation inconsistencies

- **Solution:** Unit tests for all XP scenarios, centralized XP engine
- **Fallback:** Manual XP adjustment admin tool

**Issue:** Character selection regret

- **Solution:** Allow character re-selection up to Level 5
- **Fallback:** Character "respec" feature (unlockable at Level 25)

**Issue:** Database performance with achievement tracking

- **Solution:** Index frequently queried columns, use Redis caching
- **Fallback:** Lazy-load achievements, paginate results

**Issue:** Avatar upload security risks

- **Solution:** File type validation, size limits, malware scanning
- **Fallback:** Disable uploads, use avatar library only

---

## Dependencies

### Technical Stack

- **Backend:** FastAPI (Python 3.11+)
- **Frontend:** Streamlit 1.28+
- **Database:** PostgreSQL 15+
- **Caching:** Redis (optional, for performance)
- **Authentication:** bcrypt for password hashing, JWT for sessions
- **File Storage:** Local filesystem (Phase 1), S3 (future)
- **Migrations:** Alembic

### External Libraries

```bash
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1
pydantic==2.5.0
bcrypt==4.1.1
python-jose[cryptography]==3.3.0
python-multipart==0.0.6
pillow==10.1.0
streamlit==1.28.0
```

---

## Next Steps After Phase 1

Once Phase 1 is complete, we proceed to:

**Phase 2: Educational Content + Broker Lessons (Weeks 3-5)**

- Create 100 lessons across 4 modules
- Build interactive quizzes
- Implement Advisor Agent integration
- Add broker education module (Lessons 16-20)

---

## Notes & Decisions

### Decision Log

**2025-10-06:** Character archetypes finalized at 5 types

- Considered adding "The Swing Trader" but decided 5 provides enough variety without overwhelming users
- May add more characters in future updates based on user feedback

**2025-10-06:** XP curve designed to be steeper after Level 10

- Early levels (1-10) are quick wins to build engagement
- Later levels require more commitment to slow down progression appropriately

**2025-10-06:** Achievement rarity system added

- Common: 50 XP
- Rare: 150 XP
- Epic: 500 XP
- Legendary: 1000 XP

---

## Questions for Luke - ANSWERED ✅

1. **Character Customization:** Should users be able to customize character appearance (hair, clothes, etc.) or keep it simple with just the 5 archetypes?
   - **DECISION:** Keep it simple for now - just the 5 archetypes. Customization possible in future updates.

2. **Social Features:** Do we want social features in Phase 1 (leaderboards, friends list) or save for later phases?
   - **DECISION:** YES - Social features are a big must! Users like to see others and how they perform. Include leaderboards in Phase 1.

3. **Password Reset:** Do we need email-based password reset in Phase 1, or can this wait until Phase 2?
   - **DECISION:** YES - This is a necessary feature. Implement in Phase 1.

4. **Avatar Library:** How many pre-made avatars should we include? 10? 25? 50?
   - **DECISION:** Start with 10 avatars. Can increase later if needed.

5. **Character Switching:** Should users be locked into their character choice, or allow one-time change at Level 5?
   - **DECISION:** YES - Great idea! Allow one-time character change at Level 5.

6. **Display Names:** Should display names be unique (like usernames) or allow duplicates?
   - **DECISION:** Unique display names (same as usernames).

---

**Last Updated:** October 6, 2025
**Document Owner:** Luke + Claude
**Status:** Ready for Implementation - All Questions Answered
