class RegistrationRequest(BaseModel):
    user_id: Optional[str] = None
    display_name: str
    team_name: Optional[str] = None
    email: str
    captain_mp_id: int
    team_mp_ids: List[int]

@app.post("/api/register")
@db_session
def register_user(registration: RegistrationRequest):
    # 4. Input Validation & Sanitization
    display_name = registration.display_name.strip()
    if len(display_name) > 50:
        raise HTTPException(status_code=400, detail="Display name too long (max 50 chars)")
    
    team_name = registration.team_name.strip() if registration.team_name else None
    if team_name and len(team_name) > 100:
        raise HTTPException(status_code=400, detail="Team name too long (max 100 chars)")

    # 3. Email Validation
    email = registration.email.strip()
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    if Registration.get(email=email):
         raise HTTPException(status_code=400, detail="Email already registered")

    # 1. Gameplay Validation
    # Exactly 4 team members
    if len(registration.team_mp_ids) != 4:
        raise HTTPException(status_code=400, detail="Team must have exactly 4 MPs")
    
    # No duplicate MPs
    if len(set(registration.team_mp_ids)) != 4:
         raise HTTPException(status_code=400, detail="Duplicate MPs in team")

    # All MP IDs exist
    # Note: PonyORM select with 'in' list works fine for integers
    existing_mps = MP.select(lambda m: m.id in registration.team_mp_ids)
    if existing_mps.count() != 4:
         raise HTTPException(status_code=400, detail="One or more selected MPs do not exist")
         
    # Captain exists
    if not MP.get(id=registration.captain_mp_id):
        raise HTTPException(status_code=400, detail="Captain MP does not exist")

    # 2. Secure Identity
    # Ignore client-provided user_id and generate a secure UUID
    new_user_id = str(uuid.uuid4())

    # Create registration
    try:
        Registration(
            user_id=new_user_id,
            display_name=display_name,
            team_name=team_name,
            email=email,
            captain_mp_id=registration.captain_mp_id,
            team_mp_ids=registration.team_mp_ids,
            registered_at=datetime.utcnow()
        )
        # Placeholder for mailing list integration
        print(f"MAILING LIST: Added {email} to mailing list.")
        
        return {
            "status": "success", 
            "message": "Registration successful",
            "user_id": new_user_id 
        }
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")
