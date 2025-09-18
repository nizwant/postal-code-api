"""
Polish Character Normalizer

Utility for converting Polish diacritical characters to ASCII equivalents
for user-friendly search functionality. Used by both Flask and FastAPI implementations.
"""

def normalize_polish_text(text):
    """
    Convert Polish characters to ASCII equivalents.

    Args:
        text (str or None): Text to normalize

    Returns:
        str or None: Normalized text, or None if input was None
    """
    if not text:
        return text

    POLISH_CHAR_MAP = {
        # Lowercase Polish characters
        'ą': 'a',
        'ć': 'c',
        'ę': 'e',
        'ł': 'l',
        'ń': 'n',
        'ó': 'o',
        'ś': 's',
        'ź': 'z',
        'ż': 'z',

        # Uppercase Polish characters
        'Ą': 'A',
        'Ć': 'C',
        'Ę': 'E',
        'Ł': 'L',
        'Ń': 'N',
        'Ó': 'O',
        'Ś': 'S',
        'Ź': 'Z',
        'Ż': 'Z'
    }

    result = text
    for polish_char, ascii_char in POLISH_CHAR_MAP.items():
        result = result.replace(polish_char, ascii_char)

    return result


def normalize_search_params(city=None, street=None, province=None, county=None, municipality=None, **kwargs):
    """
    Normalize search parameters by converting Polish characters to ASCII equivalents.

    Args:
        city (str, optional): City name
        street (str, optional): Street name
        province (str, optional): Province name
        county (str, optional): County name
        municipality (str, optional): Municipality name
        **kwargs: Other parameters (passed through unchanged)

    Returns:
        dict: Dictionary with normalized parameters
    """
    normalized_params = kwargs.copy()

    # Normalize text parameters that may contain Polish characters
    if city:
        normalized_params['city'] = normalize_polish_text(city)
    if street:
        normalized_params['street'] = normalize_polish_text(street)
    if province:
        normalized_params['province'] = normalize_polish_text(province)
    if county:
        normalized_params['county'] = normalize_polish_text(county)
    if municipality:
        normalized_params['municipality'] = normalize_polish_text(municipality)

    return normalized_params


def get_normalized_search_params(city=None, street=None, province=None, county=None, municipality=None, **kwargs):
    """
    Get normalized search parameters for Polish character fallback using database normalized columns.
    This replaces complex mapping logic with simple normalization for database search.

    Args:
        city (str, optional): City name
        street (str, optional): Street name
        province (str, optional): Province name
        county (str, optional): County name
        municipality (str, optional): Municipality name
        **kwargs: Other parameters (passed through unchanged)

    Returns:
        dict: Normalized parameter dictionary for searching normalized columns
    """
    normalized_params = kwargs.copy()

    # Normalize all text parameters to ASCII for searching normalized columns
    normalized_params['city'] = normalize_polish_text(city) if city else city
    normalized_params['street'] = normalize_polish_text(street) if street else street
    normalized_params['province'] = normalize_polish_text(province) if province else province
    normalized_params['county'] = normalize_polish_text(county) if county else county
    normalized_params['municipality'] = normalize_polish_text(municipality) if municipality else municipality

    return normalized_params


def has_polish_characters(text):
    """
    Check if text contains Polish diacritical characters.

    Args:
        text (str or None): Text to check

    Returns:
        bool: True if text contains Polish characters, False otherwise
    """
    if not text:
        return False

    polish_chars = {'ą', 'ć', 'ę', 'ł', 'ń', 'ó', 'ś', 'ź', 'ż',
                   'Ą', 'Ć', 'Ę', 'Ł', 'Ń', 'Ó', 'Ś', 'Ź', 'Ż'}

    return any(char in polish_chars for char in text)


