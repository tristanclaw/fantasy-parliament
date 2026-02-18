from pony.orm import Database, Required, Optional, Set, PrimaryKey, db_session, Json
from datetime import date, datetime

db = Database()

class Registration(db.Entity):
    _table_ = 'registration'
    user_id = Required(str, unique=True)
    display_name = Required(str)
    team_name = Optional(str)
    email = Optional(str)
    captain_mp_id = Required(int)
    team_mp_ids = Required(Json)
    ip_address = Optional(str)
    registered_at = Required(datetime, default=datetime.utcnow)

class MP(db.Entity):
    _table_ = 'mp'
    name = Required(str)
    slug = Required(str, unique=True)
    party = Optional(str)
    riding = Optional(str)
    image_url = Optional(str)
    active = Required(bool, default=True)
    committees = Optional(Json) # List of dicts: [{"name": "Finance", "role": "Chair"}, {"name": "Health", "role": "Member"}]
    # speeches = Set('Speech')
    # votes = Set('VoteAttendance')
    # sponsored_bills = Set('Bill', reverse='sponsor')
    daily_scores = Set('DailyScore')
    total_score = Required(int, default=0)
    score_breakdown = Optional(Json) # Stores points from speeches, votes, bills, committees
    penalty = Optional(int, default=0) # Permanent penalty subtracted from score

class DailyScore(db.Entity):
    _table_ = 'dailyscore'
    mp = Required(MP)
    mp_name = Required(str)
    party = Optional(str)
    riding = Optional(str)
    points_today = Required(int)
    date = Required(date)

class LeaderboardEntry(db.Entity):
    _table_ = 'leaderboardentry'
    username = Required(str, unique=True)
    score = Required(int)
    updated_at = Required(datetime)

# class Speech(db.Entity):
#     _table_ = 'speech'
#     mp = Required(MP)
#     date = Required(date)
#     content_url = Required(str)

# class VoteAttendance(db.Entity):
#     _table_ = 'voteattendance'
#     mp = Required(MP)
#     vote_url = Required(str)
#     attended = Required(bool)
#     date = Required(date)

# class Bill(db.Entity):
#     _table_ = 'bill'
#     number = Required(str)
#     title = Required(str)
#     sponsor = Required(MP)
#     passed = Required(bool, default=False)
#     date_introduced = Required(date)
#     date_passed = Optional(date)

class Subscriber(db.Entity):
    _table_ = 'subscriber'
    name = Required(str)
    email = Required(str, unique=True)
    selected_mps = Required(Json)  # JSON array of MP IDs
    unsubscribe_token = Required(str, unique=True)
    created_at = Required(datetime, default=datetime.utcnow)

@db_session
def run_migrations(dsn=None, **kwargs):
    """
    Run manual migrations using psycopg2 directly.
    This can be called at startup (safe mode) or via API.
    """
    import psycopg2
    import os
    
    print("Starting manual migrations...")
    try:
        # Construct DSN if not provided
        if not dsn:
            db_url = os.getenv('INTERNAL_DATABASE_URL') or os.getenv('DATABASE_URL_INTERNAL') or os.getenv('DATABASE_URL')
            if db_url:
                dsn = db_url
                if dsn.startswith('postgres://'):
                    dsn = dsn.replace('postgres://', 'postgresql://', 1)
        
        if dsn:
            if 'sslmode=' not in dsn:
                separator = '&' if '?' in dsn else '?'
                dsn += f"{separator}sslmode=require"
            conn = psycopg2.connect(dsn, connect_timeout=10)
        else:
            conn = psycopg2.connect(
                user=kwargs.get('user') or os.getenv('DB_USER'),
                password=kwargs.get('password') or os.getenv('DB_PASSWORD'),
                host=kwargs.get('host') or os.getenv('DB_HOST'),
                database=kwargs.get('database') or os.getenv('DB_NAME'),
                sslmode='require',
                connect_timeout=10
            )
        
        conn.autocommit = True
        with conn.cursor() as cur:
            # Audit tables first to debug
            print("Auditing tables in public schema...")
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = [t[0] for t in cur.fetchall()]
            print(f"Found tables: {tables}")

            # Migration 1: MP.total_score
            for table in ['mp', 'MP']:
                if table in tables:
                    try:
                        cur.execute(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "total_score" INTEGER NOT NULL DEFAULT 0')
                        print(f"Applied/Checked: {table}.total_score")
                    except Exception as e:
                        print(f"Migration warning ({table}.total_score): {e}")
            
            # Migration 2: MP.image_url
            for table in ['mp', 'MP']:
                if table in tables:
                    try:
                        cur.execute(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "image_url" TEXT')
                        print(f"Applied/Checked: {table}.image_url")
                    except Exception as e:
                        print(f"Migration warning ({table}.image_url): {e}")

            # Migration 3: Bill.date_passed - REMOVED (Table deprecated)
            # for table in ['bill', 'Bill']:
            #     if table in tables:
            #         try:
            #             cur.execute(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "date_passed" DATE')
            #             print(f"Applied/Checked: {table}.date_passed")
            #         except Exception as e:
            #             print(f"Migration warning ({table}.date_passed): {e}")

            # Migration 4: Registration.ip_address
            for table in ['registration', 'Registration']:
                if table in tables:
                    try:
                        cur.execute(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "ip_address" TEXT')
                        # Ensure it's nullable
                        cur.execute(f'ALTER TABLE "{table}" ALTER COLUMN "ip_address" DROP NOT NULL')
                        print(f"Applied/Checked: {table}.ip_address")
                    except Exception as e:
                        print(f"Migration warning ({table}.ip_address): {e}")

            # Migration 10: Registration nullability
            for table in ['registration', 'Registration']:
                if table in tables:
                    try:
                        cur.execute(f'ALTER TABLE "{table}" ALTER COLUMN "team_name" DROP NOT NULL')
                        print(f"Applied/Checked: {table}.team_name nullable")
                    except Exception as e:
                        print(f"Migration warning ({table}.team_name nullability): {e}")

            # Migration 5: MP.committees
            for table in ['mp', 'MP']:
                if table in tables:
                    try:
                        cur.execute(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "committees" JSONB')
                        print(f"Applied/Checked: {table}.committees")
                    except Exception as e:
                        print(f"Migration warning ({table}.committees): {e}")

            # Migration 6: MP.score_breakdown
            for table in ['mp', 'MP']:
                if table in tables:
                    try:
                        cur.execute(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "score_breakdown" JSONB')
                        print(f"Applied/Checked: {table}.score_breakdown")
                    except Exception as e:
                        print(f"Migration warning ({table}.score_breakdown): {e}")

            # Migration 9: MP.active
            for table in ['mp', 'MP']:
                if table in tables:
                    try:
                        cur.execute(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "active" BOOLEAN NOT NULL DEFAULT TRUE')
                        print(f"Applied/Checked: {table}.active")
                    except Exception as e:
                        print(f"Migration warning ({table}.active): {e}")

            # Migration 11: MP.penalty
            print("DEBUG: Checking for penalty migration...")
            for table in ['mp', 'MP']:
                if table in tables:
                    try:
                        cur.execute(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "penalty" INTEGER NOT NULL DEFAULT 0')
                        print(f"Applied/Checked: {table}.penalty")
                    except Exception as e:
                        print(f"Migration warning ({table}.penalty): {e}")

            # Migration 7: Subscriber table
            if 'subscriber' not in tables and 'Subscriber' not in tables:
                try:
                    cur.execute('''
                        CREATE TABLE "subscriber" (
                            id SERIAL PRIMARY KEY,
                            name TEXT NOT NULL,
                            email TEXT UNIQUE NOT NULL,
                            "selected_mps" JSONB NOT NULL,
                            "unsubscribe_token" TEXT UNIQUE NOT NULL,
                            "created_at" TIMESTAMP NOT NULL DEFAULT NOW()
                        )
                    ''')
                    print("Created table: subscriber")
                except Exception as e:
                    print(f"Migration warning (subscriber table): {e}")
            else:
                 # Migration 8: Subscriber.unsubscribe_token
                for table in ['subscriber', 'Subscriber']:
                    if table in tables:
                        try:
                            # Add column as nullable first
                            cur.execute(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "unsubscribe_token" TEXT')
                            # Populate with random tokens for existing rows
                            cur.execute(f'''
                                UPDATE "{table}" 
                                SET "unsubscribe_token" = md5(random()::text || clock_timestamp()::text) 
                                WHERE "unsubscribe_token" IS NULL
                            ''')
                            # Make not null and unique
                            cur.execute(f'ALTER TABLE "{table}" ALTER COLUMN "unsubscribe_token" SET NOT NULL')
                            cur.execute(f'ALTER TABLE "{table}" ADD CONSTRAINT "{table}_unsubscribe_token_key" UNIQUE ("unsubscribe_token")')
                            print(f"Applied/Checked: {table}.unsubscribe_token")
                        except Exception as e:
                            print(f"Migration warning ({table}.unsubscribe_token): {e}")
                
        conn.close()
        print("Direct Postgres migration successful")
        return True, f"Migrations completed. Tables found: {tables}"
    except Exception as e:
        error_msg = f"Direct migration failed: {e}"
        print(error_msg)
        return False, error_msg

def init_db(provider_or_url='postgres', safe_mode=True, **kwargs):
    dsn = None
    provider = provider_or_url

    # Check if first arg is a URL
    if provider_or_url.startswith('postgres://') or provider_or_url.startswith('postgresql://'):
        provider = 'postgres'
        dsn = provider_or_url
        if dsn.startswith('postgres://'):
            dsn = dsn.replace('postgres://', 'postgresql://', 1)

    # Bind Pony first so run_migrations can use the provider
    try:
        if dsn:
            print(f"init_db: Binding with URL (len={len(dsn)})...")
            # Ensure sslmode is required for Pony/psycopg2
            if 'sslmode=' not in dsn:
                separator = '&' if '?' in dsn else '?'
                dsn += f"{separator}sslmode=require"
            db.bind(provider='postgres', dsn=dsn)
        else:
            # Pass through the original provider string (e.g. 'sqlite') if not a URL
            db.bind(provider=provider, **kwargs)

        db.generate_mapping(create_tables=True)
        print("PonyORM binding and mapping successful")
    except Exception as e:
        print(f"PonyORM binding failed: {e}")
        if not safe_mode:
            raise

    # Run manual migrations using psycopg2 directly via Pony connection
    if provider == 'postgres':
        success, msg = run_migrations(dsn, **kwargs)
        if not success:
            if safe_mode:
                print(f"WARNING: {msg} - Continuing startup in safe mode.")
            else:
                raise Exception(msg)
