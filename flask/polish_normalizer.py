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


def get_alternative_search_params(city=None, street=None, province=None, county=None, municipality=None, **kwargs):
    """
    Get alternative search parameters for Polish character fallback.
    This handles both directions: Polish→ASCII and ASCII→Polish variants.

    Args:
        city (str, optional): City name
        street (str, optional): Street name
        province (str, optional): Province name
        county (str, optional): County name
        municipality (str, optional): Municipality name
        **kwargs: Other parameters (passed through unchanged)

    Returns:
        list: List of alternative parameter dictionaries to try
    """
    alternatives = []
    base_params = kwargs.copy()

    # Strategy 1: Normalize Polish → ASCII (for users typing with Polish characters)
    normalized_params = base_params.copy()
    changed = False

    if city and has_polish_characters(city):
        normalized_params['city'] = normalize_polish_text(city)
        changed = True
    else:
        normalized_params['city'] = city

    if street and has_polish_characters(street):
        normalized_params['street'] = normalize_polish_text(street)
        changed = True
    else:
        normalized_params['street'] = street

    if province and has_polish_characters(province):
        normalized_params['province'] = normalize_polish_text(province)
        changed = True
    else:
        normalized_params['province'] = province

    if county and has_polish_characters(county):
        normalized_params['county'] = normalize_polish_text(county)
        changed = True
    else:
        normalized_params['county'] = county

    if municipality and has_polish_characters(municipality):
        normalized_params['municipality'] = normalize_polish_text(municipality)
        changed = True
    else:
        normalized_params['municipality'] = municipality

    if changed:
        alternatives.append(normalized_params)

    # Strategy 2: Try common Polish character variants (for ASCII inputs that might match Polish cities)
    # This is the key addition to handle "Lodz" → "Łódź" type searches
    polish_variants_params = base_params.copy()
    changed = False

    # Common ASCII → Polish mappings for major cities
    city_mappings = {
        'lodz': 'Łódź',
        'bialystok': 'Białystok',
        'krakow': 'Kraków',
        'gdansk': 'Gdańsk',
        'poznan': 'Poznań',
        'wroclaw': 'Wrocław'
    }

    if city and not has_polish_characters(city):
        city_lower = city.lower()
        if city_lower in city_mappings:
            polish_variants_params['city'] = city_mappings[city_lower]
            changed = True
        else:
            polish_variants_params['city'] = city
    else:
        polish_variants_params['city'] = city

    # For streets, we could add similar logic but it's more complex
    # For now, just pass through
    polish_variants_params['street'] = street
    polish_variants_params['province'] = province
    polish_variants_params['county'] = county
    polish_variants_params['municipality'] = municipality

    if changed:
        alternatives.append(polish_variants_params)

    return alternatives


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


def params_would_change_after_normalization(city=None, street=None, province=None, county=None, municipality=None):
    """
    Check if any of the search parameters would change after normalization.
    This helps avoid unnecessary normalized searches when input is already ASCII.

    Args:
        city (str, optional): City name
        street (str, optional): Street name
        province (str, optional): Province name
        county (str, optional): County name
        municipality (str, optional): Municipality name

    Returns:
        bool: True if normalization would change any parameter, False otherwise
    """
    params_to_check = [city, street, province, county, municipality]

    for param in params_to_check:
        if param and normalize_polish_text(param) != param:
            return True

    return False


def should_try_polish_search(city=None, street=None, province=None, county=None, municipality=None):
    """
    Check if we should try a Polish character search as fallback.
    This returns True for ASCII inputs that might match Polish character database entries.

    Args:
        city (str, optional): City name
        street (str, optional): Street name
        province (str, optional): Province name
        county (str, optional): County name
        municipality (str, optional): Municipality name

    Returns:
        bool: True if we should try Polish character search fallback
    """
    # Common ASCII inputs that often have Polish equivalents
    polish_city_mappings = {
        'lodz': 'Łódź',
        'bialystok': 'Białystok',
        'krakow': 'Kraków',
        'gdansk': 'Gdańsk',
        'poznan': 'Poznań',
        'wroclaw': 'Wrocław',
        'szczecin': 'Szczecin',
        'bydgoszcz': 'Bydgoszcz',
        'lublin': 'Lublin',
        'katowice': 'Katowice'
    }

    # Check if any parameter looks like it could have Polish character equivalents
    params_to_check = [
        (city, polish_city_mappings),
        (street, {}),  # Could expand this with street mappings
        (province, {}),
        (county, {}),
        (municipality, {})
    ]

    for param, mappings in params_to_check:
        if param:
            # Check direct mappings
            if param.lower() in mappings:
                return True
            # Check if contains characters that are commonly ASCII-fied Polish characters
            if any(char in param.lower() for char in ['a', 'c', 'e', 'l', 'n', 'o', 's', 'z']):
                # Only try if it's not already Polish characters
                if not has_polish_characters(param):
                    return True

    return False