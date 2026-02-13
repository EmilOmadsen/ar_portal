from num2words import num2words

def number_to_words(n: int):
    """Convert numeric value to Title Case English words."""
    return num2words(n, lang="en").replace("-", " ").title()

