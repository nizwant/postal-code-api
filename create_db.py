#!/usr/bin/env python3
"""
Create a normalized postal codes database by splitting comma-separated house number ranges
into individual records. This makes house number matching much more efficient and accurate.
"""

import sqlite3
import pandas as pd
import os
import re


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


def split_house_number_ranges(house_numbers_str):
    """
    Split comma-separated house number ranges into individual range parts.

    Args:
        house_numbers_str (str): Original comma-separated ranges like "270-336(p), 283-335(n)"

    Returns:
        list: Individual range parts like ["270-336(p)", "283-335(n)"]
    """
    if not house_numbers_str or pd.isna(house_numbers_str):
        return []

    # Split by comma and clean up whitespace
    parts = [part.strip() for part in house_numbers_str.split(",")]

    # Filter out empty parts
    parts = [part for part in parts if part]

    return parts


def validate_split_pattern(pattern):
    """
    Validate that a split pattern looks reasonable.
    This helps catch any edge cases we might have missed.

    Args:
        pattern (str): Individual range pattern

    Returns:
        bool: True if pattern looks valid, False otherwise
    """
    if not pattern:
        return False

    # Check for basic valid patterns based on our analysis:
    valid_patterns = [
        r"^\d+$",  # Individual number: "60"
        r"^\d+[a-z]?$",  # Individual with letter: "35c"
        r"^\d+-\d+$",  # Simple range: "1-12"
        r"^\d+-\d+\([np]\)$",  # Side indicator: "1-41(n)"
        r"^\d+-DK$",  # DK range: "337-DK"
        r"^\d+-DK\([np]\)$",  # DK with side: "2-DK(p)"
        r"^\d+[a-z]?-\d+[a-z]?$",  # Letter suffix: "4a-9b"
        r"^\d+[a-z]?-\d+[a-z]?\([np]\)$",  # Letter with side: "87a-89(n)"
        r"^\d+/\d+$",  # Slash notation: "2/4"
        r"^\d+-\d+/\d+$",  # Slash range: "55-69/71"
        r"^\d+-\d+/\d+\([np]\)$",  # Slash with side: "55-69/71(n)"
        r"^\d+/\d+-\d+$",  # Slash start: "2/4-10"
        r"^\d+/\d+-\d+\([np]\)$",  # Slash start with side: "2/4-10(p)"
        r"^\d+[a-z]?-\d+[a-z]?/\d+[a-z]?$",  # Complex letter/slash: "4a-9/11"
        r"^\d+-\d+-\d+$",  # Triple range (edge case): "38-40-42"
    ]

    for pattern_regex in valid_patterns:
        if re.match(pattern_regex, pattern):
            return True

    # Log suspicious patterns for review
    print(f"Warning: Suspicious pattern detected: '{pattern}'")
    return True  # Accept it anyway, but warn


def create_normalized_database():
    """Create the normalized postal codes database."""

    # Read CSV file
    csv_path = "postal_codes_poland.csv"
    print(f"Reading CSV file: {csv_path}")
    df = pd.read_csv(csv_path)

    print(f"Original records: {len(df)}")

    # Create SQLite database
    db_path = "postal_codes.db"

    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table with normalized columns added
    cursor.execute(
        """
        CREATE TABLE postal_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            postal_code TEXT NOT NULL,
            city TEXT,
            street TEXT,
            house_numbers TEXT,
            municipality TEXT,
            county TEXT,
            province TEXT,
            city_normalized TEXT,
            street_normalized TEXT
        )
    """
    )

    # Create indexes for better performance
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_postal_code ON postal_codes(postal_code)"
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_city ON postal_codes(city COLLATE NOCASE)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_street ON postal_codes(street COLLATE NOCASE)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_province ON postal_codes(province COLLATE NOCASE)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_county ON postal_codes(county COLLATE NOCASE)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_municipality ON postal_codes(municipality COLLATE NOCASE)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_house_numbers ON postal_codes(house_numbers)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_city_normalized ON postal_codes(city_normalized COLLATE NOCASE)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_street_normalized ON postal_codes(street_normalized COLLATE NOCASE)"
    )

    # Counters for tracking
    original_with_house_numbers = 0
    total_normalized_records = 0
    records_without_house_numbers = 0
    comma_separated_records = 0
    total_splits = 0
    suspicious_patterns = []

    # Process each record
    for _, row in df.iterrows():
        base_record = {
            "postal_code": row["PNA"],
            "city": row["Miejscowość"],
            "street": row["Ulica"] if pd.notna(row["Ulica"]) else None,
            "municipality": row["Gmina"],
            "county": row["Powiat"],
            "province": row["Województwo"],
        }

        # Handle house numbers
        house_numbers = row["Numery"] if pd.notna(row["Numery"]) else None

        if not house_numbers:
            # No house numbers - insert as single record with NULL house_numbers
            cursor.execute(
                """
                INSERT INTO postal_codes
                (postal_code, city, street, house_numbers, municipality, county, province, city_normalized, street_normalized)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    base_record["postal_code"],
                    base_record["city"],
                    base_record["street"],
                    None,  # house_numbers = NULL
                    base_record["municipality"],
                    base_record["county"],
                    base_record["province"],
                    normalize_polish_text(base_record["city"]),
                    normalize_polish_text(base_record["street"]),
                ),
            )
            records_without_house_numbers += 1
            total_normalized_records += 1
        else:
            # Has house numbers - split and create multiple records
            original_with_house_numbers += 1

            # Split the house number ranges
            house_number_parts = split_house_number_ranges(house_numbers)

            if len(house_number_parts) > 1:
                comma_separated_records += 1
                total_splits += len(house_number_parts)

            # Create a record for each house number part
            for part in house_number_parts:
                if validate_split_pattern(part):
                    cursor.execute(
                        """
                        INSERT INTO postal_codes
                        (postal_code, city, street, house_numbers, municipality, county, province, city_normalized, street_normalized)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            base_record["postal_code"],
                            base_record["city"],
                            base_record["street"],
                            part,  # Individual house number range
                            base_record["municipality"],
                            base_record["county"],
                            base_record["province"],
                            normalize_polish_text(base_record["city"]),
                            normalize_polish_text(base_record["street"]),
                        ),
                    )
                    total_normalized_records += 1
                else:
                    suspicious_patterns.append(part)

    # Commit changes
    conn.commit()

    # Get final statistics
    final_count = cursor.execute("SELECT COUNT(*) FROM postal_codes").fetchone()[0]
    house_number_count = cursor.execute(
        "SELECT COUNT(*) FROM postal_codes WHERE house_numbers IS NOT NULL"
    ).fetchone()[0]

    conn.close()

    # Print summary
    print("\n" + "=" * 60)
    print("NORMALIZATION COMPLETE")
    print("=" * 60)
    print(f"Original total records:           {len(df):,}")
    print(f"Original with house numbers:      {original_with_house_numbers:,}")
    print(f"Original without house numbers:   {records_without_house_numbers:,}")
    print(f"Comma-separated records split:    {comma_separated_records:,}")
    print(f"Total individual ranges created:  {total_splits:,}")
    print()
    print(f"Final database records:           {final_count:,}")
    print(f"Records with house numbers:       {house_number_count:,}")
    print(f"Records without house numbers:    {records_without_house_numbers:,}")
    print(f"Expansion factor:                 {final_count / len(df):.2f}x")
    print()
    print(f"Database file: {os.path.abspath(db_path)}")

    if suspicious_patterns:
        print(f"\nWarning: {len(suspicious_patterns)} suspicious patterns detected:")
        for pattern in suspicious_patterns[:10]:  # Show first 10
            print(f"  - {pattern}")
        if len(suspicious_patterns) > 10:
            print(f"  ... and {len(suspicious_patterns) - 10} more")

    return db_path


def verify_normalization(db_path):
    """Quick verification of the normalization process."""
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)

    conn = sqlite3.connect(db_path)

    # Check for any comma-separated entries that shouldn't exist
    remaining_commas = conn.execute(
        "SELECT COUNT(*) FROM postal_codes WHERE house_numbers LIKE '%,%'"
    ).fetchone()[0]

    if remaining_commas > 0:
        print(f"ERROR: {remaining_commas} records still have commas in house_numbers!")
        examples = conn.execute(
            "SELECT house_numbers FROM postal_codes WHERE house_numbers LIKE '%,%' LIMIT 5"
        ).fetchall()
        for example in examples:
            print(f"  - {example[0]}")
    else:
        print("✓ No comma-separated house numbers remain")

    # Sample some records for manual verification
    sample_records = conn.execute(
        """
        SELECT postal_code, city, street, house_numbers
        FROM postal_codes
        WHERE house_numbers IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 10
    """
    ).fetchall()

    print(f"\nSample normalized records:")
    for record in sample_records:
        postal_code, city, street, house_numbers = record
        street_info = f", {street}" if street else ""
        print(f"  {postal_code}: {city}{street_info} - {house_numbers}")

    conn.close()


if __name__ == "__main__":
    print("Creating normalized postal codes database...")
    db_path = create_normalized_database()
    verify_normalization(db_path)
    print("\nNormalization complete!")
