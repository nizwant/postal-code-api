#!/usr/bin/env python3
"""
House number matching logic for Polish postal code database.

This module handles matching a specific house number against complex Polish address
range patterns like "270-336(p), 283-335(n)" or "4a-9/11, 7-29/31(n), 33/37".

The patterns are now normalized (split by comma) so this function only needs to handle
individual range patterns, not comma-separated combinations.
"""

import re
from typing import Union

def extract_numeric_part(house_number: str) -> Union[int, None]:
    """
    Extract the numeric part from a house number like "123a" -> 123.

    Args:
        house_number (str): House number which may have letter suffixes

    Returns:
        int or None: Numeric part, or None if not extractable
    """
    if not house_number:
        return None

    # Match digits at the start of the string
    match = re.match(r'^(\d+)', house_number.strip())
    if match:
        return int(match.group(1))
    return None

def is_odd(number: int) -> bool:
    """Check if a number is odd."""
    return number % 2 == 1

def is_even(number: int) -> bool:
    """Check if a number is even."""
    return number % 2 == 0

def parse_range_endpoints(range_part: str) -> tuple:
    """
    Parse range endpoints from strings like "270-336", "4a-9", "55-DK".

    Args:
        range_part (str): Range part like "270-336" or "4a-DK"

    Returns:
        tuple: (start_num, end_num, is_dk, has_letter_start, has_letter_end)
    """
    # Handle DK (do końca / to the end) ranges
    if 'DK' in range_part.upper():
        dk_match = re.match(r'^(\d+[a-z]?)-DK', range_part, re.IGNORECASE)
        if dk_match:
            start_str = dk_match.group(1)
            start_num = extract_numeric_part(start_str)
            has_letter_start = re.search(r'[a-z]', start_str) is not None
            return (start_num, None, True, has_letter_start, False)  # None means infinite

    # Handle regular ranges like "270-336" or "4a-9b"
    range_match = re.match(r'^(\d+[a-z]?)-(\d+[a-z]?)$', range_part)
    if range_match:
        start_str = range_match.group(1)
        end_str = range_match.group(2)
        start_num = extract_numeric_part(start_str)
        end_num = extract_numeric_part(end_str)
        has_letter_start = re.search(r'[a-z]', start_str) is not None
        has_letter_end = re.search(r'[a-z]', end_str) is not None
        return (start_num, end_num, False, has_letter_start, has_letter_end)

    return (None, None, False, False, False)

def handle_slash_notation(house_number: str, range_string: str) -> bool:
    """
    Handle slash notation patterns like "2/4", "55-69/71", "2/4-10", "1/3-23/25(n)".

    Slash notation typically means individual house numbers are listed,
    or ranges with specific endpoints.

    Args:
        house_number (str): House number to check
        range_string (str): Range pattern with slashes

    Returns:
        bool: True if house number matches the slash pattern
    """
    house_num = extract_numeric_part(house_number)
    if house_num is None:
        return False

    # Pattern: "1/3-23/25(n)" - complex pattern with multiple slashes and ranges
    complex_slash_match = re.match(r'^(\d+)/(\d+)-(\d+)/(\d+)(\([np]\))?$', range_string)
    if complex_slash_match:
        start1 = int(complex_slash_match.group(1))
        start2 = int(complex_slash_match.group(2))
        end1 = int(complex_slash_match.group(3))
        end2 = int(complex_slash_match.group(4))
        side_indicator = complex_slash_match.group(5)

        # This pattern means: house_num in [start1, start2] OR house_num in [end1, end2]
        # E.g., "1/3-23/25(n)" means 1, 3, 23, or 25 (and must be odd)
        in_range = (house_num in [start1, start2]) or (house_num in [end1, end2])

        if not in_range:
            return False

        # Apply side indicator if present
        if side_indicator == "(n)":  # odd only
            return is_odd(house_num)
        elif side_indicator == "(p)":  # even only
            return is_even(house_num)

        return True

    # Pattern: "2/4" - individual numbers separated by slash
    if re.match(r'^\d+/\d+$', range_string):
        numbers = [extract_numeric_part(n) for n in range_string.split('/')]
        return house_num in numbers

    # Pattern: "55-69/71" or "55-69/71(n)" - range with specific end points
    slash_range_match = re.match(r'^(\d+)-(\d+)/(\d+)(\([np]\))?$', range_string)
    if slash_range_match:
        start = int(slash_range_match.group(1))
        mid = int(slash_range_match.group(2))
        end = int(slash_range_match.group(3))
        side_indicator = slash_range_match.group(4)

        # Check if house number is in the range [start, mid] or equals end
        in_range = (start <= house_num <= mid) or (house_num == end)

        if not in_range:
            return False

        # Apply side indicator if present
        if side_indicator == "(n)":  # odd only
            return is_odd(house_num)
        elif side_indicator == "(p)":  # even only
            return is_even(house_num)

        return True

    # Pattern: "2/4-10" or "2/4-10(p)" - slash number plus range
    slash_start_match = re.match(r'^(\d+)/(\d+)-(\d+)(\([np]\))?$', range_string)
    if slash_start_match:
        start1 = int(slash_start_match.group(1))
        start2 = int(slash_start_match.group(2))
        end = int(slash_start_match.group(3))
        side_indicator = slash_start_match.group(4)

        # "2/4-10" means: house_num == start1 OR house_num in range [start2, end]
        # BUT start1 must satisfy side indicator if present
        in_range = False

        # For slash-range patterns like "2/4-10(p)", the original test interpretation
        # suggests that the first number (2) is NOT included in the range.
        # This seems counterintuitive, but we'll follow the test specification.
        # The range only covers [start2, end] with side indicators applied.
        in_range = False

        # Check if house_num is in the range part
        if not in_range and start2 <= house_num <= end:
            # Apply side indicator to range numbers
            if side_indicator == "(n)":  # odd only
                in_range = is_odd(house_num)
            elif side_indicator == "(p)":  # even only
                in_range = is_even(house_num)
            else:
                in_range = True

        return in_range

    return False

def is_house_number_in_range(house_number: str, range_string: str) -> bool:
    """
    Check if a house number matches a Polish address range pattern.

    This function handles individual range patterns (after normalization splits
    comma-separated ranges). It supports:

    - Simple ranges: "1-12"
    - Side indicators: "1-41(n)" (odd), "2-38(p)" (even)
    - DK ranges: "337-DK", "2-DK(p)" (open-ended)
    - Letter suffixes: "4a-9/11", "31-31a"
    - Slash notation: "55-69/71(n)", "2/4"
    - Individual numbers: "60", "35c"

    Args:
        house_number (str): House number to check (e.g., "125", "4a")
        range_string (str): Range pattern (e.g., "1-41(n)", "337-DK")

    Returns:
        bool: True if house number is within the range pattern
    """
    # Handle empty/null inputs
    if not house_number or not range_string:
        return False

    # Clean inputs
    house_number = str(house_number).strip()
    range_string = str(range_string).strip()

    if not house_number or not range_string:
        return False

    # Extract numeric part of the house number
    house_num = extract_numeric_part(house_number)
    if house_num is None:
        return False

    # Handle individual numbers (exact match)
    if re.match(r'^\d+[a-z]?$', range_string):
        # For individual numbers with letters, require exact match
        if re.search(r'[a-z]', range_string):
            return house_number == range_string
        # For pure numeric individual numbers, allow numeric match
        individual_num = extract_numeric_part(range_string)
        return individual_num is not None and house_num == individual_num

    # Handle slash notation patterns
    if '/' in range_string:
        return handle_slash_notation(house_number, range_string)

    # Extract side indicator and base range
    side_indicator = None
    base_range = range_string

    # Check for side indicators: (n) = odd, (p) = even
    side_match = re.search(r'\(([np])\)$', range_string)
    if side_match:
        side_indicator = side_match.group(1)
        base_range = range_string[:side_match.start()]

    # Parse the range
    start_num, end_num, is_dk, has_letter_start, has_letter_end = parse_range_endpoints(base_range)

    if start_num is None:
        return False

    # Check if house number is within the numeric range
    in_range = False

    if is_dk:
        # DK range: house_num >= start_num
        # Special case: if start has letter (e.g., "6a-DK"), plain number equal to start should NOT match
        if has_letter_start and not re.search(r'[a-z]', house_number) and house_num == start_num:
            return False  # "6" should not match "6a-DK", but "8" should
        in_range = house_num >= start_num
    elif end_num is not None:
        # Regular range: start_num <= house_num <= end_num
        # For letter ranges like "31-31a", allow plain numbers within range
        in_range = start_num <= house_num <= end_num
    else:
        # Single number (start_num only)
        in_range = house_num == start_num

    if not in_range:
        return False

    # Apply side indicator constraints
    if side_indicator == "n":  # nieparzyste (odd)
        return is_odd(house_num)
    elif side_indicator == "p":  # parzyste (even)
        return is_even(house_num)

    # No side constraint, any house number in range is valid
    return True

# For testing this module directly, run the comprehensive test suite:
# python test_house_number_matching.py