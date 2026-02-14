import sys
import os
from unittest.mock import MagicMock
from datetime import datetime

# Set env vars before imports
os.environ['SYNC_API_KEY'] = 'test-key'
os.environ['DB_PASSWORD'] = 'dummy' 
# os.environ['DATABASE_URL'] = 'sqlite:///test.db' # Not used by main at module level, but good to have.

# Import models and bind DB *before* importing main might be safer, 
# but main doesn't bind at module level.
from models import db, Registration, MP
from pony.orm import db_session

# Bind to SQLite
try:
    db.bind(provider='sqlite', filename='db.sqlite', create_db=True)
    db.generate_mapping(create_tables=True)
except Exception as e:
    print(f"DB Binding note: {e}")

# Now import main
# We need to mock fastapi modules if we want to avoid full fastAPI overhead? 
# No, fastAPI is installed.
from fastapi import Request, HTTPException
from main import register_user, RegistrationRequest

def setup_data():
    with db_session:
        Registration.select().delete()
        MP.select().delete()
        MP(id=1, name="MP One", party="Liberal", riding="Riding 1", slug="mp-1", total_score=10)
        MP(id=2, name="MP Two", party="Conservative", riding="Riding 2", slug="mp-2", total_score=20)
        MP(id=3, name="MP Three", party="NDP", riding="Riding 3", slug="mp-3", total_score=30)
        MP(id=4, name="MP Four", party="Green", riding="Riding 4", slug="mp-4", total_score=40)
        MP(id=5, name="MP Five", party="Bloc", riding="Riding 5", slug="mp-5", total_score=50)

def test_rate_limiting():
    print("\n--- Testing Rate Limiting ---")
    setup_data()
    
    # Mock Request
    mock_request = MagicMock(spec=Request)
    mock_request.client.host = "192.168.1.100"
    
    # Create a valid registration request
    def create_req(email):
        return RegistrationRequest(
            user_id="ignore",
            display_name="User",
            team_name="Team",
            email=email,
            captain_mp_id=1,
            team_mp_ids=[1,2,3,4]
        )

    # 1. First registration (Success)
    try:
        register_user(create_req("user1@example.com"), mock_request)
        print("Reg 1: OK")
    except Exception as e:
        print(f"Reg 1 FAIL: {e}")

    # 2. Second registration (Success)
    try:
        register_user(create_req("user2@example.com"), mock_request)
        print("Reg 2: OK")
    except Exception as e:
        print(f"Reg 2 FAIL: {e}")

    # 3. Third registration (Success)
    try:
        register_user(create_req("user3@example.com"), mock_request)
        print("Reg 3: OK")
    except Exception as e:
        print(f"Reg 3 FAIL: {e}")

    # 4. Fourth registration (Fail - Rate Limit)
    try:
        register_user(create_req("user4@example.com"), mock_request)
        print("Reg 4 FAIL: Should have been blocked")
    except HTTPException as e:
        if e.status_code == 429:
            print("Reg 4 PASS: Blocked with 429")
        else:
            print(f"Reg 4 FAIL: Wrong status {e.status_code}")
    except Exception as e:
        print(f"Reg 4 FAIL: Unexpected error {e}")

    # 5. Different IP (Success)
    mock_request_2 = MagicMock(spec=Request)
    mock_request_2.client.host = "192.168.1.101"
    try:
        register_user(create_req("user5@example.com"), mock_request_2)
        print("Reg 5 PASS: Allowed from new IP")
    except Exception as e:
        print(f"Reg 5 FAIL: {e}")

if __name__ == "__main__":
    test_rate_limiting()
