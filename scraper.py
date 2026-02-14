import httpx
import asyncio
from datetime import datetime, date, timedelta
from urllib.parse import quote
from pony.orm import db_session, select, delete, count
from models import MP, Speech, VoteAttendance, Bill, db
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.openparliament.ca"

PARTY_MAPPING = {
    "Conservative": "CPC",
    "Liberal": "Lib",
    "NDP": "NDP",
    "Bloc Québécois": "BQ",
    "Green Party": "GPC",
    "Independent": "Ind"
}

# Semaphore to limit concurrent requests
SEMAPHORE_LIMIT = 5

def construct_image_url(name, party_name):
    parts = name.replace(".", "").split()
    if len(parts) >= 2:
        first = parts[0]
        last = "".join(parts[1:])
    else:
        first = name
        last = ""
        
    first = first.replace("-", "").replace("'", "")
    last = last.replace("-", "").replace("'", "")
    
    party_code = PARTY_MAPPING.get(party_name, "Ind")
    
    # Updated for 45th Parliament
    return f"https://www.ourcommons.ca/Content/Parliamentarians/Images/OfficialMPPhotos/45/{last}{first}_{party_code}.jpg"

async def fetch_json(client, url):
    """Fetch JSON with semaphore-limited concurrency."""
    if '?' not in url and not url.endswith('/') and '&' not in url:
        url += '/'
    try:
        headers = {
            "Accept": "application/json",
            "User-Agent": "FantasyParliament/1.0 (contact@example.com)"
        }
        response = await client.get(url, params={"format": "json"}, headers=headers)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

async def fetch_with_semaphore(client, semaphore, url):
    """Wrapper to fetch JSON with semaphore limiting."""
    async with semaphore:
        return await fetch_json(client, url)

@db_session
def cleanup_old_data():
    cutoff_date = date.today() - timedelta(days=7)
    print(f"Cleaning up data older than {cutoff_date}")
    Speech.select(lambda s: s.date < cutoff_date).delete(bulk=True)
    VoteAttendance.select(lambda v: v.date < cutoff_date).delete(bulk=True)
    
    bills_to_check = Bill.select(lambda b: b.date_introduced < cutoff_date)
    for b in bills_to_check:
        if b.date_passed is None or b.date_passed < cutoff_date:
            b.delete()

@db_session
def calculate_all_scores():
    # Prestigious Committees
    PRESTIGIOUS = {"Finance", "Health", "Foreign Affairs", "Public Accounts", "Transport and Infrastructure", "Justice and Human Rights", "Defence", "Indigenous Affairs", "Environment"}
    
    mps = MP.select()[:]
    cutoff_date = date.today() - timedelta(days=7)
    
    print("Recalculating scores...")
    for mp in mps:
        score = 0
        breakdown = {}
        
        # Speeches: 1 point (active in last 7 days)
        speech_pts = mp.speeches.select(lambda s: s.date >= cutoff_date).count() * 1
        score += speech_pts
        breakdown['speeches'] = speech_pts
        
        # Votes: 2 points
        vote_pts = mp.votes.select(lambda v: v.date >= cutoff_date).count() * 2
        score += vote_pts
        breakdown['votes'] = vote_pts
        
        # Bills:
        # +10 if introduced in last 7 days
        # +50 if passed in last 7 days
        bill_pts = 0
        for bill in mp.sponsored_bills:
            if bill.date_introduced >= cutoff_date:
                bill_pts += 10
            if bill.date_passed and bill.date_passed >= cutoff_date:
                bill_pts += 50
        score += bill_pts
        breakdown['bills'] = bill_pts
        
        # Committee Bonus
        comm_pts = 0
        if mp.committees:
            for c in mp.committees:
                name = c.get('name', '')
                role = c.get('role', '')
                if name in PRESTIGIOUS:
                    base = 25 if role == 'Chair' else 10
                    comm_pts += base
        
        score += comm_pts
        breakdown['committees'] = comm_pts
        breakdown['total'] = score
                
        mp.total_score = score
        mp.score_breakdown = breakdown
    print("Score recalculation complete.")

async def sync_mps(client):
    url = f"{BASE_URL}/politicians/?limit=1000&offset=0"
    total_synced = 0
    total_created = 0
    
    print(f"Scraper: Starting MP sync from {url}")
    while url:
        print(f"Scraper: Fetching MPs from {url}")
        try:
            data = await fetch_json(client, url)
        except Exception as e:
            print(f"Scraper: fetch_json error: {e}")
            break
            
        if not data: 
            print("Scraper: No data returned from fetch_json")
            break
        
        objects = data.get('objects', [])
        print(f"Scraper: Found {len(objects)} objects in page")
        
        with db_session:
            for mp_data in objects:
                party_info = mp_data.get('current_party')
                if not party_info:
                    print(f"Scraper: Skipping MP {mp_data.get('name')} (no party info)")
                    continue
                    
                party_name = party_info.get('short_name', {}).get('en')
                
                riding_info = mp_data.get('current_riding')
                riding_name = riding_info.get('name', {}).get('en') if riding_info else None
                
                slug = mp_data['url'].strip('/').split('/')[-1]
                name = mp_data['name']
                
                mp = MP.get(slug=slug)
                if not mp:
                    mp = MP(name=name, slug=slug)
                    total_created += 1
                
                mp.party = party_name
                mp.riding = riding_name

                # Update image URL from API or fallback
                api_image = mp_data.get('image')
                if api_image:
                    mp.image_url = f"https://api.openparliament.ca{api_image}"
                else:
                    mp.image_url = construct_image_url(name, party_name)
                
                total_synced += 1
            
        next_path = data.get('pagination', {}).get('next_url')
        if next_path:
             url = f"{BASE_URL}{next_path}"
        else:
             url = None
        
    print(f"Synced {total_synced} MPs ({total_created} new)")

async def process_mp_data(client, semaphore, mp_slug, start_date_str):
    """Process MP data: speeches and bills. Uses semaphore for rate limiting."""
    # 1. Speeches
    speech_data = await fetch_with_semaphore(
        client, semaphore,
        f"{BASE_URL}/debates/?politician={quote(mp_slug)}&date__gte={start_date_str}"
    )
    if speech_data:
        with db_session:
            mp = MP.get(slug=mp_slug)
            if mp:
                for obj in speech_data.get('objects', []):
                    if not Speech.exists(content_url=obj['url']):
                        Speech(mp=mp, date=date.fromisoformat(obj['date']), content_url=obj['url'])

    Bills
    bill_data = await fetch_with_semaphore(
        client, semaphore,
        f"{BASE_URL}/bills/?sponsor={quote(mp_slug)}"
    )
    if bill_data:
        with db_session:
            mp = MP.get(slug=mp_slug)
            if mp:
                for b in bill_data.get('objects', []):
                    bill = Bill.get(number=b['number'])
                    
                    # Determine introduced date
                    intro_date_str = b.get('introduced') or start_date_str
                    intro_date = date.fromisoformat(intro_date_str)
                    
                    if not bill:
                        bill = Bill(number=b['number'], 
                                   title=b['name']['en'], 
                                   sponsor=mp, 
                                   date_introduced=intro_date)
                    else:
                        bill.date_introduced = intro_date
                    
                    # Check if status indicates Royal Assent
                    status_text = str(b.get('status', {}).get('en', ''))
                    if 'Royal Assent' in status_text:
                        if not bill.passed:
                            bill.passed = True
                            bill.date_passed = date.fromisoformat(start_date_str)
                        elif bill.passed and not bill.date_passed:
                            bill.date_passed = date.fromisoformat(start_date_str)
    
    print(f"Processed MP: {mp_slug}")

async def sync_votes(client, start_date_str):
    """Sync votes with semaphore limiting."""
    votes_url = f"{BASE_URL}/votes/?session=45-1"
    start_date = date.fromisoformat(start_date_str)
    semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)
    
    while votes_url:
        votes_data = await fetch_with_semaphore(client, semaphore, votes_url)
        if not votes_data: break
        
        objects = votes_data.get('objects', [])
        if not objects: break
        
        for v_data in objects:
            vote_date = v_data.get('date')
            if not vote_date: continue
            
            v_date_obj = date.fromisoformat(vote_date)
            if v_date_obj < start_date - timedelta(days=14):
                 votes_url = None
                 break

            if v_date_obj < start_date:
                continue
    
            vote_url = v_data['url']
            
            # Fetch ballots with pagination
            ballot_url = f"{BASE_URL}/votes/ballots/?vote={vote_url}"
            while ballot_url:
                ballot_data = await fetch_with_semaphore(client, semaphore, ballot_url)
                if not ballot_data: break
            
                with db_session:
                    for ballot in ballot_data.get('objects', []):
                        p_url = ballot.get('politician_url')
                        if not p_url: continue
                        
                        slug = p_url.strip('/').split('/')[-1]
                        mp = MP.get(slug=slug)
                        if mp:
                            if not VoteAttendance.exists(mp=mp, vote_url=vote_url):
                                VoteAttendance(mp=mp, vote_url=vote_url, attended=True, date=v_date_obj)
                
                b_next = ballot_data.get('pagination', {}).get('next_url')
                if b_next:
                    ballot_url = f"https://openparliament.ca{b_next}" if b_next.startswith('/') else b_next
                else:
                    ballot_url = None

        if votes_url:
            v_next = votes_data.get('pagination', {}).get('next_url')
            if v_next:
                votes_url = f"https://openparliament.ca{v_next}" if v_next.startswith('/') else v_next
            else:
                votes_url = None

async def sync_single_committee(client, semaphore, mp):
    """Sync committees for a single MP."""
    detail_url = f"{BASE_URL}/politicians/{mp.slug}/"
    data = await fetch_with_semaphore(client, semaphore, detail_url)
    
    if data:
        committees_data = data.get('committees', [])
        formatted = []
        for c in committees_data:
            name = c.get('name') or c.get('committee', {}).get('name')
            role = c.get('position')
            if name:
                formatted.append({"name": name, "role": role})
        
        if formatted:
            with db_session:
                mp_obj = MP.get(id=mp.id)
                if mp_obj:
                    mp_obj.committees = formatted
                    print(f"Updated committees for {mp_obj.name}: {[c['name'] for c in formatted]}")
    
    return mp.slug

async def sync_committees(client, semaphore):
    """Sync all committees using asyncio.gather with semaphore."""
    print("Syncing committees...")
    with db_session:
        mps = list(MP.select())
    
    total = len(mps)
    print(f"Processing {total} MPs for committees...")
    
    # Create tasks for all MPs
    tasks = [sync_single_committee(client, semaphore, mp) for mp in mps]
    
    # Process with gather, semaphore limits concurrency
    results = []
    for i, coro in enumerate(asyncio.as_completed(tasks)):
        result = await coro
        results.append(result)
        if (i + 1) % 20 == 0:
            print(f"Committee sync progress: {i + 1}/{total}")
    
    print("Committee sync complete.")

async def run_sync():
    # Create a single async client for the entire session
    client = httpx.AsyncClient(timeout=30.0)
    semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)
    
    # Fetch data for the last 7 days
    start_date = date.today() - timedelta(days=7)
    start_date_str = start_date.isoformat()
    
    try:
        print(f"Starting MP sync (since {start_date_str})...")
        await sync_mps(client)
        print("MP sync complete, now committees...")
        
        print("Syncing committees...")
        await sync_committees(client, semaphore)
        
        with db_session:
            mp_slugs = [mp.slug for mp in MP.select()]
        
        total_mps = len(mp_slugs)
        print(f"Processing individual MP data for {total_mps} MPs...")
        
        # Use asyncio.gather with semaphore for MP data processing
        tasks = [
            process_mp_data(client, semaphore, mp_slug, start_date_str) 
            for mp_slug in mp_slugs
        ]
        
        # Process in batches to show progress
        for i in range(0, len(tasks), 20):
            batch = tasks[i:i+20]
            await asyncio.gather(*batch)
            print(f"MP data progress: {min(i+20, total_mps)}/{total_mps}")
        
        print("Syncing votes...")
        await sync_votes(client, start_date_str)
        
        print("Cleaning up old data...")
        cleanup_old_data()
        
        print("Calculating scores...")
        calculate_all_scores()
        print("Sync complete.")
    except Exception as e:
        print(f"ERROR in sync: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.aclose()

if __name__ == "__main__":
    from models import db
    db.bind(provider='sqlite', filename='db.sqlite', create_db=True)
    db.generate_mapping(create_tables=True)
    asyncio.run(run_sync())
