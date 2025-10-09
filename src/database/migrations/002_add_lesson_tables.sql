-- Migration 002: Add Lesson System Tables
-- Phase 2: Educational Content
-- Created: October 9, 2025

-- ============================================
-- TABLE: lessons
-- Stores all educational lesson content
-- ============================================

CREATE TABLE IF NOT EXISTS lessons (
    lesson_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lesson_number INTEGER UNIQUE NOT NULL,
    module_number INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    content JSONB NOT NULL,  -- Lesson content in structured format (sections with text, images, videos)
    estimated_duration INTEGER DEFAULT 15, -- Minutes
    xp_reward INTEGER DEFAULT 100,
    difficulty VARCHAR(20) DEFAULT 'beginner',
    prerequisites JSONB DEFAULT '[]'::jsonb, -- Array of required lesson_numbers
    tags JSONB DEFAULT '[]'::jsonb, -- Array of tags for filtering (e.g., ["stocks", "technical-analysis"])
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (module_number BETWEEN 1 AND 4),
    CHECK (lesson_number BETWEEN 1 AND 100),
    CHECK (difficulty IN ('beginner', 'intermediate', 'advanced')),
    CHECK (xp_reward >= 0),
    CHECK (estimated_duration > 0)
);

-- Indexes for lessons table
CREATE INDEX idx_lessons_module ON lessons(module_number);
CREATE INDEX idx_lessons_number ON lessons(lesson_number);
CREATE INDEX idx_lessons_difficulty ON lessons(difficulty);

-- Comments
COMMENT ON TABLE lessons IS 'Educational lesson content for the trading game';
COMMENT ON COLUMN lessons.content IS 'JSONB structure: {"sections": [{"type": "text|image|video", "content": "...", "url": "..."}]}';
COMMENT ON COLUMN lessons.prerequisites IS 'Array of lesson_numbers that must be completed first, e.g., [1, 2, 3]';


-- ============================================
-- TABLE: quizzes
-- Stores quiz questions for each lesson
-- ============================================

CREATE TABLE IF NOT EXISTS quizzes (
    quiz_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lesson_id UUID REFERENCES lessons(lesson_id) ON DELETE CASCADE,
    questions JSONB NOT NULL,  -- Array of question objects
    passing_score INTEGER DEFAULT 70,
    time_limit INTEGER, -- Optional time limit in seconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (passing_score BETWEEN 0 AND 100)
);

-- Index for quizzes table
CREATE INDEX idx_quizzes_lesson ON quizzes(lesson_id);

-- Comments
COMMENT ON TABLE quizzes IS 'Quiz questions for lessons';
COMMENT ON COLUMN quizzes.questions IS 'JSONB array: [{"question": "...", "type": "multiple_choice", "options": [], "correct_answer": 0, "explanation": "..."}]';


-- ============================================
-- TABLE: user_lessons
-- Tracks user progress through lessons
-- ============================================

CREATE TABLE IF NOT EXISTS user_lessons (
    user_lesson_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    lesson_id UUID REFERENCES lessons(lesson_id) ON DELETE CASCADE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    quiz_score INTEGER,
    quiz_attempts INTEGER DEFAULT 0,
    time_spent INTEGER DEFAULT 0, -- Seconds spent on lesson
    progress_percent INTEGER DEFAULT 0, -- How much of the lesson has been read (0-100)
    status VARCHAR(20) DEFAULT 'in_progress',
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE(user_id, lesson_id),
    CHECK (status IN ('in_progress', 'completed', 'failed')),
    CHECK (quiz_score IS NULL OR (quiz_score BETWEEN 0 AND 100)),
    CHECK (quiz_attempts >= 0),
    CHECK (time_spent >= 0),
    CHECK (progress_percent BETWEEN 0 AND 100)
);

-- Indexes for user_lessons table
CREATE INDEX idx_user_lessons_user ON user_lessons(user_id);
CREATE INDEX idx_user_lessons_lesson ON user_lessons(lesson_id);
CREATE INDEX idx_user_lessons_status ON user_lessons(status);
CREATE INDEX idx_user_lessons_completed ON user_lessons(user_id, completed_at) WHERE completed_at IS NOT NULL;

-- Comments
COMMENT ON TABLE user_lessons IS 'Tracks individual user progress through lessons';
COMMENT ON COLUMN user_lessons.progress_percent IS 'Percentage of lesson content read (0-100)';
COMMENT ON COLUMN user_lessons.status IS 'in_progress = reading, completed = passed quiz, failed = quiz score < passing_score';


-- ============================================
-- TABLE: lesson_bookmarks
-- Allows users to bookmark lessons for later
-- ============================================

CREATE TABLE IF NOT EXISTS lesson_bookmarks (
    bookmark_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    lesson_id UUID REFERENCES lessons(lesson_id) ON DELETE CASCADE,
    note TEXT, -- Optional personal note about why bookmarked
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE(user_id, lesson_id)
);

-- Index for lesson_bookmarks table
CREATE INDEX idx_lesson_bookmarks_user ON lesson_bookmarks(user_id);
CREATE INDEX idx_lesson_bookmarks_lesson ON lesson_bookmarks(lesson_id);

-- Comments
COMMENT ON TABLE lesson_bookmarks IS 'User bookmarks for lessons they want to revisit';


-- ============================================
-- TRIGGER: Update updated_at timestamp
-- ============================================

CREATE OR REPLACE FUNCTION update_lessons_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_lessons_updated_at
    BEFORE UPDATE ON lessons
    FOR EACH ROW
    EXECUTE FUNCTION update_lessons_updated_at();


-- ============================================
-- TRIGGER: Update last_accessed timestamp
-- ============================================

CREATE OR REPLACE FUNCTION update_user_lessons_last_accessed()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_accessed = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_lessons_last_accessed
    BEFORE UPDATE ON user_lessons
    FOR EACH ROW
    EXECUTE FUNCTION update_user_lessons_last_accessed();


-- ============================================
-- FUNCTION: Get user's learning statistics
-- ============================================

CREATE OR REPLACE FUNCTION get_user_learning_stats(p_user_id UUID)
RETURNS TABLE(
    total_lessons_started INTEGER,
    total_lessons_completed INTEGER,
    total_time_spent INTEGER,
    average_quiz_score NUMERIC,
    completion_percentage NUMERIC,
    lessons_in_progress INTEGER,
    total_bookmarks INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::INTEGER AS total_lessons_started,
        COUNT(*) FILTER (WHERE status = 'completed')::INTEGER AS total_lessons_completed,
        COALESCE(SUM(time_spent), 0)::INTEGER AS total_time_spent,
        COALESCE(ROUND(AVG(quiz_score) FILTER (WHERE quiz_score IS NOT NULL), 2), 0) AS average_quiz_score,
        COALESCE(ROUND((COUNT(*) FILTER (WHERE status = 'completed')::NUMERIC / NULLIF((SELECT COUNT(*) FROM lessons), 0)) * 100, 2), 0) AS completion_percentage,
        COUNT(*) FILTER (WHERE status = 'in_progress')::INTEGER AS lessons_in_progress,
        (SELECT COUNT(*)::INTEGER FROM lesson_bookmarks WHERE user_id = p_user_id) AS total_bookmarks
    FROM user_lessons
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_user_learning_stats IS 'Returns comprehensive learning statistics for a user';


-- ============================================
-- FUNCTION: Get recommended lessons for user
-- ============================================

CREATE OR REPLACE FUNCTION get_recommended_lessons(p_user_id UUID, p_limit INTEGER DEFAULT 5)
RETURNS TABLE(
    lesson_id UUID,
    lesson_number INTEGER,
    title VARCHAR,
    description TEXT,
    xp_reward INTEGER,
    estimated_duration INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        l.lesson_id,
        l.lesson_number,
        l.title,
        l.description,
        l.xp_reward,
        l.estimated_duration
    FROM lessons l
    WHERE l.lesson_id NOT IN (
        SELECT ul.lesson_id
        FROM user_lessons ul
        WHERE ul.user_id = p_user_id AND ul.status = 'completed'
    )
    -- Check prerequisites are met
    AND (
        l.prerequisites = '[]'::jsonb
        OR NOT EXISTS (
            SELECT 1
            FROM jsonb_array_elements_text(l.prerequisites) AS prereq_num
            WHERE prereq_num::INTEGER NOT IN (
                SELECT ls.lesson_number
                FROM user_lessons ul2
                JOIN lessons ls ON ul2.lesson_id = ls.lesson_id
                WHERE ul2.user_id = p_user_id AND ul2.status = 'completed'
            )
        )
    )
    ORDER BY l.lesson_number
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_recommended_lessons IS 'Returns next recommended lessons based on prerequisites and completion status';


-- ============================================
-- SUCCESS MESSAGE
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '✅ Migration 002 completed successfully!';
    RAISE NOTICE 'Created tables: lessons, quizzes, user_lessons, lesson_bookmarks';
    RAISE NOTICE 'Created functions: get_user_learning_stats, get_recommended_lessons';
    RAISE NOTICE 'Created triggers: update timestamps on lessons and user_lessons';
END $$;
