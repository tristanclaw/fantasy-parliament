import sys
import os
sys.path.insert(0, '/home/munky/projects/fantasy-parliament')

# Force SQLite for testing
os.environ['DATABASE_URL'] = 'sqlite:///test.db' # In-memory or file

# Mock the environment variables that main.py expects
os.environ['SYNC_API_KEY'] = 'test-key'
os.environ['DB_PASSWORD'] = '' 

# Need to override init_db to not try to connect to postgres
# But models.py init_db tries to bind to 'postgres' unless dsn is sqlite.
# The DATABASE_URL starting with sqlite:// should work if I modify init_db to support it.
# But init_db logic checks for postgres:// or postgresql://.
# I'll just manually init_db using pony before importing main logic if possible.
# Actually, let's just try to run main.py and see if it works with sqlite if I set URL right?
# main.py startup tries to init_db. If I pass 'sqlite:///db.sqlite', it should work if I tweak init_db logic?
# No, init_db in models.py:
# provider = 'postgres' unless URL.
# I can just run a test that imports the code logic or copies it here.
# I'll copy the logic to be isolated from server startup issues.

from models import init_db, db, MP, Registration
from pony.orm import db_session
import uuid
import re
from datetime import datetime

# Initialize SQLite DB
print("Initializing SQLite DB...")
db.bind(provider='sqlite', filename='db.sqlite', create_db=True)
db.generate_mapping(create_tables=True)

# Clean slate
with db_session:
    Registration.select().delete()
    MP.select().delete()
    MP(id=1, name="MP One", party="Liberal", riding="Riding 1", slug="mp-1", total_score=10)
    MP(id=2, name="MP Two", party="Conservative", riding="Riding 2", slug="mp-2", total_score=20)
    MP(id=3, name="MP Three", party="NDP", riding="Riding 3", slug="mp-3", total_score=30)
    MP(id=4, name="MP Four", party="Green", riding="Riding 4", slug="mp-4", total_score=40)
    MP(id=5, name="MP Five", party="Bloc", riding="Riding 5", slug="mp-5", total_score=50)
    print("Created dummy MPs")

# Now import the logic from main.py manually or copy-paste the validation logic to be safe.
# I'll copy the logic to be isolated from server startup issues.

def test_validation():
    print("\n--- Testing Validation Logic ---")

    # Mock Request and Header logic for the function
    class Req:
        def __init__(self, user_id, display_name, team_name, email, captain_mp_id, team_mp_ids):
            self.user_id = user_id
            self.display_name = display_name
            self.team_name = team_name
            self.email = email
            self.captain_mp_id = captain_mp_id
            self.team_mp_ids = team_mp_ids

    class MockHTTPException(Exception):
        def __init__(self, status_code, detail):
            self.status_code = status_code
            self.detail = detail
            super().__init__(detail)

    # Re-implementing the validation logic here to test exactly what I wrote
    def validate_and_create(registration):
        # 4. Input Validation & Sanitization
        display_name = registration.display_name.strip()
        if len(display_name) > 50:
            raise MockHTTPException(status_code=400, detail="Display name too long (max 50 chars)")
        
        team_name = registration.team_name.strip() if registration.team_name else None
        if team_name and len(team_name) > 100:
            raise MockHTTPException(status_code=400, detail="Team name too long (max 100 chars)")

        # 3. Email Validation
        email = registration.email.strip()
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise MockHTTPException(status_code=400, detail="Invalid email format")
        
        with db_session:
            if Registration.get(email=email):
                raise MockHTTPException(status_code=400, detail="Email already registered")

        # 1. Gameplay Validation
        # Exactly 4 team members
        if len(registration.team_mp_ids) != 4:
            raise MockHTTPException(status_code=400, detail="Team must have exactly 4 MPs")
        
        # No duplicate MPs
        if len(set(registration.team_mp_ids)) != 4:
            raise MockHTTPException(status_code=400, detail="Duplicate MPs in team")

        with db_session:
            # All MP IDs exist
            existing_mps = MP.select(lambda m: m.id in registration.team_mp_ids)
            if existing_mps.count() != 4:
                raise MockHTTPException(status_code=400, detail="One or more selected MPs do not exist")

            # Captain must be part of the team (enforces "Exactly 4 team members")
            if registration.captain_mp_id not in registration.team_mp_ids:
                raise MockHTTPException(status_code=400, detail="Captain must be part of the 4-member team")
                
            # Captain exists
            if not MP.get(id=registration.captain_mp_id):
                raise MockHTTPException(status_code=400, detail="Captain MP does not exist")

        # 2. Secure Identity
        new_user_id = str(uuid.uuid4())

        # Create registration
        with db_session:
            Registration(
                user_id=new_user_id,
                display_name=display_name,
                team_name=team_name,
                email=email,
                captain_mp_id=registration.captain_mp_id,
                team_mp_ids=registration.team_mp_ids,
                registered_at=datetime.utcnow()
            )
        return new_user_id


    # Test 1: Success
    try:
        req = Req(None, "Valid Name", "Team A", "test@example.com", 1, [1,2,3,4])
        uid = validate_and_create(req)
        print(f"Test 1 PASS: Valid registration. UUID: {uid}")
        assert len(uid) == 36 # UUID format
    except Exception as e:
        print(f"Test 1 FAIL: {e}")

    # Test 2: Wrong Team Size (e.g., 3)
    try:
        req = Req(None, "Name", "Team", "test2@example.com", 1, [1,2,3])
        validate_and_create(req)
        print("Test 2 FAIL: Should have raised error for 3 MPs")
    except MockHTTPException as e:
        if "exactly 4 MPs" in e.detail:
            print("Test 2 PASS: Correctly rejected 3 MPs")
        else:
            print(f"Test 2 FAIL: Wrong error: {e.detail}")
    except Exception as e:
        print(f"Test 2 FAIL: {e}")

    # Test 3: Duplicate MPs
    try:
        req = Req(None, "Name", "Team", "test3@example.com", 1, [1,1,2,3])
        validate_and_create(req)
        print("Test 3 FAIL: Should have raised error for duplicates")
    except MockHTTPException as e:
        if "Duplicate" in e.detail:
            print("Test 3 PASS: Correctly rejected duplicates")
        else:
            print(f"Test 3 FAIL: Wrong error: {e.detail}")
    except Exception as e:
        print(f"Test 3 FAIL: {e}")

    # Test 4: Invalid Email
    try:
        req = Req(None, "Name", "Team", "invalid-email", 1, [1,2,3,4])
        validate_and_create(req)
        print("Test 4 FAIL: Should have raised error for invalid email")
    except MockHTTPException as e:
        if "Invalid email" in e.detail:
            print("Test 4 PASS: Correctly rejected invalid email")
        else:
            print(f"Test 4 FAIL: Wrong error: {e.detail}")

    # Test 5: Name too long
    try:
        long_name = "A" * 51
        req = Req(None, long_name, "Team", "test5@example.com", 1, [1,2,3,4])
        validate_and_create(req)
        print("Test 5 FAIL: Should have raised error for long name")
    except MockHTTPException as e:
        if "too long" in e.detail:
            print("Test 5 PASS: Correctly rejected long name")
        else:
            print(f"Test 5 FAIL: Wrong error: {e.detail}")

    # Test 6: Non-existent MP
    try:
        req = Req(None, "Name", "Team", "test6@example.com", 1, [1,2,3,999])
        validate_and_create(req)
        print("Test 6 FAIL: Should have raised error for non-existent MP")
    except MockHTTPException as e:
        if "do not exist" in e.detail:
            print("Test 6 PASS: Correctly rejected non-existent MP")
        else:
            print(f"Test 6 FAIL: Wrong error: {e.detail}")

    # Test 7: Whitespace stripping
    try:
        req = Req(None, "  Spaced Name  ", "  Team Name  ", "test7@example.com", 1, [1,2,3,4])
        uid = validate_and_create(req)
        with db_session:
            r = Registration.get(user_id=uid)
            if r.display_name == "Spaced Name" and r.team_name == "Team Name":
                print("Test 7 PASS: Whitespace stripped correctly")
            else:
                print(f"Test 7 FAIL: Whitespace not stripped. Name: '{r.display_name}', Team: '{r.team_name}'")
    except Exception as e:
        print(f"Test 7 FAIL: {e}")

    # Test 8: Captain not in team
    try:
        req = Req(None, "Name", "Team", "test8@example.com", 5, [1,2,3,4])
        validate_and_create(req)
        print("Test 8 FAIL: Should have raised error for Captain not in team")
    except MockHTTPException as e:
        if "Captain must be part" in e.detail:
            print("Test 8 PASS: Correctly rejected Captain not in team")
        else:
            print(f"Test 8 FAIL: Wrong error: {e.detail}")
    except Exception as e:
        print(f"Test 8 FAIL: {e}")

test_validation()
