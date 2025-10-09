# Database Setup Guide

**Date:** October 9, 2025
**Project:** Trading Dashboard - Phase 2

---

## Quick Check: Do You Already Have the Database?

Run this command to check:

```bash
# Windows CMD
where psql

# Or check if you can connect
psql -U postgres -l
```

If this works and shows a `trading_game` database, **skip to Option B**.

---

## Option A: Fresh PostgreSQL Setup (First Time)

### Step 1: Install PostgreSQL

1. Download PostgreSQL from: https://www.postgresql.org/download/windows/
2. Run installer (PostgreSQL 15+ recommended)
3. During installation:
   - Set password for `postgres` user (remember this!)
   - Port: 5432 (default)
   - Install pgAdmin 4 (GUI tool)

### Step 2: Create Database in pgAdmin

1. Open pgAdmin 4
2. Connect to PostgreSQL server (enter your postgres password)
3. Right-click **"Databases"** → **"Create"** → **"Database..."**
4. Database name: `trading_game`
5. Owner: `postgres`
6. Click **"Save"**

### Step 3: Apply All Migrations

**Phase 1 Schema:**
```sql
-- In pgAdmin Query Tool (trading_game database):
-- Copy/paste contents of: src/database/schema.sql
-- Click Execute (F5)
```

**Phase 1 Achievements:**
```sql
-- Copy/paste contents of: src/database/seeds/achievements.sql
-- Click Execute (F5)
```

**Phase 2 Lesson Tables:**
```sql
-- Copy/paste contents of: src/database/migrations/002_add_lesson_tables.sql
-- Click Execute (F5)
```

**Phase 2 Lessons:**
```sql
-- Copy/paste contents of: src/database/seeds/lessons_module_1.sql
-- Click Execute (F5)
```

### Step 4: Update .env File

```bash
# Create .env file in project root (copy from .env.example)
cp .env.example .env

# Edit .env and set:
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_game
DB_USER=postgres
DB_PASSWORD=YOUR_ACTUAL_PASSWORD_HERE  # ← CHANGE THIS
JWT_SECRET_KEY=YOUR_GENERATED_SECRET_KEY  # Generate one (see below)
```

**Generate JWT Secret:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 5: Verify Setup

```sql
-- In pgAdmin Query Tool, run:
SELECT COUNT(*) as total_tables
FROM information_schema.tables
WHERE table_schema = 'public';
-- Should show: 13 tables (9 from Phase 1 + 4 from Phase 2)

SELECT COUNT(*) FROM achievements;
-- Should show: 63

SELECT COUNT(*) FROM lessons;
-- Should show: 3 (so far)
```

---

## Option B: Add Phase 2 Tables to Existing Database

**If you already have `trading_game` database from Phase 1:**

### Step 1: Open pgAdmin

1. Open pgAdmin 4
2. Navigate to: Servers → PostgreSQL → Databases → **trading_game**
3. Right-click → **Query Tool**

### Step 2: Add Lesson Tables

```sql
-- Copy entire contents of:
-- src/database/migrations/002_add_lesson_tables.sql
-- Paste into Query Tool
-- Click Execute (F5) or press F5
```

**Expected Output:**
```
NOTICE:  ✅ Migration 002 completed successfully!
NOTICE:  Created tables: lessons, quizzes, user_lessons, lesson_bookmarks
NOTICE:  Created functions: get_user_learning_stats, get_recommended_lessons
NOTICE:  Created triggers: update timestamps on lessons and user_lessons
```

### Step 3: Seed Lessons

```sql
-- Copy entire contents of:
-- src/database/seeds/lessons_module_1.sql
-- Paste into Query Tool
-- Click Execute (F5)
```

**Expected Output:**
```
NOTICE:  ✅ Module 1 lessons 1-3 seeded successfully!
NOTICE:  Created 3 lessons with quizzes
NOTICE:  Total XP available: 350 XP
```

### Step 4: Verify

```sql
-- Check tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name LIKE 'lesson%'
ORDER BY table_name;

-- Should show:
-- lesson_bookmarks
-- lessons
-- quizzes (has lesson_id foreign key)
-- user_lessons

-- Check lessons
SELECT lesson_number, title, xp_reward, difficulty
FROM lessons
ORDER BY lesson_number;

-- Should show:
-- 1 | What is Trading? | 100 | beginner
-- 2 | Market Participants | 100 | beginner
-- 3 | Understanding Stocks | 150 | beginner
```

---

## Option C: Command Line (Using psql)

### If you have psql in PATH:

```bash
# Navigate to project directory
cd C:\Users\infob\Desktop\Agents\trading-dashboard

# Add Phase 2 tables
psql -U postgres -d trading_game -f src/database/migrations/002_add_lesson_tables.sql

# Seed lessons
psql -U postgres -d trading_game -f src/database/seeds/lessons_module_1.sql

# Verify
psql -U postgres -d trading_game -c "SELECT COUNT(*) FROM lessons;"
```

---

## Troubleshooting

### Issue: "database trading_game does not exist"
**Solution:** Create it first (see Option A, Step 2)

### Issue: "role postgres does not exist"
**Solution:** Use your actual PostgreSQL username in commands

### Issue: "password authentication failed"
**Solution:**
1. Find `pg_hba.conf` file (usually in PostgreSQL install directory)
2. Change `md5` to `trust` for localhost
3. Restart PostgreSQL service
4. Or use correct password

### Issue: "relation already exists"
**Solution:** Tables already created - this is OK! Skip to seed data step.

### Issue: Can't find pgAdmin
**Solution:**
- Windows: Start Menu → PostgreSQL → pgAdmin 4
- Or access via browser: http://localhost:5432

---

## Database Schema Overview

### Phase 1 Tables (9)
1. `users` - User accounts
2. `user_profiles` - Character and XP
3. `user_progression` - XP history
4. `achievements` - Achievement definitions
5. `user_achievements` - User achievement progress
6. `friendships` - Social connections
7. `leaderboard_cache` - Rankings
8. `password_reset_tokens` - Password recovery
9. `character_stats` - Character attributes

### Phase 2 Tables (4) ← NEW
10. `lessons` - Lesson content (100 lessons planned)
11. `quizzes` - Quiz questions
12. `user_lessons` - User lesson progress
13. `lesson_bookmarks` - Bookmarked lessons

**Total Tables:** 13

---

## Next Steps After Setup

1. ✅ Database tables created
2. ✅ Lessons seeded
3. 🔄 Start Backend API:
   ```bash
   python -m uvicorn src.api.main:app --reload --port 8000
   ```
4. 🔄 Test API endpoints: http://localhost:8000/api/docs
5. 🔄 Build frontend lesson pages

---

## Quick Reference

### Connection Info
- **Host:** localhost
- **Port:** 5432
- **Database:** trading_game
- **User:** postgres
- **Password:** (your password)

### Important Files
- Schema: `src/database/schema.sql` (Phase 1)
- Migration: `src/database/migrations/002_add_lesson_tables.sql` (Phase 2)
- Seeds:
  - `src/database/seeds/achievements.sql` (Phase 1)
  - `src/database/seeds/lessons_module_1.sql` (Phase 2)

### Useful Queries
```sql
-- Check database size
SELECT pg_size_pretty(pg_database_size('trading_game'));

-- List all tables
\dt

-- Count rows in all tables
SELECT
    schemaname,
    tablename,
    n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
```

---

**Status:** Ready for Phase 2 Development
**Last Updated:** October 9, 2025
