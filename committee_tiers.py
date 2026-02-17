# Committee Tiers - defines prestige levels for parliamentary committees
# Higher tiers = more points for participation

COMMITTEE_TIERS = {
    # A-Tier: Most prestigious, highest point value
    "A-Tier": {
        "weight": 2.0,
        "committees": [
            "Finance",
            "Foreign Affairs",
            "Defence",
            "Treasury Board",
            "Public Accounts",
        ]
    },
    # B-Tier: Important committees
    "B-Tier": {
        "weight": 1.5,
        "committees": [
            "Health",
            "Justice",
            "Industry",
            "Transport",
            "Environment",
            "National Defence",
            "Veterans Affairs",
            "Immigration",
            "Indigenous and Northern Affairs",
            "Ethics",
            "Procedure and House Affairs",
            "Government Operations",
            "Finance",
            "Foreign Affairs and International Development",
        ]
    },
    # C-Tier: Standard committees
    "C-Tier": {
        "weight": 1.0,
        "committees": [
            "Agriculture and Agri-Food",
            "Canadian Heritage",
            "Employment and Social Development",
            "Fisheries and Oceans",
            "Natural Resources",
            "Public Safety and Emergency Preparedness",
            "Science and Research",
            "Small Business",
            "Seniors",
            "Women and Gender Equality",
            "Youth",
            "Housing",
            "Mental Health",
            "International Trade",
            "Climate",
            "Digital Government",
            "Information, Privacy and Ethics",
            "Official Languages",
            "Persons with Disabilities",
            "Veterinary Affairs",
        ]
    },
    # D-Tier: Other/lower profile committees
    "D-Tier": {
        "weight": 0.5,
        "committees": []
    }
}

# Base points for committee participation
COMMITTEE_BASE_POINTS = 10  # Points per committee per scoring period

def get_committee_tier(committee_name: str) -> str:
    """Determine the tier of a committee by name"""
    committee_lower = committee_name.lower()
    
    for tier, data in COMMITTEE_TIERS.items():
        for committee in data["committees"]:
            if committee.lower() in committee_lower or committee_lower in committee.lower():
                return tier
    
    # Default to C-Tier if not found
    return "C-Tier"

def get_tier_weight(tier: str) -> float:
    """Get the point multiplier for a tier"""
    return COMMITTEE_TIERS.get(tier, {}).get("weight", 1.0)

def calculate_committee_score(committees: list) -> dict:
    """
    Calculate committee points based on tier weighting.
    
    Args:
        committees: Can be either:
            - List of strings: ["justice", "science-and-research"]
            - List of dicts: [{"name": "Finance", "role": "Chair"}, ...]
    
    Returns:
        dict with tier breakdown and total points
    """
    if not committees:
        return {"total": 0, "breakdown": {}}
    
    total = 0
    breakdown = {}
    
    for committee in committees:
        # Handle both string format and dict format
        if isinstance(committee, str):
            # String format: "justice" -> name="justice", role="Member"
            name = committee
            role = "Member"
        else:
            # Dict format: {"name": "Finance", "role": "Chair"}
            name = committee.get("name", "")
            role = committee.get("role", "Member")
        
        tier = get_committee_tier(name)
        weight = get_tier_weight(tier)
        
        # Role multiplier: Chair = 1.5x, Vice-Chair = 1.25x, Member = 1x
        role_multiplier = {
            "Chair": 1.5,
            "Vice-Chair": 1.25,
            "Member": 1.0
        }.get(role, 1.0)
        
        points = COMMITTEE_BASE_POINTS * weight * role_multiplier
        total += points
        
        if tier not in breakdown:
            breakdown[tier] = 0
        breakdown[tier] += points
    
    return {"total": total, "breakdown": breakdown}

# Export for easy importing
__all__ = ["COMMITTEE_TIERS", "get_committee_tier", "get_tier_weight", "calculate_committee_score", "COMMITTEE_BASE_POINTS"]
