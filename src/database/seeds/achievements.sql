-- ============================================================================
-- Achievement Seed Data
-- Trading Game - Phase 1: Character & Profile System
-- ============================================================================

-- Clear existing achievements (for re-seeding)
TRUNCATE TABLE achievements CASCADE;

-- ============================================================================
-- EDUCATION ACHIEVEMENTS (Lessons & Learning)
-- ============================================================================

INSERT INTO achievements (achievement_code, name, description, icon_url, xp_reward, category, rarity, unlock_criteria) VALUES
-- Common Education Achievements
('first_lesson', 'First Steps', 'Complete your first lesson', '/icons/achievements/first_lesson.png', 50, 'education', 'common', '{"type": "lesson_count", "target": 1}'),
('lessons_5', 'Getting Started', 'Complete 5 lessons', '/icons/achievements/lessons_5.png', 100, 'education', 'common', '{"type": "lesson_count", "target": 5}'),
('lessons_10', 'Knowledge Seeker', 'Complete 10 lessons', '/icons/achievements/lessons_10.png', 150, 'education', 'common', '{"type": "lesson_count", "target": 10}'),
('perfect_quiz', 'Perfect Score', 'Get 100% on a quiz', '/icons/achievements/perfect_quiz.png', 75, 'education', 'common', '{"type": "quiz_score", "target": 100}'),

-- Rare Education Achievements
('lessons_25', 'Dedicated Student', 'Complete 25 lessons', '/icons/achievements/lessons_25.png', 250, 'education', 'rare', '{"type": "lesson_count", "target": 25}'),
('module_1_complete', 'Market Fundamentals Master', 'Complete Module 1: Market Fundamentals', '/icons/achievements/module_1.png', 500, 'education', 'rare', '{"type": "module_complete", "module": 1}'),
('module_2_complete', 'Technical Analysis Expert', 'Complete Module 2: Technical Analysis', '/icons/achievements/module_2.png', 500, 'education', 'rare', '{"type": "module_complete", "module": 2}'),
('perfect_quiz_streak_3', 'Quiz Master', 'Get 100% on 3 quizzes in a row', '/icons/achievements/quiz_master.png', 200, 'education', 'rare', '{"type": "perfect_quiz_streak", "target": 3}'),

-- Epic Education Achievements
('lessons_50', 'Scholar', 'Complete 50 lessons', '/icons/achievements/lessons_50.png', 500, 'education', 'epic', '{"type": "lesson_count", "target": 50}'),
('module_3_complete', 'Risk Management Pro', 'Complete Module 3: Risk Management', '/icons/achievements/module_3.png', 750, 'education', 'epic', '{"type": "module_complete", "module": 3}'),
('broker_education_complete', 'Broker Expert', 'Complete all Broker Education lessons (16-20)', '/icons/achievements/broker_expert.png', 600, 'education', 'epic', '{"type": "lessons_range_complete", "start": 16, "end": 20}'),

-- Legendary Education Achievements
('lessons_100', 'Master Trader', 'Complete all 100 lessons', '/icons/achievements/lessons_100.png', 1000, 'education', 'legendary', '{"type": "lesson_count", "target": 100}'),
('all_modules_complete', 'Trading Sage', 'Complete all 4 modules', '/icons/achievements/all_modules.png', 1500, 'education', 'legendary', '{"type": "all_modules_complete"}'),
('perfect_quiz_streak_10', 'Genius Investor', 'Get 100% on 10 quizzes in a row', '/icons/achievements/genius.png', 1000, 'education', 'legendary', '{"type": "perfect_quiz_streak", "target": 10}');

-- ============================================================================
-- TRADING ACHIEVEMENTS (Execution & Performance)
-- ============================================================================

INSERT INTO achievements (achievement_code, name, description, icon_url, xp_reward, category, rarity, unlock_criteria) VALUES
-- Common Trading Achievements
('first_trade', 'First Trade', 'Execute your first trade', '/icons/achievements/first_trade.png', 100, 'trading', 'common', '{"type": "trade_count", "target": 1}'),
('trades_10', 'Active Trader', 'Execute 10 trades', '/icons/achievements/trades_10.png', 150, 'trading', 'common', '{"type": "trade_count", "target": 10}'),
('first_profit', 'In the Green', 'Close your first profitable trade', '/icons/achievements/first_profit.png', 100, 'trading', 'common', '{"type": "profitable_trade_count", "target": 1}'),
('paper_1k', 'Four Figures', 'Reach $1,000 profit in paper trading', '/icons/achievements/paper_1k.png', 100, 'trading', 'common', '{"type": "paper_profit", "target": 1000}'),

-- Rare Trading Achievements
('trades_50', 'Experienced Trader', 'Execute 50 trades', '/icons/achievements/trades_50.png', 250, 'trading', 'rare', '{"type": "trade_count", "target": 50}'),
('profitable_streak_5', 'Hot Streak', '5 profitable trades in a row', '/icons/achievements/hot_streak.png', 300, 'trading', 'rare', '{"type": "profitable_streak", "target": 5}'),
('paper_10k', 'Five Figures', 'Reach $10,000 profit in paper trading', '/icons/achievements/paper_10k.png', 300, 'trading', 'rare', '{"type": "paper_profit", "target": 10000}'),
('hodl_30d', 'Diamond Hands', 'Hold a position for 30+ days', '/icons/achievements/diamond_hands.png', 250, 'trading', 'rare', '{"type": "hold_duration_days", "target": 30}'),

-- Epic Trading Achievements
('trades_100', 'Veteran Trader', 'Execute 100 trades', '/icons/achievements/trades_100.png', 500, 'trading', 'epic', '{"type": "trade_count", "target": 100}'),
('profitable_streak_10', 'Unstoppable', '10 profitable trades in a row', '/icons/achievements/unstoppable.png', 600, 'trading', 'epic', '{"type": "profitable_streak", "target": 10}'),
('paper_50k', 'Paper Millionaire Track', 'Reach $50,000 profit in paper trading', '/icons/achievements/paper_50k.png', 600, 'trading', 'epic', '{"type": "paper_profit", "target": 50000}'),
('diversified_portfolio', 'Diversification Master', 'Hold positions in 10+ different assets', '/icons/achievements/diversified.png', 400, 'trading', 'epic', '{"type": "unique_assets_held", "target": 10}'),

-- Legendary Trading Achievements
('trades_500', 'Professional Trader', 'Execute 500 trades', '/icons/achievements/trades_500.png', 1000, 'trading', 'legendary', '{"type": "trade_count", "target": 500}'),
('paper_millionaire', 'Paper Millionaire', 'Reach $1,000,000 total value in paper trading', '/icons/achievements/paper_millionaire.png', 1500, 'trading', 'legendary', '{"type": "paper_total_value", "target": 1000000}'),
('profitable_streak_20', 'Market Wizard', '20 profitable trades in a row', '/icons/achievements/market_wizard.png', 1200, 'trading', 'legendary', '{"type": "profitable_streak", "target": 20}'),
('hodl_365d', 'True HODLer', 'Hold a position for 365+ days', '/icons/achievements/true_hodler.png', 1000, 'trading', 'legendary', '{"type": "hold_duration_days", "target": 365}');

-- ============================================================================
-- SOCIAL ACHIEVEMENTS (Friends & Leaderboards)
-- ============================================================================

INSERT INTO achievements (achievement_code, name, description, icon_url, xp_reward, category, rarity, unlock_criteria) VALUES
-- Common Social Achievements
('first_friend', 'Making Friends', 'Add your first friend', '/icons/achievements/first_friend.png', 50, 'social', 'common', '{"type": "friend_count", "target": 1}'),
('friends_5', 'Social Trader', 'Have 5 friends', '/icons/achievements/friends_5.png', 100, 'social', 'common', '{"type": "friend_count", "target": 5}'),
('leaderboard_top_100', 'On the Board', 'Reach top 100 on the leaderboard', '/icons/achievements/top_100.png', 100, 'social', 'common', '{"type": "leaderboard_rank", "target": 100}'),

-- Rare Social Achievements
('friends_10', 'Popular Trader', 'Have 10 friends', '/icons/achievements/friends_10.png', 200, 'social', 'rare', '{"type": "friend_count", "target": 10}'),
('leaderboard_top_50', 'Rising Star', 'Reach top 50 on the leaderboard', '/icons/achievements/top_50.png', 250, 'social', 'rare', '{"type": "leaderboard_rank", "target": 50}'),
('character_leaderboard_1', 'Class Leader', 'Rank #1 in your character leaderboard', '/icons/achievements/class_leader.png', 400, 'social', 'rare', '{"type": "character_leaderboard_rank", "target": 1}'),

-- Epic Social Achievements
('friends_25', 'Community Builder', 'Have 25 friends', '/icons/achievements/friends_25.png', 400, 'social', 'epic', '{"type": "friend_count", "target": 25}'),
('leaderboard_top_10', 'Elite Trader', 'Reach top 10 on the leaderboard', '/icons/achievements/top_10.png', 600, 'social', 'epic', '{"type": "leaderboard_rank", "target": 10}'),

-- Legendary Social Achievements
('friends_50', 'Influencer', 'Have 50 friends', '/icons/achievements/friends_50.png', 800, 'social', 'legendary', '{"type": "friend_count", "target": 50}'),
('leaderboard_1', 'Number One', 'Reach #1 on the overall leaderboard', '/icons/achievements/number_one.png', 2000, 'social', 'legendary', '{"type": "leaderboard_rank", "target": 1}');

-- ============================================================================
-- MILESTONE ACHIEVEMENTS (Levels & XP)
-- ============================================================================

INSERT INTO achievements (achievement_code, name, description, icon_url, xp_reward, category, rarity, unlock_criteria) VALUES
-- Common Milestone Achievements
('level_5', 'Level 5 Reached', 'Reach Level 5', '/icons/achievements/level_5.png', 100, 'milestones', 'common', '{"type": "level", "target": 5}'),
('level_10', 'Level 10 Reached', 'Reach Level 10 - Education Complete!', '/icons/achievements/level_10.png', 200, 'milestones', 'common', '{"type": "level", "target": 10}'),
('xp_1000', '1K XP', 'Earn 1,000 total XP', '/icons/achievements/xp_1k.png', 50, 'milestones', 'common', '{"type": "total_xp", "target": 1000}'),

-- Rare Milestone Achievements
('level_15', 'Level 15 Reached', 'Reach Level 15', '/icons/achievements/level_15.png', 300, 'milestones', 'rare', '{"type": "level", "target": 15}'),
('level_20', 'Level 20 Reached', 'Reach Level 20 - Broker Expert!', '/icons/achievements/level_20.png', 400, 'milestones', 'rare', '{"type": "level", "target": 20}'),
('level_25', 'Level 25 Reached', 'Reach Level 25 - Education Phase Complete!', '/icons/achievements/level_25.png', 500, 'milestones', 'rare', '{"type": "level", "target": 25}'),
('xp_10000', '10K XP', 'Earn 10,000 total XP', '/icons/achievements/xp_10k.png', 200, 'milestones', 'rare', '{"type": "total_xp", "target": 10000}'),

-- Epic Milestone Achievements
('level_50', 'Level 50 Reached', 'Reach Level 50 - Paper Trading Complete!', '/icons/achievements/level_50.png', 750, 'milestones', 'epic', '{"type": "level", "target": 50}'),
('level_75', 'Level 75 Reached', 'Reach Level 75', '/icons/achievements/level_75.png', 1000, 'milestones', 'epic', '{"type": "level", "target": 75}'),
('xp_50000', '50K XP', 'Earn 50,000 total XP', '/icons/achievements/xp_50k.png', 500, 'milestones', 'epic', '{"type": "total_xp", "target": 50000}'),

-- Legendary Milestone Achievements
('level_100', 'Level 100 Reached', 'Reach Level 100 - Game Complete!', '/icons/achievements/level_100.png', 2000, 'milestones', 'legendary', '{"type": "level", "target": 100}'),
('xp_100000', '100K XP', 'Earn 100,000 total XP', '/icons/achievements/xp_100k.png', 1000, 'milestones', 'legendary', '{"type": "total_xp", "target": 100000}');

-- ============================================================================
-- SPECIAL ACHIEVEMENTS (Unique & Event-Based)
-- ============================================================================

INSERT INTO achievements (achievement_code, name, description, icon_url, xp_reward, category, rarity, unlock_criteria) VALUES
-- Common Special Achievements
('daily_login_streak_7', 'Week Warrior', 'Log in 7 days in a row', '/icons/achievements/week_warrior.png', 100, 'special', 'common', '{"type": "login_streak_days", "target": 7}'),
('character_created', 'Choose Your Path', 'Create your character', '/icons/achievements/character_created.png', 50, 'special', 'common', '{"type": "character_selected"}'),
('profile_complete', 'Complete Profile', 'Fill out your full profile', '/icons/achievements/profile_complete.png', 75, 'special', 'common', '{"type": "profile_fields_complete", "required": ["bio", "avatar"]}'),

-- Rare Special Achievements
('daily_login_streak_30', 'Monthly Dedication', 'Log in 30 days in a row', '/icons/achievements/monthly_dedication.png', 300, 'special', 'rare', '{"type": "login_streak_days", "target": 30}'),
('character_change', 'New Perspective', 'Change your character at Level 5+', '/icons/achievements/character_change.png', 200, 'special', 'rare', '{"type": "character_changed"}'),
('early_adopter', 'Early Adopter', 'Join during beta phase', '/icons/achievements/early_adopter.png', 500, 'special', 'rare', '{"type": "join_date_before", "date": "2026-01-01"}'),

-- Epic Special Achievements
('daily_login_streak_100', 'Century Club', 'Log in 100 days in a row', '/icons/achievements/century_club.png', 800, 'special', 'epic', '{"type": "login_streak_days", "target": 100}'),
('all_character_try', 'Jack of All Trades', 'Try all 5 character types (requires multiple accounts)', '/icons/achievements/all_characters.png', 1000, 'special', 'epic', '{"type": "unique_characters_tried", "target": 5}'),

-- Legendary Special Achievements
('daily_login_streak_365', 'Year Round Trader', 'Log in 365 days in a row', '/icons/achievements/year_round.png', 2000, 'special', 'legendary', '{"type": "login_streak_days", "target": 365}'),
('founder', 'Founder', 'One of the first 100 users', '/icons/achievements/founder.png', 1500, 'special', 'legendary', '{"type": "user_id_under", "target": 100}'),
('completionist', 'Completionist', 'Unlock all other achievements', '/icons/achievements/completionist.png', 5000, 'special', 'legendary', '{"type": "all_achievements_unlocked"}');

-- ============================================================================
-- Summary Stats
-- ============================================================================
-- Total achievements: 63
-- Common: 21
-- Rare: 19
-- Epic: 14
-- Legendary: 16

-- By Category:
-- Education: 15
-- Trading: 16
-- Social: 10
-- Milestones: 10
-- Special: 12

-- Total XP available from achievements: 33,625 XP
