# How to Run the Trading Game

This guide explains how to run the gamified trading education platform.

## Prerequisites

- Python 3.11+
- PostgreSQL 15+ (for database)
- Virtual environment activated

## Quick Start

### 1. Activate Virtual Environment

```bash
cd c:\Users\infob\Desktop\Agents\trading-dashboard
.\venv\Scripts\activate
```

### 2. Start the Backend API (Terminal 1)

```bash
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
```

**API will be available at:** `http://localhost:8000`
**API Documentation:** `http://localhost:8000/api/docs`

### 3. Start the Game Frontend (Terminal 2)

```bash
python -m streamlit run src/dashboard/game_app.py --server.port=8501
```

**Game will open in your browser at:** `http://localhost:8501`

## User Flow

1. **Character Selection** - Choose one of 5 trading archetypes:
   - 📊 The Analyst (Blue)
   - 🚀 The Risk Taker (Red)
   - 🛡️ The Conservative (Green)
   - ⚡ The Day Trader (Purple)
   - 💎 The HODLer (Cyan)

2. **Registration** - Create your account with:
   - Username (unique)
   - Email (unique)
   - Password (min 8 chars, 1 uppercase, 1 lowercase, 1 number, 1 special)
   - Display Name (unique)
   - Optional bio

3. **Login** - Authenticate with username/email + password

4. **Profile** - View your:
   - Level & XP progress
   - Character info
   - Achievement stats
   - Profile details

## API Endpoints

### Authentication (6 endpoints)
- POST `/api/auth/register` - Register new user
- POST `/api/auth/login` - Login
- POST `/api/auth/logout` - Logout
- GET `/api/auth/me` - Get current user
- POST `/api/auth/forgot-password` - Request password reset
- POST `/api/auth/reset-password` - Reset password

### Users (4 endpoints)
- GET `/api/users/profile` - Get profile
- PUT `/api/users/profile` - Update profile
- DELETE `/api/users/account` - Deactivate account
- GET `/api/users/stats` - Get user stats (XP, level, achievements)

### Characters (4 endpoints)
- GET `/api/characters/list` - Get all 5 character types
- GET `/api/characters/info/{type}` - Get character details
- POST `/api/characters/change` - Change character (Level 5+)
- GET `/api/characters/my-character` - Get user's character

### Achievements (3 endpoints)
- GET `/api/achievements` - List all 63 achievements
- GET `/api/achievements/user` - Get user's achievements
- POST `/api/achievements/unlock` - Unlock achievement (internal)

### Social (5 endpoints)
- POST `/api/social/friend-request` - Send friend request
- PUT `/api/social/friend-request/{id}/accept` - Accept request
- DELETE `/api/social/friend/{username}` - Remove friend
- GET `/api/social/friends` - Get friends list
- GET `/api/social/friend-requests` - Get pending requests

### Leaderboard (3 endpoints)
- GET `/api/leaderboard/overall` - Overall rankings
- GET `/api/leaderboard/character/{type}` - Character rankings
- GET `/api/leaderboard/my-rank` - User's rank

## Files Structure

```
src/
├── dashboard/
│   ├── game_app.py              # Main game application
│   └── pages/
│       ├── character_selection.py  # Character selection UI
│       ├── register.py             # Registration form
│       ├── login.py                # Login form
│       └── profile.py              # User profile page
├── api/
│   ├── main.py                  # FastAPI application
│   ├── routes/                  # 6 route files (auth, users, etc.)
│   ├── models/                  # SQLAlchemy models
│   └── schemas/                 # Pydantic schemas
└── database/
    ├── schema.sql               # Database schema
    └── connection.py            # Database connection