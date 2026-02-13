from app.core.contracts.number_words import number_to_words


def build_marketing_fields(payload: dict) -> dict:
    """
    Build marketing recoupment fields (numeric + words).
    Backend ONLY provides data - Word handles text generation.
    """
    marketing_enabled = payload.get("marketing_recoupment_enabled", False)
    
    if not marketing_enabled:
        return {
            "marketing_recoupment_enabled": False,
            "marketing_recoupment_amount_numeric": 0,
            "marketing_recoupment_amount_words": "",
            "marketing_option_enabled": False,
            "marketing_option_amount_numeric": 0,
            "marketing_option_amount_words": ""
        }
    
    marketing_amount = payload.get("marketing_recoupment_amount", 0)
    marketing_option = payload.get("marketing_option_enabled", False)
    marketing_option_amount = payload.get("marketing_option_amount", 0)
    
    result = {
        "marketing_recoupment_enabled": True,
        "marketing_recoupment_amount_numeric": marketing_amount,
        "marketing_recoupment_amount_words": number_to_words(marketing_amount).title(),
        "marketing_option_enabled": marketing_option
    }
    
    if marketing_option:
        result["marketing_option_amount_numeric"] = marketing_option_amount
        result["marketing_option_amount_words"] = number_to_words(marketing_option_amount).title()
    else:
        result["marketing_option_amount_numeric"] = 0
        result["marketing_option_amount_words"] = ""
    
    return result


def build_advance(payload: dict) -> dict:
    """
    Build standard advance fields (numeric + words).
    """
    advance_enabled = payload.get("advance_enabled", False)
    
    if not advance_enabled:
        return {
            "advance_enabled": False,
            "advance_amount_numeric": 0,
            "advance_amount_words": ""
        }
    
    advance_amount = payload.get("advance_amount", 0)
    
    return {
        "advance_enabled": True,
        "advance_amount_numeric": advance_amount,
        "advance_amount_words": number_to_words(advance_amount).title()
    }


def build_milestone_advance(payload: dict) -> dict:
    """
    Build milestone advance fields (numeric + words).
    
    Milestone = conditional advance based on streaming performance:
    - X daily streams
    - for Y consecutive days
    - triggers Z advance amount
    """
    milestone_enabled = payload.get("milestone_enabled", False)
    
    if not milestone_enabled:
        return {
            "milestone_enabled": False,
            "milestone_daily_streams": 0,
            "milestone_period_days": 0,
            "milestone_advance_amount_numeric": 0,
            "milestone_advance_amount_words": ""
        }
    
    milestone_amount = payload.get("milestone_advance_amount", 0)
    
    return {
        "milestone_enabled": True,
        "milestone_daily_streams": payload.get("milestone_daily_streams", 0),
        "milestone_period_days": payload.get("milestone_period_days", 0),
        "milestone_advance_amount_numeric": milestone_amount,
        "milestone_advance_amount_words": number_to_words(milestone_amount).title()
    }
