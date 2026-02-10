import httpx
import asyncio
from datetime import datetime, date, timedelta
from pony.orm import db_session, select
from models import MP, Speech, VoteAttendance, Bill, db
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://openparliament.ca/api/v1"

async def fetch_json(url):
    async with httpx.AsyncClient() as client:
        # OpenParliament API often requires a trailing slash
        if not url.endswith('/'):
            url += '/'
        response = await client.get(url, params={"format": "json"}, headers={"Accept": "application/json"})
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

@db_session
async def sync_mps():
    data = await fetch_json(f"{BASE_URL}/politicians/")
    if not data: return
    for mp_data in data['objects']:
        slug = mp_data['url'].strip('/').split('/')[-1]
        mp = MP.get(slug=slug)
        if not mp:
            mp = MP(name=mp_data['name'], slug=slug)
        mp.party = mp_data.get('party')
        # Riding is often in a nested dict or needs extra fetch
        # For now, keep it simple
    print(f"Synced {len(data['objects'])} MPs")

@db_session
async def process_mp_data(mp, yesterday_str):
    # 1. Speeches (+1 point)
    speech_data = await fetch_json(f"{BASE_URL}/debates/?politician={mp.slug}&date={yesterday_str}")
    if speech_data:
        for obj in speech_data.get('objects', []):
            if not Speech.exists(content_url=obj['url']):
                Speech(mp=mp, date=date.fromisoformat(yesterday_str), content_url=obj['url'])
                mp.total_score += 1

    # 2. Votes (+2 points)
    # This is tricky because we need to check ballots.
    # Alternative: check /votes/ and filter by date, then check each vote's ballots.
    # But for a daily sync, maybe we check all votes from yesterday.
    
    # 3. Bills (Sponsored +10, Passed +50)
    bill_data = await fetch_json(f"{BASE_URL}/bills/?sponsor={mp.slug}")
    if bill_data:
        for b in bill_data.get('objects', []):
            bill = Bill.get(number=b['number'])
            if not bill:
                # Need introduced date
                intro_date = b.get('introduced') or yesterday_str
                bill = Bill(number=b['number'], 
                           title=b['name']['en'], 
                           sponsor=mp, 
                           date_introduced=date.fromisoformat(intro_date))
                mp.total_score += 10
            
            # Check if status changed to Royal Assent recently
            if 'Royal Assent' in str(b.get('status', {}).get('en', '')) and not bill.passed:
                bill.passed = True
                mp.total_score += 50

async def sync_votes(yesterday_str):
    # Fetch votes from yesterday
    votes_data = await fetch_json(f"{BASE_URL}/votes/?date={yesterday_str}")
    if not votes_data: return

    for v_data in votes_data.get('objects', []):
        vote_url = v_data['url']
        
        # Security: Validate vote_url to prevent SSRF
        if not vote_url.startswith('/votes/'):
            print(f"Skipping suspicious vote_url: {vote_url}")
            continue
            
        # Fetch ballots for this vote
        ballot_data = await fetch_json(f"{BASE_URL}{vote_url}ballots/")
        if not ballot_data: continue
        
        with db_session:
            for ballot in ballot_data.get('objects', []):
                p_url = ballot['politician_url']
                slug = p_url.strip('/').split('/')[-1]
                mp = MP.get(slug=slug)
                if mp:
                    if not VoteAttendance.exists(mp=mp, vote_url=vote_url):
                        # Any vote cast (Yes, No, Paired) counts as "Attended" for simplicity
                        VoteAttendance(mp=mp, vote_url=vote_url, attended=True, date=date.fromisoformat(yesterday_str))
                        mp.total_score += 2

async def run_sync():
    yesterday = date.today() - timedelta(days=1)
    yesterday_str = yesterday.isoformat()
    
    await sync_mps()
    
    with db_session:
        mps = select(m for m in MP)[:]
    
    # Process MPs with a small delay to avoid overwhelming the API
    for mp in mps:
        await process_mp_data(mp, yesterday_str)
        await asyncio.sleep(0.2) # Rate limiting
    
    await sync_votes(yesterday_str)

if __name__ == "__main__":
    from models import init_db
    init_db(provider='sqlite', filename='db.sqlite', create_db=True) # Default for testing
    asyncio.run(run_sync())
