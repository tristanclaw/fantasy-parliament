import os
import sys
import traceback
import psycopg2
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv('INTERNAL_DATABASE_URL') or os.getenv('DATABASE_URL_INTERNAL') or os.getenv('DATABASE_URL')
db_password = os.getenv('DB_PASSWORD')

def get_connection():
    if db_url:
        dsn = db_url
        if dsn.startswith('postgres://'):
            dsn = dsn.replace('postgres://', 'postgresql://', 1)
        # Try to use external URL if provided in env, else use the components
        # Note: Render provides INTERNAL_DATABASE_URL and DATABASE_URL (external)
        return psycopg2.connect(dsn)
    else:
        # Construct DSN string to ensure sslmode is handled by psycopg2
        dsn = f"dbname={os.getenv('DB_NAME')} user={os.getenv('DB_USER')} password={os.getenv('DB_PASSWORD')} host={os.getenv('DB_HOST')} sslmode=require"
        return psycopg2.connect(dsn)

try:
    conn = get_connection()
    conn.autocommit = True
    with conn.cursor() as cur:
        print("Checking tables in 'public' schema:")
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE';
        """)
        tables = cur.fetchall()
        for t in tables:
            print(f"Table: {t[0]}")
            
        for table_name in ['mp', 'MP', 'LeaderboardEntry', 'leaderboardentry', 'Speech', 'speech', 'VoteAttendance', 'voteattendance', 'Bill', 'bill']:
            print(f"\nChecking columns for table: {table_name}")
            try:
                cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s", (table_name,))
                cols = cur.fetchall()
                if not cols:
                    print(f"  No columns found (table might not exist or case mismatch)")
                for c in cols:
                    print(f"  Column: {c[0]} ({c[1]})")
            except Exception as e:
                print(f"  Error checking {table_name}: {e}")

    conn.close()
except Exception as e:
    print(f"Connection error: {e}")
    traceback.print_exc()
