# Session Startup Guide - Phase 2: Educational Content

**Start Date:** October 9, 2025
**Phase:** 2 of 8
**Timeline:** 21 days (Weeks 3-5)
**Status:** Ready to Begin 🚀

---

## 🎉 Phase 1 Recap

**Phase 1 is 100% COMPLETE!** ✅

All 10 steps finished:

- ✅ Database with 9 tables and 63 achievements
- ✅ Backend API with 23 endpoints
- ✅ Frontend with 10 complete pages
- ✅ Character system with 5 archetypes
- ✅ XP and progression system
- ✅ Achievement tracking
- ✅ Social features (friends, leaderboard)
- ✅ Authentication and security

See: [PHASE-1-COMPLETE.md](PHASE-1-COMPLETE.md) for full details.

---

## 📋 Phase 2 Overview

**Objective:** Build a comprehensive educational platform with 100 lessons

### What We're Building

1. **100 Interactive Lessons** across 4 modules
2. **Quiz System** with instant feedback and XP rewards
3. **Advisor Agent Integration** for personalized guidance
4. **Broker Education Module** (Bolero-specific lessons)
5. **Progress Tracking** and completion certificates

### Expected Outcomes

- Users can learn trading from beginner to advanced
- XP rewards drive engagement and progression
- Quizzes validate knowledge (70% passing score)
- Advisor Agent provides personalized help
- Users advance from Level 1-10 to Level 25-30

---

## 🎯 Phase 2 Modules Breakdown

### Module 1: Trading Fundamentals (Lessons 1-15)

**Estimated Time:** 5-7 hours to complete
**Total XP Available:** 1,750 XP
**Topics:**

- What is trading vs investing
- Market participants
- Understanding stocks
- Order types (market, limit, stop-loss)
- Reading stock charts
- Technical analysis basics (5 lessons)
- Fundamental analysis (5 lessons)

### Module 2: Broker Education - Bolero (Lessons 16-20)

**Estimated Time:** 2-3 hours
**Total XP Available:** 1,000 XP
**Topics:**

- Introduction to Bolero platform
- Placing your first order
- Portfolio management on Bolero
- Advanced Bolero features
- Bolero best practices

### Module 3: Advanced Trading Strategies (Lessons 21-50)

**Estimated Time:** 12-15 hours
**Total XP Available:** 4,500 XP
**Topics:**

- Swing trading, day trading techniques
- Position sizing and risk management
- Portfolio diversification
- Options trading basics
- Technical patterns (head & shoulders, triangles, flags)
- Fibonacci retracements, volume analysis
- Market psychology, trading plan development

### Module 4: Advanced Topics (Lessons 51-100)

**Estimated Time:** 20-25 hours
**Total XP Available:** 7,500 XP
**Topics:**

- Options strategies (covered calls, puts, spreads)
- Futures, commodities, forex, cryptocurrency
- Algorithmic trading introduction
- News trading, earnings reports, IPOs
- Short selling, margin trading
- Tax strategies, building a trading business

**Total XP from Lessons:** ~15,000 XP
**Total XP from Achievements:** ~5,750 XP
**Grand Total:** ~20,750 XP

---

## 📊 Database Schema Updates

### New Tables to Create

**1. lessons table**

```sql
CREATE TABLE lessons (
    lesson_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lesson_number INTEGER UNIQUE NOT NULL,
    module_number INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    content JSONB NOT NULL,
    estimated_duration INTEGER, -- Minutes
    xp_reward INTEGER DEFAULT 100,
    difficulty VARCHAR(20) DEFAULT 'beginner',
    prerequisites JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**2. quizzes table**

```sql
CREATE TABLE quizzes (
    quiz_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lesson_id UUID REFERENCES lessons(lesson_id) ON DELETE CASCADE,
    questions JSONB NOT NULL,
    passing_score INTEGER DEFAULT 70,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**3. user_lessons table**

```sql
CREATE TABLE user_lessons (
    user_lesson_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    lesson_id UUID REFERENCES lessons(lesson_id) ON DELETE CASCADE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    quiz_score INTEGER,
    quiz_attempts INTEGER DEFAULT 0,
    time_spent INTEGER, -- Seconds
    status VARCHAR(20) DEFAULT 'in_progress',
    UNIQUE(user_id, lesson_id)
);
```

**4. lesson_bookmarks table**

```sql
CREATE TABLE lesson_bookmarks (
    bookmark_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    lesson_id UUID REFERENCES lessons(lesson_id) ON DELETE CASCADE,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, lesson_id)
);
```

---

## 🛠️ Implementation Plan

### Week 3 (Days 15-21) - Foundation

**Days 15-16: Database & Backend**

- [ ] Create 4 new database tables (lessons, quizzes, user_lessons, lesson_bookmarks)
- [ ] Write migration script
- [ ] Seed first 20 lessons (Modules 1 & 2) with content
- [ ] Create lesson API endpoints (6 endpoints)
- [ ] Create quiz API endpoints (3 endpoints)
- [ ] Create progress API endpoints (4 endpoints)

**Days 17-18: Lesson UI**

- [ ] Create lesson page component
- [ ] Markdown renderer for lesson content
- [ ] Progress tracking (% read)
- [ ] Bookmark functionality
- [ ] Next/Previous navigation

**Days 19-20: Quiz UI**

- [ ] Quiz page component
- [ ] Multiple choice, true/false, fill-in-blank question types
- [ ] Answer submission
- [ ] Instant feedback with explanations
- [ ] Score calculation and XP rewards
- [ ] Retry functionality

**Day 21: Testing**

- [ ] Test complete lesson flow
- [ ] Test quiz submission and scoring
- [ ] Fix bugs
- [ ] Performance optimization

### Week 4 (Days 22-28) - Content Creation

**Days 22-24: Module 3 Content**

- [ ] Write lessons 21-50 (30 lessons)
- [ ] Create quizzes for each lesson
- [ ] Add images and diagrams
- [ ] Review and edit content

**Days 25-26: Advisor Agent Integration**

- [ ] Chat interface on lesson pages
- [ ] Recommendation engine (suggest next lessons)
- [ ] Progress analysis endpoint
- [ ] Concept explanation feature

**Days 27-28: Polish & Testing**

- [ ] UI improvements
- [ ] Bug fixes
- [ ] User testing
- [ ] Performance optimization

### Week 5 (Days 29-35) - Advanced Content & Launch

**Days 29-32: Module 4 Content**

- [ ] Write lessons 51-100 (50 lessons)
- [ ] Create quizzes for advanced lessons
- [ ] Research advanced topics
- [ ] Review and edit content

**Days 33-34: Certificates & Achievements**

- [ ] Certificate generation (PDF or image)
- [ ] Module completion rewards
- [ ] Share achievements feature
- [ ] Add 10 new lesson-related achievements

**Day 35: Final Testing & Launch**

- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Documentation
- [ ] Launch Phase 2!

---

## 🔌 API Endpoints to Build

### Lessons Endpoints (6)

- `GET /api/lessons` - List all lessons with filters (module, difficulty)
- `GET /api/lessons/{id}` - Get single lesson content
- `GET /api/lessons/{id}/quiz` - Get lesson quiz questions
- `POST /api/lessons/{id}/start` - Mark lesson as started
- `POST /api/lessons/{id}/complete` - Mark lesson as completed
- `POST /api/lessons/{id}/bookmark` - Bookmark/unbookmark lesson

### Quiz Endpoints (3)

- `POST /api/quizzes/{id}/submit` - Submit quiz answers
- `GET /api/quizzes/{id}/results` - Get quiz results
- `GET /api/user/quiz-history` - Get user's quiz history

### Progress Endpoints (4)

- `GET /api/user/learning-progress` - Overall progress stats
- `GET /api/user/lessons/completed` - List completed lessons
- `GET /api/user/lessons/in-progress` - Current lessons
- `GET /api/user/recommendations` - Personalized recommendations

### Advisor Agent Endpoints (4)

- `POST /api/advisor/chat` - Chat with advisor
- `GET /api/advisor/recommendations` - Get study recommendations
- `GET /api/advisor/analysis` - Get progress analysis
- `POST /api/advisor/explain` - Request concept explanation

**Total New Endpoints:** 17

---

## 🎨 UI Pages to Build

### Lesson Pages

1. **Lesson Library** - Browse all 100 lessons by module
2. **Lesson Detail** - Read lesson content with progress tracking
3. **Quiz Page** - Take quiz and get instant feedback
4. **My Learning** - Dashboard showing progress, streaks, bookmarks

### Components

- Lesson card (with lock/unlock status)
- Progress bar (% of module complete)
- Quiz question component (multiple choice, true/false, fill-in)
- XP reward animation
- Certificate display
- Chat with Advisor (sidebar)

---

## 📝 Lesson Content Format

### Lesson JSON Structure

```json
{
  "lesson_id": "uuid",
  "lesson_number": 5,
  "module_number": 1,
  "title": "Reading Stock Charts",
  "description": "Learn candlestick charts and volume",
  "estimated_duration": 15,
  "xp_reward": 200,
  "difficulty": "beginner",
  "content": {
    "sections": [
      {
        "type": "text",
        "content": "# Introduction to Candlestick Charts..."
      },
      {
        "type": "image",
        "url": "/lessons/images/candlestick-basics.png",
        "caption": "Basic candlestick patterns"
      },
      {
        "type": "video",
        "url": "https://youtube.com/watch?v=example"
      }
    ]
  },
  "quiz": {
    "questions": [
      {
        "question": "What does a green candlestick indicate?",
        "type": "multiple_choice",
        "options": ["Price went up", "Price went down", "No change"],
        "correct_answer": 0,
        "explanation": "Green means closing > opening price."
      }
    ]
  }
}
```

---

## 🏆 New Achievements for Phase 2

Add to achievements table:

- "First Lesson" - Complete any lesson (50 XP)
- "Perfect Score" - Get 100% on any quiz (100 XP)
- "Module 1 Complete" - Finish all 15 lessons (500 XP)
- "Bolero Expert" - Complete Broker Education (500 XP)
- "Trading Scholar" - Complete 50 lessons (1,000 XP)
- "Master Trader" - Complete all 100 lessons (2,000 XP)
- "Quiz Master" - Get 100% on 10 quizzes (500 XP)
- "Study Streak" - Learn 7 days in a row (250 XP)
- "Speed Learner" - Complete 5 lessons in one day (300 XP)
- "Bookworm" - Spend 10 hours in lessons (500 XP)

**Total New XP from Achievements:** ~5,750 XP

---

## 🎯 Success Criteria

### Week 3 Goals

- ✅ 4 new database tables created
- ✅ First 20 lessons seeded
- ✅ Lesson and quiz UI functional
- ✅ Users can complete lessons and earn XP

### Week 4 Goals

- ✅ Lessons 21-50 available
- ✅ Advisor Agent integrated
- ✅ Progress tracking working
- ✅ Quiz system stable

### Week 5 Goals

- ✅ All 100 lessons available
- ✅ Certificates generated
- ✅ All achievements unlockable
- ✅ Phase 2 complete and tested

---

## 🚀 Getting Started (Today)

### Step 1: Database Schema

```bash
# Create new schema file for Phase 2 tables
# File: src/database/migrations/002_add_lesson_tables.sql
```

### Step 2: Seed First Lessons

```bash
# Create seed file with first 20 lessons
# File: src/database/seeds/lessons_module_1_2.sql
```

### Step 3: API Routes

```bash
# Create lesson routes
# File: src/api/routes/lessons.py
```

### Step 4: UI Pages

```bash
# Create lesson library page
# File: src/dashboard/pages/lesson_library.py
```

---

## 📂 Files to Create

### Database

- `src/database/migrations/002_add_lesson_tables.sql`
- `src/database/seeds/lessons_module_1_2.sql`
- `src/database/seeds/lessons_module_3.sql`
- `src/database/seeds/lessons_module_4.sql`

### Backend API

- `src/api/routes/lessons.py` (6 endpoints)
- `src/api/routes/quizzes.py` (3 endpoints)
- `src/api/routes/progress.py` (4 endpoints)
- `src/api/routes/advisor.py` (4 endpoints)
- `src/api/models/lesson.py`
- `src/api/schemas/lesson.py`
- `src/api/services/lesson_service.py`
- `src/api/services/quiz_service.py`

### Frontend UI

- `src/dashboard/pages/lesson_library.py`
- `src/dashboard/pages/lesson_detail.py`
- `src/dashboard/pages/quiz.py`
- `src/dashboard/pages/my_learning.py`
- `src/dashboard/components/lesson_card.py`
- `src/dashboard/components/quiz_question.py`
- `src/dashboard/components/advisor_chat.py`
- `src/dashboard/components/certificate.py`

### Content

- `content/lessons/module_1/` (15 lessons)
- `content/lessons/module_2/` (5 lessons)
- `content/lessons/module_3/` (30 lessons)
- `content/lessons/module_4/` (50 lessons)

---

## 💡 Recommended Approach

### Option A: Database-First (Recommended)

1. Create database tables (Day 1)
2. Seed first 20 lessons (Day 1)
3. Build API endpoints (Day 2)
4. Build UI pages (Day 3-4)
5. Test end-to-end (Day 5)

### Option B: Content-First

1. Write lesson content (Day 1-2)
2. Create database and seed (Day 3)
3. Build API and UI together (Day 4-5)

**I recommend Option A** - Database-first approach allows for parallel development and testing.

---

## 🔧 Technical Setup

### Start Backend API

```bash
cd c:\Users\infob\Desktop\Agents\trading-dashboard
.\venv\Scripts\activate
python -m uvicorn src.api.main:app --reload --port 8000
```

### Start Frontend

```bash
python -m streamlit run src/dashboard/game_app.py --server.port=8501
```

### Database Migrations

```bash
# Apply new migration
psql -U postgres -d trading_game -f src/database/migrations/002_add_lesson_tables.sql

# Seed lessons
psql -U postgres -d trading_game -f src/database/seeds/lessons_module_1_2.sql
```

---

## 📊 Progress Tracking

We'll track Phase 2 progress using:

- Daily commit messages
- Updated SESSION-STARTUP documents
- Progress percentage in phase-2 doc

### Daily Goals

- **Day 15:** Database schema + seed 5 lessons
- **Day 16:** Complete seeding 20 lessons + API routes
- **Day 17:** Lesson library UI + lesson detail page
- **Day 18:** Quiz UI + scoring
- **Day 19:** Progress tracking + bookmarks
- **Day 20:** Testing + bug fixes
- **Day 21:** Review week 3 progress

---

## 🎯 First Day Tasks (Day 15)

### Priority 1: Database Schema

- [ ] Create `002_add_lesson_tables.sql` migration
- [ ] Define lessons, quizzes, user_lessons, lesson_bookmarks tables
- [ ] Apply migration to database
- [ ] Verify tables created

### Priority 2: Seed First Lessons

- [ ] Write Lesson 1: "What is Trading?" with quiz
- [ ] Write Lesson 2: "Market Participants" with quiz
- [ ] Write Lesson 3: "Understanding Stocks" with quiz
- [ ] Write Lesson 4: "Market Orders & Limit Orders" with quiz
- [ ] Write Lesson 5: "Reading Stock Charts" with quiz
- [ ] Insert into database
- [ ] Verify lessons load

### Priority 3: API Endpoints (Start)

- [ ] Create `src/api/routes/lessons.py`
- [ ] Implement `GET /api/lessons` - List all lessons
- [ ] Implement `GET /api/lessons/{id}` - Get lesson detail
- [ ] Test endpoints in /api/docs

---

## 📚 Reference Documents

- **Phase 2 Full Plan:** [phase-2-educational-content.md](phase-2-educational-content.md)
- **Phase 1 Complete:** [PHASE-1-COMPLETE.md](PHASE-1-COMPLETE.md)
- **Database Schema:** `src/database/schema.sql`
- **API Docs:** <http://localhost:8000/api/docs>

---

**Ready to Start Phase 2?** Let's build 100 lessons! 🚀

**Current Status:** Phase 1 ✅ Complete | Phase 2 🎯 Ready to Begin
**Next Action:** Create database schema for lessons
**Estimated Time:** 21 days (Oct 9 - Oct 29, 2025)

---

**Last Updated:** October 9, 2025
**Document Owner:** Luke + Claude
**Phase:** 2 of 8
**Status:** Ready to Start 🚀
