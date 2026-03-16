from app.core.contracts.number_words import number_to_words


# Currency code to full name mapping
CURRENCY_NAMES = {
    "USD": "US Dollars",
    "EUR": "Euros",
    "BRL": "Brazilian Reals"
}


def get_currency_name(currency_code: str) -> str:
    """Get the full currency name from currency code."""
    return CURRENCY_NAMES.get(currency_code, currency_code)


def format_amount_with_commas(amount: int) -> str:
    """Format a number with thousand separators (commas)."""
    return f"{amount:,}"


def build_marketing_fields(payload: dict) -> dict:
    """
    Build marketing recoupment fields (numeric + words).
    Backend ONLY provides data - Word handles text generation.
    Now includes currency support (USD/EUR/BRL) with currency names.
    """
    marketing_enabled = payload.get("marketing_recoupment_enabled", False)
    
    if not marketing_enabled:
        return {
            "marketing_recoupment_enabled": False,
            "marketing_recoupment_currency": "USD",
            "marketing_recoupment_currency_name": "US Dollars",
            "marketing_recoupment_amount_numeric": 0,
            "marketing_recoupment_amount_formatted": "0",
            "marketing_recoupment_amount_words": "",
            "marketing_option_enabled": False,
            "marketing_option_currency": "USD",
            "marketing_option_currency_name": "US Dollars",
            "marketing_option_amount_numeric": 0,
            "marketing_option_amount_formatted": "0",
            "marketing_option_amount_words": ""
        }
    
    marketing_amount = int(payload.get("marketing_recoupment_amount", 0))
    marketing_currency = payload.get("marketing_recoupment_currency", "USD")
    marketing_option = payload.get("marketing_option_enabled", False)
    marketing_option_amount = int(payload.get("marketing_option_amount", 0))
    marketing_option_currency = payload.get("marketing_option_currency", "USD")
    
    result = {
        "marketing_recoupment_enabled": True,
        "marketing_recoupment_currency": marketing_currency,
        "marketing_recoupment_currency_name": get_currency_name(marketing_currency),
        "marketing_recoupment_amount_numeric": marketing_amount,
        "marketing_recoupment_amount_formatted": format_amount_with_commas(marketing_amount),
        "marketing_recoupment_amount_words": number_to_words(marketing_amount).title(),
        "marketing_option_enabled": marketing_option,
        "marketing_option_currency": marketing_option_currency,
        "marketing_option_currency_name": get_currency_name(marketing_option_currency)
    }
    
    if marketing_option:
        result["marketing_option_amount_numeric"] = marketing_option_amount
        result["marketing_option_amount_formatted"] = format_amount_with_commas(marketing_option_amount)
        result["marketing_option_amount_words"] = number_to_words(marketing_option_amount).title()
    else:
        result["marketing_option_amount_numeric"] = 0
        result["marketing_option_amount_formatted"] = "0"
        result["marketing_option_amount_words"] = ""
    
    return result


def build_advance(payload: dict) -> dict:
    """
    Build standard advance fields (numeric + words).
    Now includes currency support (USD/EUR/BRL) with currency names.
    """
    advance_enabled = payload.get("advance_enabled", False)
    
    if not advance_enabled:
        return {
            "advance_enabled": False,
            "advance_currency": "USD",
            "advance_currency_name": "US Dollars",
            "advance_amount_numeric": 0,
            "advance_amount_formatted": "0",
            "advance_amount_words": ""
        }
    
    advance_amount = int(payload.get("advance_amount", 0))
    advance_currency = payload.get("advance_currency", "USD")
    
    return {
        "advance_enabled": True,
        "advance_currency": advance_currency,
        "advance_currency_name": get_currency_name(advance_currency),
        "advance_amount_numeric": advance_amount,
        "advance_amount_formatted": format_amount_with_commas(advance_amount),
        "advance_amount_words": number_to_words(advance_amount).title()
    }


def build_milestone_advance(payload: dict) -> dict:
    """
    Build milestone advance fields (numeric + words).
    
    Milestone = conditional advance based on streaming performance:
    - X daily streams
    - for Y consecutive days
    - triggers Z advance amount
    Uses same currency as the main advance.
    """
    milestone_enabled = payload.get("milestone_enabled", False)
    
    if not milestone_enabled:
        return {
            "milestone_enabled": False,
            "milestone_daily_streams": 0,
            "milestone_daily_streams_formatted": "0",
            "milestone_period_days": 0,
            "milestone_advance_amount_numeric": 0,
            "milestone_advance_amount_formatted": "0",
            "milestone_advance_amount_words": ""
        }
    
    milestone_amount = int(payload.get("milestone_advance_amount", 0))
    milestone_daily_streams = int(payload.get("milestone_daily_streams", 0))
    # Milestone uses the same currency as advance
    advance_currency = payload.get("advance_currency", "USD")
    
    return {
        "milestone_enabled": True,
        "milestone_currency": advance_currency,
        "milestone_daily_streams": milestone_daily_streams,
        "milestone_daily_streams_formatted": format_amount_with_commas(milestone_daily_streams),
        "milestone_period_days": payload.get("milestone_period_days", 0),
        "milestone_advance_amount_numeric": milestone_amount,
        "milestone_advance_amount_formatted": format_amount_with_commas(milestone_amount),
        "milestone_advance_amount_words": number_to_words(milestone_amount).title()
    }
