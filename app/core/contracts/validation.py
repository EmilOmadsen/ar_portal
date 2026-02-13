"""
Contract data validation
"""
from typing import Dict, Any, List, Tuple


def validate_contract_data(payload: Dict[str, Any], contract_type: str = "50_50") -> Tuple[bool, List[str]]:
    """
    Validate contract payload data
    
    Args:
        payload: Contract data to validate
        contract_type: Type of contract being created
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Validate artists
    if "artists" not in payload or not payload["artists"]:
        errors.append("At least one artist is required")
    else:
        for idx, artist in enumerate(payload["artists"], start=1):
            artist_errors = validate_artist(artist, idx)
            errors.extend(artist_errors)
    
    # Validate publishing
    if payload.get("publishing_included"):
        for idx, artist in enumerate(payload.get("artists", []), start=1):
            if not artist.get("ipi"):
                errors.append(f"IPI number required for artist {idx} when publishing is included")
    
    # Contract type specific validations
    if contract_type == "50_50":
        # No additional validations for basic 50/50
        pass
    
    return len(errors) == 0, errors


def validate_artist(artist: Dict[str, Any], index: int) -> List[str]:
    """
    Validate a single artist's data
    
    Args:
        artist: Artist data dictionary
        index: Artist number for error messages
        
    Returns:
        List of validation errors
    """
    errors = []
    required_fields = [
        "stage_name",
        "full_name",
        "address",
        "postcode",
        "city",
        "country",
        "id_number",
        "email",
    ]
    
    for field in required_fields:
        if not artist.get(field):
            errors.append(f"Missing '{field}' for artist {index}")
    
    # Validate email format
    if artist.get("email") and "@" not in artist["email"]:
        errors.append(f"Invalid email format for artist {index}")
    
    return errors


def validate_royalties(royalties: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate royalty data
    
    Args:
        royalties: Royalty structure data
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if "splits" in royalties:
        total = sum(split.get("percentage", 0) for split in royalties["splits"])
        if abs(total - 100.0) > 0.01:
            errors.append(f"Royalty splits must total 100% (currently {total}%)")
    
    return len(errors) == 0, errors


def validate_options(options: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate option clause data
    
    Args:
        options: Option clause data
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if options.get("num_albums") and options["num_albums"] < 1:
        errors.append("Number of option albums must be at least 1")
    
    if options.get("deadline_days") and options["deadline_days"] < 1:
        errors.append("Option deadline must be at least 1 day")
    
    return len(errors) == 0, errors
