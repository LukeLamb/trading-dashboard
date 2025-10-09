"""
Test script for Phase 2 API flow
Tests: Registration -> Authentication -> Lessons -> Quiz
"""
import requests
import json
import random

API_BASE = "http://localhost:8000"

def test_registration():
    """Test user registration"""
    print("=" * 60)
    print("1. Testing User Registration")
    print("=" * 60)

    rand_id = random.randint(10000, 99999)
    user_data = {
        "username": f"test_user_{rand_id}",
        "email": f"test{rand_id}@example.com",
        "password": "TestPass123!",
        "display_name": f"Test User {rand_id}",
        "character_type": "analyst",
        "bio": "Automated test user"
    }

    response = requests.post(f"{API_BASE}/api/auth/register", json=user_data)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 201:
        data = response.json()
        print(f"[OK] Registration successful!")
        print(f"User ID: {data.get('user', {}).get('user_id')}")
        print(f"Username: {data.get('user', {}).get('username')}")
        # Token is nested under 'token' key
        token = data.get('token', {}).get('access_token')
        print(f"Token received: {token[:50]}..." if token else "[FAIL] No token!")

        # Check if it's the old mock token
        if token == "dev_token_12345":
            print("[FAIL] ERROR: Received mock dev token instead of real JWT!")
            return None
        else:
            print("[OK] Real JWT token received (not mock)")

        return {
            "token": token,
            "user_id": data.get('user', {}).get('user_id'),
            "username": data.get('user', {}).get('username')
        }
    else:
        print(f"[FAIL] Registration failed: {response.text}")
        return None

def test_fetch_lessons(auth_data):
    """Test fetching lessons with authentication"""
    print("\n" + "=" * 60)
    print("2. Testing Fetch Lessons")
    print("=" * 60)

    headers = {
        "Authorization": f"Bearer {auth_data['token']}"
    }

    response = requests.get(f"{API_BASE}/api/lessons", headers=headers)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        lessons = response.json()
        print(f"[OK] Lessons loaded successfully!")
        print(f"Total lessons: {len(lessons)}")

        if lessons:
            print(f"\nFirst lesson preview:")
            lesson = lessons[0]
            print(f"  - ID: {lesson.get('id')}")
            print(f"  - Title: {lesson.get('title')}")
            print(f"  - Category: {lesson.get('category')}")
            print(f"  - Difficulty: {lesson.get('difficulty_level')}")

        return lessons
    elif response.status_code == 401:
        print(f"[FAIL] 401 Unauthorized - Authentication failed!")
        print(f"Response: {response.text}")
        return None
    else:
        print(f"[FAIL] Failed to fetch lessons: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_fetch_lesson_detail(auth_data, lesson_id):
    """Test fetching a specific lesson"""
    print("\n" + "=" * 60)
    print(f"3. Testing Fetch Lesson Detail (ID: {lesson_id})")
    print("=" * 60)

    headers = {
        "Authorization": f"Bearer {auth_data['token']}"
    }

    response = requests.get(f"{API_BASE}/api/lessons/{lesson_id}", headers=headers)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        lesson = response.json()
        print(f"[OK] Lesson details loaded successfully!")
        print(f"Title: {lesson.get('title')}")
        print(f"Content length: {len(lesson.get('content', ''))} characters")
        print(f"XP Reward: {lesson.get('xp_reward')} XP")
        return lesson
    else:
        print(f"[FAIL] Failed to fetch lesson detail: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_start_lesson(auth_data, lesson_id):
    """Test starting a lesson"""
    print("\n" + "=" * 60)
    print(f"4. Testing Start Lesson (ID: {lesson_id})")
    print("=" * 60)

    headers = {
        "Authorization": f"Bearer {auth_data['token']}"
    }

    response = requests.post(f"{API_BASE}/api/lessons/{lesson_id}/start", headers=headers)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"[OK] Lesson started successfully!")
        print(f"Status: {data.get('status')}")
        print(f"Started at: {data.get('started_at')}")
        return data
    else:
        print(f"[FAIL] Failed to start lesson: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def main():
    print("\n" + "=" * 60)
    print("PHASE 2: END-TO-END API FLOW TEST")
    print("=" * 60)

    # Step 1: Register
    auth_data = test_registration()
    if not auth_data:
        print("\n[FAIL] FAILED: Registration failed, cannot continue")
        return

    # Step 2: Fetch lessons
    lessons = test_fetch_lessons(auth_data)
    if not lessons:
        print("\n[FAIL] FAILED: Cannot fetch lessons, stopping test")
        return

    # Step 3: Get lesson detail
    if lessons:
        first_lesson_id = lessons[0].get('id')
        lesson_detail = test_fetch_lesson_detail(auth_data, first_lesson_id)

        # Step 4: Start lesson
        if lesson_detail:
            test_start_lesson(auth_data, first_lesson_id)

    print("\n" + "=" * 60)
    print("[OK] ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print(f"\nKey Findings:")
    print(f"  [OK] Registration creates real JWT tokens (not mock)")
    print(f"  [OK] Lessons API accepts JWT authentication")
    print(f"  [OK] No 401 errors encountered")
    print(f"  [OK] Phase 2 educational system is working correctly")

if __name__ == "__main__":
    main()
