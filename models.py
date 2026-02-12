from pony.orm import Database, Required, Optional, Set, PrimaryKey
from datetime import date, datetime

db = Database()

class MP(db.Entity):
    name = Required(str)
    slug = Required(str, unique=True)
    party = Optional(str)
    riding = Optional(str)
    image_url = Optional(str)
    speeches = Set('Speech')
    votes = Set('VoteAttendance')
    sponsored_bills = Set('Bill', reverse='sponsor')
    total_score = Required(int, default=0)

class LeaderboardEntry(db.Entity):
    username = Required(str, unique=True)
    score = Required(int)
    updated_at = Required(datetime)

class Speech(db.Entity):
    mp = Required(MP)
    date = Required(date)
    content_url = Required(str)

class VoteAttendance(db.Entity):
    mp = Required(MP)
    vote_url = Required(str)
    attended = Required(bool)
    date = Required(date)

class Bill(db.Entity):
    number = Required(str)
    title = Required(str)
    sponsor = Required(MP)
    passed = Required(bool, default=False)
    date_introduced = Required(date)
    date_passed = Optional(date)

def init_db(provider_or_url='postgres', **kwargs):
    dsn = None
    provider = provider_or_url

    # Check if first arg is a URL
    if provider_or_url.startswith('postgres://') or provider_or_url.startswith('postgresql://'):
        provider = 'postgres'
        dsn = provider_or_url
        if dsn.startswith('postgres://'):
            dsn = dsn.replace('postgres://', 'postgresql://', 1)

    # Run manual migrations using psycopg2 directly before Pony binds
    # Only if provider is postgres
    if provider == 'postgres':
        try:
            import psycopg2
            if dsn:
                # Handle Render's postgres:// vs postgresql:// for psycopg2 if needed
                # psycopg2 usually handles postgres:// fine, but let's pass it directly.
                conn = psycopg2.connect(dsn, sslmode='require')
            else:
                conn = psycopg2.connect(
                    user=kwargs.get('user'),
                    password=kwargs.get('password'),
                    host=kwargs.get('host'),
                    database=kwargs.get('database'),
                    sslmode='require'
                )
            
            conn.autocommit = True
            with conn.cursor() as cur:
                try:
                    cur.execute('ALTER TABLE "MP" ADD COLUMN IF NOT EXISTS "total_score" INTEGER NOT NULL DEFAULT 0')
                except Exception as e:
                    print(f"Migration warning (MP.total_score): {e}")
                
                try:
                    cur.execute('ALTER TABLE "MP" ADD COLUMN IF NOT EXISTS "image_url" TEXT')
                except Exception as e:
                    print(f"Migration warning (MP.image_url): {e}")

                try:
                    cur.execute('ALTER TABLE "Bill" ADD COLUMN IF NOT EXISTS "date_passed" DATE')
                except Exception as e:
                    print(f"Migration warning (Bill.date_passed): {e}")
            conn.close()
            print("Direct Postgres migration successful")
        except Exception as e:
            print(f"Direct migration warning (normal for fresh DB or connection error): {e}")

    # Bind Pony
    if dsn:
        print(f"init_db: Binding with URL...")
        db.bind(provider='postgres', dsn=dsn)
    else:
        # Pass through the original provider string (e.g. 'sqlite') if not a URL
        db.bind(provider=provider_or_url, **kwargs)

    db.generate_mapping(create_tables=True)
