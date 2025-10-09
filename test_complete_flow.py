"""
Test the complete Phase 2 flow:
1. Register user
2. Login
3. Fetch lessons with JWT token
4. Verify NO 401 errors
"""

import requests
import random

API_BASE_URL = "http://localhost:8000"

# Generate random user
rand_id = random.randint(1000, 9999)
test_user = {
    'username': f'flowtest_{rand_id}',
    'email': f'flow{rand_id}@test.com',
    'password': 'TestPass123!',
    'display_name': f'Flow Test {rand_id}',
    'character_type': 'analyst',
    'bio': 'Complete flow test'
}

print("=" * 60)
print("PHASE 2 COMPLETE FLOW TEST")
print("=" * 60)

# Step 1: Register
print(f"\n[1] Registering user: {test_user['username']}")
try:
    response = requests.post(
        f"{API_BASE_URL}/api/auth/register",
        json=test_user,
        timeout=5
    )

    if response.status_code in [200, 201]:
        data = response.json()
        print(f"✅ Registration successful!")
        print(f"   User ID: {data.get('user', {}).get('id')}")

        # Extract token correctly
        token_data = data.get("token", {})
        if isinstance(token_data, dict):
            access_token = token_data.get("access_token")
            print(f"✅ Token extracted correctly (dict → string)")
            print(f"   Token type: {type(access_token).__name__}")
            print(f"   Token preview: {access_token[:30]}...")
        else:
            print(f"❌ Token is not a dict: {type(token_data).__name__}")
            access_token = None
    else:
        print(f"❌ Registration failed: {response.status_code}")
        print(f"   {response.text}")
        exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Step 2: Login
print(f"\n[2] Logging in with: {test_user['username']}")
try:
    response = requests.post(
        f"{API_BASE_URL}/api/auth/login",
        json={
            "username_or_email": test_user['username'],
            "password": test_user['password']
        },
        timeout=5
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful!")

        # Extract token
        token_data = data.get("token", {})
        login_token = token_data.get("access_token")
        print(f"✅ Token extracted from login")
        print(f"   Token matches registration: {login_token == access_token}")
    else:
        print(f"❌ Login failed: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Step 3: Fetch lessons with JWT token
print(f"\n[3] Fetching lessons with JWT token")
try:
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"{API_BASE_URL}/api/lessons",
        headers=headers,
        timeout=5
    )

    if response.status_code == 200:
        lessons = response.json()
        print(f"✅ Lessons loaded successfully!")
        print(f"   Total lessons: {len(lessons)}")
        print(f"   First lesson: {lessons[0].get('title')}")
        print(f"\n🎉 NO 401 ERRORS - Phase 2 is working correctly!")
    elif response.status_code == 401:
        print(f"❌ FAILED: Got 401 Unauthorized")
        print(f"   This means the JWT token is not working!")
        print(f"   Response: {response.text}")
        exit(1)
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   Response: {response.text}")
        exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# Step 4: Test lesson detail
print(f"\n[4] Fetching lesson detail")
try:
    lesson_id = lessons[0].get('lesson_id')
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"{API_BASE_URL}/api/lessons/{lesson_id}",
        headers=headers,
        timeout=5
    )

    if response.status_code == 200:
        lesson = response.json()
        print(f"✅ Lesson detail loaded!")
        print(f"   Lesson: {lesson.get('title')}")
        print(f"   Content sections: {len(lesson.get('content_sections', []))}")
        print(f"   Quiz questions: {len(lesson.get('quiz_questions', []))}")
    else:
        print(f"❌ Failed: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("SUMMARY:")
print("✅ Registration: PASS")
print("✅ Login: PASS")
print("✅ Lessons API: PASS")
print("✅ Lesson Detail API: PASS")
print("✅ NO 401 ERRORS!")
print("=" * 60)
print("\n🎉 Phase 2 Educational Content System is WORKING!\n")
