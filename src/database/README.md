# Trading Game Database Setup

This directory contains the database schema, migrations, and seed data for the Trading Game Phase 1: Character & Profile System.

## Prerequisites

1. **PostgreSQL 15+** installed and running
2. **Python 3.11+** with virtual environment activated
3. **Required packages** installed (see Installation section)

## Installation

```bash
# Install required packages
pip install alembic psycopg2-binary sqlalchemy python-jose[cryptography] bcrypt pydantic-settings

# Or install from requirements.txt
pip install -r requirements.txt
```

## Database Setup

### Step 1: Create PostgreSQL Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE trading_game;

# Create user (optional)
CREATE USER trading_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE trading_game TO trading_user;

# Exit psql
\q
```

### Step 2: Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and set database credentials
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_game
DB_USER=postgres
DB_PASSWORD=your_password_here
```

### Step 3: Apply Database Schema

Option A - Using raw SQL (direct):

```bash
# Apply schema directly
psql -U postgres -d trading_game -f src/database/schema.sql
```

Option B - Using Alembic migrations (recommended):

```bash
# Navigate to database directory
cd src/database

# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

### Step 4: Seed Achievement Data

```bash
# Load achievement seed data
psql -U postgres -d trading_game -f src/database/seeds/achievements.sql
```

## Database Schema Overview

### Core Tables

#### `users` - User Authentication

- `user_id` (UUID, PK)
- `username` (VARCHAR, UNIQUE)
- `email` (VARCHAR, UNIQUE)
- `password_hash` (VARCHAR)
- Constraints: Username length ≥3, Email format validation

#### `user_profiles` - User Profiles & Characters

- `profile_id` (UUID, PK)
- `user_id` (UUID, FK → users)
- `character_type` (ENUM: analyst, risk_taker, conservative, day_trader, hodler)
- `display_name` (VARCHAR, UNIQUE)
- `current_level` (INTEGER, 1-100)
- `total_xp` (INTEGER)
- `can_change_character` (BOOLEAN)

#### `user_progression` - XP History

- `progression_id` (UUID, PK)
- `user_id` (UUID, FK → users)
- `xp_gained` (INTEGER)
- `xp_source` (ENUM: lesson_complete, trade_executed, etc.)
- `metadata` (JSONB)

#### `achievements` - Achievement Definitions

- `achievement_id` (UUID, PK)
- `achievement_code` (VARCHAR, UNIQUE)
- `category` (ENUM: education, trading, social, milestones, special)
- `rarity` (ENUM: common, rare, epic, legendary)
- `xp_reward` (INTEGER)
- `unlock_criteria` (JSONB)

#### `user_achievements` - User Achievement Progress

- `user_achievement_id` (UUID, PK)
- `user_id` (UUID, FK → users)
- `achievement_id` (UUID, FK → achievements)
- `progress` (INTEGER)
- `completed` (BOOLEAN)

#### `friendships` - Social Connections

- `friendship_id` (UUID, PK)
- `user_id` (UUID, FK → users)
- `friend_id` (UUID, FK → users)
- `status` (ENUM: pending, accepted, blocked)

#### `leaderboard_cache` - Leaderboard Performance

- `cache_id` (UUID, PK)
- `user_id` (UUID, FK → users)
- `total_xp` (INTEGER)
- `rank_overall` (INTEGER)
- `rank_by_character` (INTEGER)
- Indexed on: total_xp, character_type, total_profit

#### `password_reset_tokens` - Password Recovery

- `token_id` (UUID, PK)
- `user_id` (UUID, FK → users)
- `token` (VARCHAR, UNIQUE)
- `expires_at` (TIMESTAMP)
- `used` (BOOLEAN)

#### `character_stats` - Character Attributes

- `stat_id` (UUID, PK)
- `user_id` (UUID, FK → users)
- `stat_name` (ENUM: risk_tolerance, research_skill, etc.)
- `stat_value` (DECIMAL)

## Alembic Migrations

### Create New Migration

```bash
cd src/database
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade <revision_id>

# Downgrade one revision
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision_id>

# View migration history
alembic history

# View current revision
alembic current
```

## Testing Database Connection

```bash
# Test connection using Python
cd src/database
python connection.py
```

Expected output:

```bash
Testing database connection...
Health check: {'status': 'healthy', 'database': 'connected', 'message': 'Database connection successful'}
✅ Database connection successful!
```

## Seed Data Summary

### Achievements (63 total)

**By Rarity:**

- Common: 21 achievements
- Rare: 19 achievements
- Epic: 14 achievements
- Legendary: 16 achievements

**By Category:**

- Education: 15 achievements (lessons, quizzes, modules)
- Trading: 16 achievements (trades, profits, streaks)
- Social: 10 achievements (friends, leaderboards)
- Milestones: 10 achievements (levels, XP totals)
- Special: 12 achievements (login streaks, events)

**Total XP Available:** 33,625 XP from all achievements

## Common Operations

### Reset Database (CAUTION)

```bash
# Drop all tables
psql -U postgres -d trading_game -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Re-apply schema
psql -U postgres -d trading_game -f src/database/schema.sql

# Re-seed achievements
psql -U postgres -d trading_game -f src/database/seeds/achievements.sql
```

### View Achievement Statistics

```sql
-- Count achievements by rarity
SELECT rarity, COUNT(*) as count
FROM achievements
GROUP BY rarity
ORDER BY
  CASE rarity
    WHEN 'common' THEN 1
    WHEN 'rare' THEN 2
    WHEN 'epic' THEN 3
    WHEN 'legendary' THEN 4
  END;

-- Total XP available
SELECT SUM(xp_reward) as total_xp FROM achievements;

-- Achievements by category
SELECT category, COUNT(*) as count, SUM(xp_reward) as total_xp
FROM achievements
GROUP BY category
ORDER BY count DESC;
```

### View User Statistics

```sql
-- Top 10 users by XP
SELECT
  u.username,
  p.display_name,
  p.character_type,
  p.current_level,
  p.total_xp
FROM user_profiles p
JOIN users u ON p.user_id = u.user_id
ORDER BY p.total_xp DESC
LIMIT 10;

-- User achievement completion rate
SELECT
  u.username,
  COUNT(ua.user_achievement_id) as unlocked_achievements,
  COUNT(ua.user_achievement_id) * 100.0 / (SELECT COUNT(*) FROM achievements) as completion_rate
FROM users u
LEFT JOIN user_achievements ua ON u.user_id = ua.user_id AND ua.completed = true
GROUP BY u.user_id, u.username
ORDER BY completion_rate DESC;
```

## Triggers & Automated Functions

### Auto-Update Triggers

- `update_user_profiles_updated_at` - Updates `updated_at` on profile changes
- `update_friendships_updated_at` - Updates `updated_at` on friendship status changes
- `update_leaderboard_on_profile_change` - Refreshes leaderboard cache when user profile changes

### Manual Leaderboard Refresh

```sql
-- Refresh all leaderboard rankings
UPDATE leaderboard_cache lc
SET
  rank_overall = subquery.rank_overall,
  rank_by_character = subquery.rank_by_character,
  last_updated = CURRENT_TIMESTAMP
FROM (
  SELECT
    user_id,
    ROW_NUMBER() OVER (ORDER BY total_xp DESC) as rank_overall,
    ROW_NUMBER() OVER (PARTITION BY character_type ORDER BY total_xp DESC) as rank_by_character
  FROM leaderboard_cache
) subquery
WHERE lc.user_id = subquery.user_id;
```

## Backup & Restore

### Backup Database

```bash
# Full database backup
pg_dump -U postgres -d trading_game -F c -b -v -f trading_game_backup.dump

# Schema only
pg_dump -U postgres -d trading_game --schema-only -f trading_game_schema.sql

# Data only
pg_dump -U postgres -d trading_game --data-only -f trading_game_data.sql
```

### Restore Database

```bash
# Restore from custom format
pg_restore -U postgres -d trading_game -v trading_game_backup.dump

# Restore from SQL file
psql -U postgres -d trading_game -f trading_game_backup.sql
```

## Troubleshooting

### Connection Issues

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS
# Check Services app on Windows

# Test connection
psql -U postgres -d trading_game -c "SELECT 1;"
```

### Permission Issues

```sql
-- Grant all privileges to user
GRANT ALL PRIVILEGES ON DATABASE trading_game TO trading_user;
GRANT ALL ON ALL TABLES IN SCHEMA public TO trading_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO trading_user;
```

### Alembic Issues

```bash
# Reset alembic
rm -rf src/database/migrations/versions/*
alembic revision --autogenerate -m "Fresh start"
alembic upgrade head
```

## Database Performance

### Indexes

All critical columns are indexed:

- `users(email, username, is_active)`
- `user_profiles(user_id, character_type, total_xp, current_level)`
- `leaderboard_cache(total_xp, character_type, total_profit)`
- `user_achievements(user_id, completed)`
- `friendships(user_id, friend_id, status)`

### Query Optimization

```sql
-- Explain query plan
EXPLAIN ANALYZE
SELECT * FROM leaderboard_cache
ORDER BY total_xp DESC
LIMIT 100;

-- Index usage statistics
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan as index_scans
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

## Next Steps

After database setup is complete:

1. **Step 2: Backend API Endpoints** - Build FastAPI routes
2. **Step 3: Character Selection UI** - Create Streamlit pages
3. **Step 4: Profile Management** - Build user registration/login
4. **Step 5: XP & Progression** - Implement XP tracking
5. **Step 6: Achievement System** - Build unlock logic
6. **Step 7: Social Features** - Add leaderboards and friends
7. **Step 8: Password Reset** - Email integration
8. **Step 9: Onboarding** - Welcome flow
9. **Step 10: Testing** - Integration tests

## Support

For issues or questions:

- Check logs: `logs/trading_game.log`
- Database logs: Check PostgreSQL logs
- Review Phase 1 documentation: `docs/implementation-phases/phase-1-character-profile-system.md`

---

**Last Updated:** October 6, 2025
**Database Version:** 1.0.0
**Schema Version:** Phase 1 - Character & Profile System
