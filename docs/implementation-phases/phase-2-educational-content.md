# Phase 2: Educational Content + Broker Lessons

**Timeline:** Weeks 3-5 (21 days)
**Status:** 📋 PLANNED - Ready to Start
**Dependencies:** Phase 1 Complete ✅
**Estimated Hours:** 60-80 hours

---

## 📊 Overview

Phase 2 transforms the Trading Game into a comprehensive educational platform by adding:
- 100 interactive lessons across 4 modules
- Quiz system with XP rewards
- Broker-specific education (Bolero)
- Advisor Agent integration
- Progress tracking and certificates

---

## 🎯 Objectives

1. ✅ Create 100 educational lessons covering all trading fundamentals
2. ✅ Build interactive quiz system with instant feedback
3. ✅ Implement Advisor Agent integration for personalized guidance
4. ✅ Add broker education module (Lessons 16-20)
5. ✅ Create progress tracking and lesson completion system
6. ✅ Award XP based on lesson performance

---

## 📚 Content Structure

### Module 1: Trading Fundamentals (Lessons 1-15)
**Estimated Time:** 5-7 hours to complete
**Total XP Available:** 1,750 XP
**Prerequisites:** None

#### Lesson Plan:

**Lesson 1: What is Trading?** (100 XP)
- Definition of trading vs investing
- Different types of markets (stocks, forex, crypto)
- How exchanges work
- Quiz: 10 questions

**Lesson 2: Market Participants** (100 XP)
- Retail traders vs institutional traders
- Market makers and brokers
- Regulators and their role
- Quiz: 10 questions

**Lesson 3: Understanding Stocks** (150 XP)
- What is a stock?
- Stock ownership and dividends
- Common vs preferred stock
- Quiz: 15 questions

**Lesson 4: Market Orders & Limit Orders** (150 XP)
- Order types explained
- When to use market orders
- When to use limit orders
- Stop-loss and stop-limit orders
- Quiz: 15 questions

**Lesson 5: Reading Stock Charts** (200 XP)
- Candlestick basics
- Volume interpretation
- Timeframes (1min, 5min, 1hr, 1day)
- Quiz: 20 questions

**Lessons 6-10: Technical Analysis Basics** (150 XP each)
- Support and resistance
- Trend lines
- Moving averages (SMA, EMA)
- RSI and momentum indicators
- MACD and signal lines

**Lessons 11-15: Fundamental Analysis** (150 XP each)
- Financial statements
- P/E ratio and valuation
- Company analysis
- Sector analysis
- Economic indicators

---

### Module 2: Broker Education - Bolero (Lessons 16-20)
**Estimated Time:** 2-3 hours
**Total XP Available:** 1,000 XP
**Prerequisites:** Lessons 1-15 complete

**Lesson 16: Introduction to Bolero** (200 XP)
- Platform overview
- Account types
- Fee structure
- Security features
- Quiz: 20 questions

**Lesson 17: Placing Your First Order on Bolero** (200 XP)
- Step-by-step order placement
- Order confirmation
- Order tracking
- Canceling orders
- Interactive tutorial with screenshots
- Quiz: 15 questions

**Lesson 18: Bolero Portfolio Management** (200 XP)
- Portfolio view
- Performance tracking
- Dividend management
- Tax documents
- Quiz: 15 questions

**Lesson 19: Advanced Bolero Features** (200 XP)
- Watchlists
- Price alerts
- Market news
- Research tools
- Quiz: 15 questions

**Lesson 20: Bolero Best Practices** (200 XP)
- Cost optimization
- Tax efficiency
- Security best practices
- Common mistakes to avoid
- Quiz: 15 questions

---

### Module 3: Advanced Trading Strategies (Lessons 21-50)
**Estimated Time:** 12-15 hours
**Total XP Available:** 4,500 XP
**Prerequisites:** Lessons 1-20 complete

#### Topics Include:
- Swing trading strategies
- Day trading techniques
- Position sizing
- Risk management (2% rule)
- Portfolio diversification
- Options trading basics
- Technical analysis patterns
- Chart patterns (head & shoulders, triangles, flags)
- Fibonacci retracements
- Volume analysis
- Market psychology
- Trading plan development
- Backtesting strategies
- Paper trading best practices

**Each lesson:** 150 XP + quiz

---

### Module 4: Advanced Topics (Lessons 51-100)
**Estimated Time:** 20-25 hours
**Total XP Available:** 7,500 XP
**Prerequisites:** Lessons 1-50 complete

#### Topics Include:
- Options strategies (covered calls, puts, spreads)
- Futures and commodities
- Forex trading
- Cryptocurrency trading
- Algorithmic trading introduction
- Market analysis tools
- News trading
- Earnings reports
- IPOs and secondary offerings
- Short selling
- Margin trading
- Advanced risk management
- Tax strategies for traders
- Building a trading business
- Professional trader interviews

**Each lesson:** 150 XP + quiz

---

## 🎓 Quiz System

### Quiz Types

**Multiple Choice** (Most common)
- 4 answer options
- 1 correct answer
- Instant feedback
- Explanation provided

**True/False**
- Binary choice
- Instant feedback with explanation

**Fill in the Blank**
- Text input
- Case-insensitive matching
- Partial credit available

**Interactive Scenarios**
- Real-world trading scenarios
- Multiple decision points
- Consequence-based learning

### XP Rewards

| Score | XP Multiplier | Badge |
|-------|---------------|-------|
| 100% | 1.5x | Perfect! 🏆 |
| 90-99% | 1.25x | Excellent! ⭐ |
| 80-89% | 1.0x | Good Job! ✅ |
| 70-79% | 0.75x | Passed 📝 |
| <70% | 0x | Retry Required ❌ |

**Example:** Lesson 5 offers 200 XP
- 100% score: 300 XP (200 * 1.5)
- 90% score: 250 XP (200 * 1.25)
- 80% score: 200 XP (200 * 1.0)
- 70% score: 150 XP (200 * 0.75)
- 60% score: 0 XP (must retry)

### Retake Policy
- Unlimited retakes allowed
- Must wait 1 hour between attempts
- XP only awarded once (highest score counts)
- Progress tracked in user_progression table

---

## 🤖 Advisor Agent Integration

### Agent Capabilities

**Personalized Learning Path**
- Analyzes user's character type
- Recommends relevant lessons
- Adjusts difficulty based on quiz performance
- Suggests prerequisite lessons if struggling

**Real-Time Assistance**
- Chat interface on every lesson page
- Answers questions about lesson content
- Provides additional examples
- Explains complex concepts

**Progress Monitoring**
- Tracks completion rate
- Identifies knowledge gaps
- Sends motivation messages
- Celebrates milestones

**Study Recommendations**
- Optimal study schedule
- Lesson duration estimates
- Review recommendations
- Spaced repetition reminders

### API Integration

```python
# Advisor Agent endpoints to create
POST /api/advisor/chat - Send message to advisor
GET /api/advisor/recommendations - Get personalized lesson recommendations
GET /api/advisor/progress-analysis - Get learning analytics
POST /api/advisor/explain - Request concept explanation
```

---

## 📊 Database Schema Updates

### New Tables

**lessons**
```sql
CREATE TABLE lessons (
    lesson_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lesson_number INTEGER UNIQUE NOT NULL,
    module_number INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    content JSONB NOT NULL,  -- Lesson content in structured format
    estimated_duration INTEGER, -- Minutes
    xp_reward INTEGER DEFAULT 100,
    difficulty VARCHAR(20) DEFAULT 'beginner',
    prerequisites JSONB, -- Array of required lesson_ids
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CHECK (module_number BETWEEN 1 AND 4),
    CHECK (lesson_number BETWEEN 1 AND 100),
    CHECK (difficulty IN ('beginner', 'intermediate', 'advanced'))
);

CREATE INDEX idx_lessons_module ON lessons(module_number);
CREATE INDEX idx_lessons_number ON lessons(lesson_number);
```

**quizzes**
```sql
CREATE TABLE quizzes (
    quiz_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lesson_id UUID REFERENCES lessons(lesson_id) ON DELETE CASCADE,
    questions JSONB NOT NULL, -- Array of question objects
    passing_score INTEGER DEFAULT 70,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**user_lessons**
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

    UNIQUE(user_id, lesson_id),
    CHECK (status IN ('in_progress', 'completed', 'failed'))
);

CREATE INDEX idx_user_lessons_user ON user_lessons(user_id);
CREATE INDEX idx_user_lessons_status ON user_lessons(status);
```

**lesson_bookmarks**
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

## 🎨 UI Components

### Lesson Page
- Lesson content display (markdown + images)
- Progress indicator (% of lesson read)
- Reading time estimate
- Bookmark button
- Next/Previous lesson navigation
- Quiz button (unlocks at 100% progress)
- Chat with Advisor Agent (sidebar)

### Quiz Page
- Question display (1 at a time or all at once)
- Answer selection
- Submit button
- Instant feedback
- Score display
- XP reward notification
- Retry button (if failed)

### Module Overview Page
- Module description
- Lesson cards (15-50 per module)
- Progress bars for each lesson
- Lock/unlock status
- Estimated completion time
- Certificate preview (for completed modules)

### My Learning Page
- Overall progress (X/100 lessons complete)
- Current streak (days of consecutive learning)
- XP earned from lessons
- Quiz performance stats
- Recommended next lessons
- Bookmarked lessons
- Recently completed

---

## 🏆 Achievements for Phase 2

**Educational Milestones:**
- "First Lesson" - Complete any lesson (50 XP)
- "Perfect Score" - Get 100% on any quiz (100 XP)
- "Module 1 Complete" - Finish all 15 lessons (500 XP)
- "Bolero Expert" - Complete Broker Education module (500 XP)
- "Trading Scholar" - Complete 50 lessons (1000 XP)
- "Master Trader" - Complete all 100 lessons (2000 XP)
- "Quiz Master" - Get 100% on 10 quizzes (500 XP)
- "Study Streak" - Learn 7 days in a row (250 XP)
- "Speed Learner" - Complete 5 lessons in one day (300 XP)
- "Bookworm" - Spend 10 hours in lessons (500 XP)

---

## 📅 Implementation Timeline

### Week 3 (Days 15-21)

**Days 15-16: Database & Backend Setup**
- Create lessons, quizzes, user_lessons tables
- Seed first 20 lessons (Modules 1 & 2)
- Build lesson API endpoints
- Build quiz API endpoints

**Days 17-18: Lesson UI**
- Create lesson page component
- Markdown renderer for lesson content
- Progress tracking
- Bookmark functionality

**Days 19-20: Quiz UI**
- Quiz page component
- Answer submission
- Score calculation
- XP reward display

**Day 21: Integration Testing**
- Test complete lesson flow
- Fix bugs
- Performance optimization

### Week 4 (Days 22-28)

**Days 22-24: Content Creation**
- Write lessons 21-50 (Module 3)
- Create quizzes for lessons 21-50
- Add images and diagrams

**Days 25-26: Advisor Agent Integration**
- Chat interface on lesson pages
- Recommendation engine
- Progress analysis

**Days 27-28: Polish & Testing**
- UI improvements
- Bug fixes
- User testing

### Week 5 (Days 29-35)

**Days 29-32: Advanced Content**
- Write lessons 51-100 (Module 4)
- Create quizzes for lessons 51-100
- Advanced topic research

**Days 33-34: Certificates & Badges**
- Certificate generation
- Module completion rewards
- Share achievements feature

**Day 35: Final Testing**
- End-to-end testing
- Performance optimization
- Launch preparation

---

## 🎯 Success Metrics

**Week 3 Goals:**
- ✅ Database schema implemented
- ✅ First 20 lessons seeded
- ✅ Lesson and quiz UI functional
- ✅ Users can complete lessons and earn XP

**Week 4 Goals:**
- ✅ Lessons 21-50 available
- ✅ Advisor Agent integrated
- ✅ Progress tracking working
- ✅ Quiz system stable

**Week 5 Goals:**
- ✅ All 100 lessons available
- ✅ Certificates generated
- ✅ All achievements unlockable
- ✅ Phase 2 complete and tested

---

## 🔗 API Endpoints to Build

### Lessons (6 endpoints)
- GET `/api/lessons` - List all lessons (with filters)
- GET `/api/lessons/{id}` - Get single lesson content
- GET `/api/lessons/{id}/quiz` - Get lesson quiz
- POST `/api/lessons/{id}/start` - Mark lesson as started
- POST `/api/lessons/{id}/complete` - Mark lesson as completed
- POST `/api/lessons/{id}/bookmark` - Bookmark a lesson

### Quizzes (3 endpoints)
- POST `/api/quizzes/{id}/submit` - Submit quiz answers
- GET `/api/quizzes/{id}/results` - Get quiz results
- GET `/api/user/quiz-history` - Get user's quiz history

### Progress (4 endpoints)
- GET `/api/user/learning-progress` - Overall progress stats
- GET `/api/user/lessons/completed` - List completed lessons
- GET `/api/user/lessons/in-progress` - Current lessons
- GET `/api/user/recommendations` - Personalized lesson recommendations

### Advisor Agent (4 endpoints)
- POST `/api/advisor/chat` - Chat with advisor
- GET `/api/advisor/recommendations` - Get study recommendations
- GET `/api/advisor/analysis` - Get progress analysis
- POST `/api/advisor/explain` - Request concept explanation

---

## 💰 XP Economy for Phase 2

**Total XP Available from Lessons:** ~15,000 XP
**Total XP from Achievements:** ~5,750 XP
**Grand Total Phase 2 XP:** ~20,750 XP

This should take most users from **Level 1-10** to **Level 25-30** depending on quiz performance.

---

## 📝 Content Format

### Lesson JSON Structure
```json
{
  "lesson_id": "uuid",
  "lesson_number": 5,
  "title": "Reading Stock Charts",
  "description": "Learn how to interpret candlestick charts and volume",
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
      },
      {
        "type": "interactive",
        "component": "ChartSimulator",
        "props": {"symbol": "AAPL"}
      }
    ]
  },
  "quiz": {
    "questions": [
      {
        "question": "What does a green candlestick indicate?",
        "type": "multiple_choice",
        "options": ["Price went up", "Price went down", "No change", "High volume"],
        "correct_answer": 0,
        "explanation": "A green candlestick means the closing price was higher than the opening price."
      }
    ]
  }
}
```

---

## 🚀 Next Steps After Phase 2

Once Phase 2 is complete, we proceed to:

**Phase 3: Paper Trading** (Weeks 6-8)
- Mock portfolio management
- Real-time market data
- Trade execution simulator
- Performance analytics

---

**Status:** Ready to implement
**Last Updated:** October 8, 2025
**Document Owner:** Luke + Claude
**Estimated Start Date:** Week 3 (After Phase 1 complete)
