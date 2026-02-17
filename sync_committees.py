#!/usr/bin/env python3
"""
Sync committee memberships from OpenParliament API.
Run locally, then upload JSON to the site.
"""
import asyncio
import httpx
import json
from urllib.parse import quote

BASE_URL = "https://api.openparliament.ca"

async def fetch_all_committee_data():
    """Fetch all MPs and their committee memberships from speeches."""
    print("Fetching MP list...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get all MPs
        mp_resp = await client.get(f"{BASE_URL}/politicians/?limit=500&format=json")
        mp_data = mp_resp.json()
        
        mps = []
        for obj in mp_data.get('objects', []):
            mps.append({
                'url': obj.get('url', '').strip('/'),
                'name': obj.get('name')
            })
        
        print(f"Found {len(mps)} MPs, fetching committee data...")
        
        committee_data = []
        
        for i, mp in enumerate(mps):
            slug = mp['url'].split('/')[-1]
            
            try:
                # Fetch recent speeches (limit 30 to be faster)
                speech_resp = await client.get(
                    f"{BASE_URL}/speeches/?politician={quote(slug)}&limit=30&format=json"
                )
                speech_data = speech_resp.json()
                
                committees = set()
                for speech in speech_data.get('objects', []):
                    doc_url = speech.get('document_url', '')
                    if '/committees/' in doc_url:
                        parts = doc_url.split('/')
                        if 'committees' in parts:
                            idx = parts.index('committees')
                            if idx + 1 < len(parts):
                                committees.add(parts[idx + 1])
                
                if committees:
                    committee_data.append({
                        'slug': slug,
                        'committees': list(committees)
                    })
                    print(f"  [{i+1}/{len(mps)}] {mp['name']}: {committees}")
                else:
                    print(f"  [{i+1}/{len(mps)}] {mp['name']}: (none)")
                    
            except Exception as e:
                print(f"  Error {mp['name']}: {e}")
        
        return committee_data

async def upload_to_site(committee_data):
    """Upload committee data to the site."""
    import requests
    
    api_key = "tristan_fantasy_secret_2026"
    url = "https://fantasy-parliament-web.onrender.com/admin/update-committees"
    
    print(f"\nUploading {len(committee_data)} MPs to site...")
    
    response = requests.post(
        url,
        json=committee_data,
        headers={"X-API-Key": api_key}
    )
    
    print(f"Response: {response.status_code}")
    print(response.text)

async def main():
    # First, just fetch and save to file
    data = await fetch_all_committee_data()
    
    # Save to file
    with open('committees.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\nSaved {len(data)} MPs with committees to committees.json")
    
    # Ask if user wants to upload
    response = input("\nUpload to site? (y/n): ")
    if response.lower() == 'y':
        await upload_to_site(data)

if __name__ == "__main__":
    asyncio.run(main())
