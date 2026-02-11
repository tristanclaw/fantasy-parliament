import httpx
import asyncio
from datetime import datetime, date, timedelta
from pony.orm import db_session, select, delete
from models import MP, Speech, VoteAttendance, Bill, db
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://openparliament.ca/api/v1"

PARTY_MAPPING = {
    "Conservative": "CPC",
    "Liberal": "Lib",
    "NDP": "NDP",
    "Bloc Québécois": "BQ",
    "Green Party": "GPC",
    "Independent": "Ind"
}

def construct_image_url(name, party_name):
    # Heuristic: Remove spaces/special chars from Last and First names
    # Try to handle complex names simply first
    parts = name.replace(".", "").split()
    if len(parts) >= 2:
        first = parts[0]
        last = "".join(parts[1:])
    else:
        first = name
        last = ""
        
    # Clean up for URL (OurCommons usually removes hyphens in filenames, or keeps them? 
    # Let's try removing them to be safe, or check a real URL if possible. 
    # Actually, standardizing on simple alphanumerics is safest guess.)
    first = first.replace("-", "").replace("'", "")
    last = last.replace("-", "").replace("'", "")
    
    party_code = PARTY_MAPPING.get(party_name, "Ind")
    
    # 44th Parliament
    return f"https://www.ourcommons.ca/Content/Parliamentarians/Images/OfficialMPPhotos/44/{last}{first}_{party_code}.jpg"

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
def cleanup_old_data():
    cutoff_date = date.today() - timedelta(days=7)
    print(f"Cleaning up data older than {cutoff_date}")
    delete(s for s in Speech if s.date < cutoff_date)
    delete(v for v in VoteAttendance if v.date < cutoff_date)
    delete(b for b in Bill if b.date_introduced < cutoff_date)

@db_session
async def sync_mps():
    # Fetch all politicians (limit=1000 to get all)
    url = f"{BASE_URL}/politicians/?limit=1000"
    data = await fetch_json(url)
    
    if not data: return
    
    count = 0
    for mp_data in data['objects']:
        # Filter for current MPs only? 
        # The API returns all, but we only want current probably?
        # The prompt says "current MPs".
        # We can check if 'current_party' exists or uses 'include=current' filter if available.
        # But looking at the JSON, 'current_party' is present for active ones.
        
        # Let's try to grab party and riding from the nested objects
        party_info = mp_data.get('current_party')
        if not party_info:
            continue # Skip if no current party (likely not an active MP)
            
        party_name = party_info.get('short_name', {}).get('en')
        
        riding_info = mp_data.get('current_riding')
        riding_name = riding_info.get('name', {}).get('en') if riding_info else None
        
        slug = mp_data['url'].strip('/').split('/')[-1]
        name = mp_data['name']
        
        mp = MP.get(slug=slug)
        if not mp:
            mp = MP(name=name, slug=slug)
        
        mp.party = party_name
        mp.riding = riding_name
        mp.image_url = construct_image_url(name, party_name)
        
        count += 1
        
    print(f"Synced {count} MPs")

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
    
    # Run cleanup
    cleanup_old_data()

if __name__ == "__main__":
    from models import init_db
    init_db(provider='sqlite', filename='db.sqlite', create_db=True) # Default for testing
    asyncio.run(run_sync())
