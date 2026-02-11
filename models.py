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

def init_db(provider_or_url='postgres', **kwargs):
    # If a URL is passed, use it directly
    if provider_or_url.startswith('postgres://') or provider_or_url.startswith('postgresql://'):
        print(f"init_db: Binding with URL...")
        db.bind(provider='postgres', dsn=provider_or_url)
        db.generate_mapping(create_tables=True)
        return

    # Fallback to keyword params
    provider = provider_or_url
    user = kwargs.get('user')
    password = kwargs.get('password')
    host = kwargs.get('host')
    database = kwargs.get('database')

    # Run manual migrations using psycopg2 directly before Pony binds
    if provider == 'postgres':
        try:
            import psycopg2
            conn = psycopg2.connect(
                user=user,
                password=password,
                host=host,
                database=database,
                sslmode='require'
            )
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute('ALTER TABLE "MP" ADD COLUMN IF NOT EXISTS "total_score" INTEGER NOT NULL DEFAULT 0')
                cur.execute('ALTER TABLE "MP" ADD COLUMN IF NOT EXISTS "image_url" TEXT')
            conn.close()
            print("Direct Postgres migration successful")
        except Exception as e:
            print(f"Direct migration warning (normal for fresh DB): {e}")

    db.bind(provider=provider, user=user, password=password, host=host, database=database, **kwargs)
    db.generate_mapping(create_tables=True)
