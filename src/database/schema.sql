-- Trading Game Database Schema
-- Phase 1: Character & Profile System
-- Created: October 6, 2025

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- USERS & AUTHENTICATION
-- ============================================================================

-- Core user table for authentication
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true,

    CONSTRAINT username_length CHECK (char_length(username) >= 3),
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = true;

-- Password reset tokens
CREATE TABLE password_reset_tokens (
    token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT token_not_expired CHECK (expires_at > created_at)
);

CREATE INDEX idx_reset_token ON password_reset_tokens(token) WHERE used = false;
CREATE INDEX idx_reset_token_expiry ON password_reset_tokens(expires_at) WHERE used = false;

-- ============================================================================
-- USER PROFILES & CHARACTERS
-- ============================================================================

-- User profile with character selection
CREATE TABLE user_profiles (
    profile_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    character_type VARCHAR(50) NOT NULL,
    display_name VARCHAR(100) UNIQUE NOT NULL,
    avatar_url VARCHAR(500),
    bio TEXT,
    current_level INTEGER DEFAULT 1,
    current_xp INTEGER DEFAULT 0,
    total_xp INTEGER DEFAULT 0,
    character_changed_at TIMESTAMP, -- Track when character was last changed
    can_change_character BOOLEAN DEFAULT true, -- Can change at Level 5
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_character_type CHECK (
        character_type IN ('analyst', 'risk_taker', 'conservative', 'day_trader', 'hodler')
    ),
    CONSTRAINT valid_level CHECK (current_level >= 1 AND current_level <= 100),
    CONSTRAINT valid_xp CHECK (current_xp >= 0 AND total_xp >= 0),
    CONSTRAINT display_name_length CHECK (char_length(display_name) >= 3)
);

CREATE INDEX idx_profiles_user ON user_profiles(user_id);
CREATE INDEX idx_profiles_character ON user_profiles(character_type);
CREATE INDEX idx_profiles_level ON user_profiles(current_level DESC);
CREATE INDEX idx_profiles_xp ON user_profiles(total_xp DESC);

-- Character stats tracking
CREATE TABLE character_stats (
    stat_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    stat_name VARCHAR(100) NOT NULL,
    stat_value DECIMAL(10, 2) DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, stat_name),
    CONSTRAINT valid_stat_name CHECK (
        stat_name IN (
            'risk_tolerance', 'research_skill', 'trading_speed',
            'patience_level', 'analytical_skill', 'emotional_control'
        )
    )
);

CREATE INDEX idx_character_stats_user ON character_stats(user_id);

-- ============================================================================
-- XP & PROGRESSION
-- ============================================================================

-- Track all XP gains for history and analytics
CREATE TABLE user_progression (
    progression_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    level INTEGER NOT NULL,
    xp_gained INTEGER NOT NULL,
    xp_source VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,

    CONSTRAINT valid_xp_gained CHECK (xp_gained > 0),
    CONSTRAINT valid_xp_source CHECK (
        xp_source IN (
            'lesson_complete', 'quiz_pass', 'module_complete',
            'first_trade', 'trade_executed', 'profitable_trade',
            'hold_position_30d', 'achievement_unlocked',
            'daily_login', 'login_streak_7d', 'manual_adjustment'
        )
    )
);

CREATE INDEX idx_progression_user ON user_progression(user_id);
CREATE INDEX idx_progression_timestamp ON user_progression(timestamp DESC);
CREATE INDEX idx_progression_source ON user_progression(xp_source);

-- ============================================================================
-- ACHIEVEMENTS
-- ============================================================================

-- Master achievement definitions
CREATE TABLE achievements (
    achievement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    achievement_code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    icon_url VARCHAR(500),
    xp_reward INTEGER DEFAULT 0,
    category VARCHAR(50) NOT NULL,
    rarity VARCHAR(20) DEFAULT 'common',
    unlock_criteria JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_category CHECK (
        category IN ('education', 'trading', 'social', 'milestones', 'special')
    ),
    CONSTRAINT valid_rarity CHECK (
        rarity IN ('common', 'rare', 'epic', 'legendary')
    ),
    CONSTRAINT valid_xp_reward CHECK (xp_reward >= 0)
);

CREATE INDEX idx_achievements_category ON achievements(category);
CREATE INDEX idx_achievements_rarity ON achievements(rarity);

-- User achievement progress and unlocks
CREATE TABLE user_achievements (
    user_achievement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    achievement_id UUID REFERENCES achievements(achievement_id) ON DELETE CASCADE,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    progress INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT false,

    UNIQUE(user_id, achievement_id),
    CONSTRAINT valid_progress CHECK (progress >= 0)
);

CREATE INDEX idx_user_achievements_user ON user_achievements(user_id);
CREATE INDEX idx_user_achievements_completed ON user_achievements(completed);

-- ============================================================================
-- SOCIAL FEATURES
-- ============================================================================

-- Friend connections
CREATE TABLE friendships (
    friendship_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    friend_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, friend_id),
    CONSTRAINT no_self_friend CHECK (user_id != friend_id),
    CONSTRAINT valid_friendship_status CHECK (
        status IN ('pending', 'accepted', 'blocked')
    )
);

CREATE INDEX idx_friendships_user ON friendships(user_id);
CREATE INDEX idx_friendships_friend ON friendships(friend_id);
CREATE INDEX idx_friendships_status ON friendships(status);

-- Leaderboard cache for performance
CREATE TABLE leaderboard_cache (
    cache_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    username VARCHAR(50) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    character_type VARCHAR(50) NOT NULL,
    current_level INTEGER NOT NULL,
    total_xp INTEGER NOT NULL,
    total_trades INTEGER DEFAULT 0,
    total_profit DECIMAL(15, 2) DEFAULT 0,
    achievement_count INTEGER DEFAULT 0,
    rank_overall INTEGER,
    rank_by_character INTEGER,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_ranks CHECK (
        rank_overall > 0 AND rank_by_character > 0
    )
);

CREATE INDEX idx_leaderboard_overall ON leaderboard_cache(total_xp DESC);
CREATE INDEX idx_leaderboard_character ON leaderboard_cache(character_type, total_xp DESC);
CREATE INDEX idx_leaderboard_profit ON leaderboard_cache(total_profit DESC);
CREATE INDEX idx_leaderboard_level ON leaderboard_cache(current_level DESC);

-- ============================================================================
-- TRIGGERS & FUNCTIONS
-- ============================================================================

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to relevant tables
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_friendships_updated_at
    BEFORE UPDATE ON friendships
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Update leaderboard cache when profile changes
CREATE OR REPLACE FUNCTION refresh_leaderboard_for_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO leaderboard_cache (
        user_id, username, display_name, character_type,
        current_level, total_xp, achievement_count
    )
    SELECT
        NEW.user_id,
        u.username,
        NEW.display_name,
        NEW.character_type,
        NEW.current_level,
        NEW.total_xp,
        (SELECT COUNT(*) FROM user_achievements WHERE user_id = NEW.user_id AND completed = true)
    FROM users u
    WHERE u.user_id = NEW.user_id
    ON CONFLICT (user_id) DO UPDATE SET
        display_name = EXCLUDED.display_name,
        character_type = EXCLUDED.character_type,
        current_level = EXCLUDED.current_level,
        total_xp = EXCLUDED.total_xp,
        achievement_count = EXCLUDED.achievement_count,
        last_updated = CURRENT_TIMESTAMP;

    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_leaderboard_on_profile_change
    AFTER INSERT OR UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION refresh_leaderboard_for_user();

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE users IS 'Core user authentication and account management';
COMMENT ON TABLE user_profiles IS 'User profile data including character selection and progression';
COMMENT ON TABLE user_progression IS 'Historical record of all XP gains for analytics';
COMMENT ON TABLE achievements IS 'Master list of all available achievements';
COMMENT ON TABLE user_achievements IS 'User progress and unlocks for achievements';
COMMENT ON TABLE friendships IS 'Social connections between users';
COMMENT ON TABLE leaderboard_cache IS 'Pre-calculated leaderboard rankings for performance';
COMMENT ON TABLE password_reset_tokens IS 'Tokens for secure password reset flow';
COMMENT ON TABLE character_stats IS 'Individual character attribute tracking';

-- ============================================================================
-- INITIAL DATA SETUP (will be moved to seeds)
-- ============================================================================

-- Character type reference (informational)
COMMENT ON COLUMN user_profiles.character_type IS
'Valid types: analyst (data-driven), risk_taker (aggressive), conservative (safety-first), day_trader (fast-paced), hodler (patient long-term)';

-- Achievement categories reference
COMMENT ON COLUMN achievements.category IS
'Categories: education (learning milestones), trading (trade execution), social (friend/leaderboard), milestones (level/XP), special (limited events)';

-- XP source reference
COMMENT ON COLUMN user_progression.xp_source IS
'Sources: lesson_complete, quiz_pass, module_complete, first_trade, trade_executed, profitable_trade, hold_position_30d, achievement_unlocked, daily_login, login_streak_7d, manual_adjustment';
