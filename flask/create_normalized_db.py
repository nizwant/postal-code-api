#!/usr/bin/env python3
"""
Polish Postal Code Database Normalization Script

This script creates a normalized version of the postal codes database
by parsing complex house number ranges into individual, queryable records.

Instead of storing complex strings like:
  "270-336(p), 283-335(n)"
  "4a-9/11, 7-29/31(n), 33/37" 
  "1, 2-DK(p), 5-DK(n)"

We store individual range records that can be efficiently queried:
  - Simple indexed lookups instead of regex parsing
  - Support for odd/even filtering
  - Proper handling of Polish postal conventions
"""

import sqlite3
import re
import json
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass 
class HouseRange:
    """Represents a parsed house number range."""
    range_type: str          # 'simple', 'odd', 'even', 'dk', 'individual', 'complex'
    start_number: Optional[int]
    end_number: Optional[int] # None for DK ranges
    is_odd: Optional[bool]   # True for (n), False for (p), None for both
    is_even: Optional[bool]  # True for (p), False for (n), None for both  
    has_letters: bool        # Contains letters like 4a, 9/11
    original_text: str       # Original range text for reference
    special_cases: Dict      # {"4a": True, "9/11": True, etc.}


class HouseNumberParser:
    """Parser for Polish postal code house number ranges."""
    
    def __init__(self):
        # Regex patterns for different types of ranges
        self.patterns = {
            # Simple range: "1-12", "337-DK"
            'simple_range': re.compile(r'^(\d+(?:[a-z])?)-(\d+|DK)(?:\([np]\))?$', re.IGNORECASE),
            
            # Range with side indicator: "1-41(n)", "2-38(p)"  
            'range_with_side': re.compile(r'^(\d+(?:[a-z])?)-(\d+|DK)\(([np])\)$', re.IGNORECASE),
            
            # Individual number: "60", "4a"
            'individual': re.compile(r'^(\d+(?:[a-z])?)$'),
            
            # Slash notation: "5/7", "4a-9/11", "2/4-10(p)"
            'slash_range': re.compile(r'^(\d+(?:[a-z])?)/(\d+(?:[a-z])?)-?(\d+)?(?:\(([np])\))?$', re.IGNORECASE),
            
            # Letter suffixes: "31-31a", "87a-89(n)"
            'letter_range': re.compile(r'^(\d+[a-z]?)-(\d+[a-z]?)(?:\(([np])\))?$', re.IGNORECASE),
        }
    
    def parse_house_numbers(self, house_numbers_str: str) -> List[HouseRange]:
        """
        Parse a house_numbers string into a list of HouseRange objects.
        
        Examples:
          "1-12" → [HouseRange(simple, 1, 12, None, None, False, ...)]
          "270-336(p), 283-335(n)" → [HouseRange(...), HouseRange(...)]
          "4a-9/11, 7-29/31(n), 33/37" → [HouseRange(...), HouseRange(...), HouseRange(...)]
        """
        if not house_numbers_str or house_numbers_str.strip() == '':
            return []
        
        # Split by commas to handle multiple ranges
        parts = [part.strip() for part in house_numbers_str.split(',')]
        ranges = []
        
        for part in parts:
            if not part:
                continue
                
            parsed_ranges = self._parse_single_part(part)
            ranges.extend(parsed_ranges)
        
        return ranges
    
    def _parse_single_part(self, part: str) -> List[HouseRange]:
        """Parse a single part of the house numbers string."""
        part = part.strip()
        
        # Try different patterns in order of specificity
        
        # 1. Range with side indicator: "1-41(n)", "2-38(p)"
        match = self.patterns['range_with_side'].match(part)
        if match:
            start, end, side = match.groups()
            return [self._create_range_with_side(start, end, side, part)]
        
        # 2. Slash notation: "5/7", "4a-9/11", "2/4-10(p)"
        match = self.patterns['slash_range'].match(part)
        if match:
            return self._parse_slash_notation(match, part)
        
        # 3. Simple range: "1-12", "337-DK"
        match = self.patterns['simple_range'].match(part)
        if match:
            start, end = match.groups()
            return [self._create_simple_range(start, end, part)]
        
        # 4. Individual number: "60", "4a"
        match = self.patterns['individual'].match(part)
        if match:
            number = match.group(1)
            return [self._create_individual_number(number, part)]
        
        # 5. Complex cases - try to extract meaningful parts
        logger.warning(f"Complex/unrecognized pattern: '{part}'")
        return [self._create_complex_range(part)]
    
    def _create_range_with_side(self, start: str, end: str, side: str, original: str) -> HouseRange:
        """Create a range with odd/even side indicator."""
        start_num = self._extract_number(start)
        end_num = None if end.upper() == 'DK' else self._extract_number(end)
        
        is_odd = side.lower() == 'n'  # 'n' = nieparzyste (odd)
        is_even = side.lower() == 'p'  # 'p' = parzyste (even)
        has_letters = bool(re.search(r'[a-z]', original, re.IGNORECASE))
        
        range_type = 'dk' if end.upper() == 'DK' else ('odd' if is_odd else 'even')
        
        return HouseRange(
            range_type=range_type,
            start_number=start_num,
            end_number=end_num,
            is_odd=is_odd,
            is_even=is_even,
            has_letters=has_letters,
            original_text=original,
            special_cases=self._extract_special_cases(original)
        )
    
    def _create_simple_range(self, start: str, end: str, original: str) -> HouseRange:
        """Create a simple numeric range without side indicators."""
        start_num = self._extract_number(start)
        end_num = None if end.upper() == 'DK' else self._extract_number(end)
        has_letters = bool(re.search(r'[a-z]', original, re.IGNORECASE))
        
        range_type = 'dk' if end.upper() == 'DK' else 'simple'
        
        return HouseRange(
            range_type=range_type,
            start_number=start_num,
            end_number=end_num,
            is_odd=None,    # No side restriction
            is_even=None,   # No side restriction
            has_letters=has_letters,
            original_text=original,
            special_cases=self._extract_special_cases(original)
        )
    
    def _create_individual_number(self, number: str, original: str) -> HouseRange:
        """Create a range for an individual house number."""
        num = self._extract_number(number)
        has_letters = bool(re.search(r'[a-z]', number, re.IGNORECASE))
        
        return HouseRange(
            range_type='individual',
            start_number=num,
            end_number=num,
            is_odd=None,
            is_even=None,
            has_letters=has_letters,
            original_text=original,
            special_cases=self._extract_special_cases(original)
        )
    
    def _parse_slash_notation(self, match, original: str) -> List[HouseRange]:
        """Parse slash notation like '5/7', '2/4-10(p)'."""
        groups = match.groups()
        
        if len(groups) == 4 and groups[2]:  # Range format: "2/4-10(p)"
            start1, start2, end, side = groups
            # This represents a range from start2 to end
            start_num = self._extract_number(start2)
            end_num = self._extract_number(end)
            
            is_odd = side and side.lower() == 'n'
            is_even = side and side.lower() == 'p'
            
            return [HouseRange(
                range_type='even' if is_even else ('odd' if is_odd else 'simple'),
                start_number=start_num,
                end_number=end_num,
                is_odd=is_odd,
                is_even=is_even,
                has_letters=bool(re.search(r'[a-z]', original, re.IGNORECASE)),
                original_text=original,
                special_cases=self._extract_special_cases(original)
            )]
        else:  # Individual numbers: "5/7"
            start1, start2 = groups[0], groups[1]
            ranges = []
            
            # Create individual entries for each number
            for num_str in [start1, start2]:
                if num_str:
                    ranges.append(self._create_individual_number(num_str, original))
            
            return ranges
    
    def _create_complex_range(self, original: str) -> HouseRange:
        """Create a range for complex patterns that don't match standard patterns."""
        # Try to extract at least some numbers for basic matching
        numbers = re.findall(r'\d+', original)
        start_num = int(numbers[0]) if numbers else None
        
        return HouseRange(
            range_type='complex',
            start_number=start_num,
            end_number=None,
            is_odd=None,
            is_even=None,
            has_letters=bool(re.search(r'[a-z]', original, re.IGNORECASE)),
            original_text=original,
            special_cases=self._extract_special_cases(original)
        )
    
    def _extract_number(self, num_str: str) -> Optional[int]:
        """Extract numeric part from a string like '4a' → 4."""
        if not num_str:
            return None
        match = re.search(r'\d+', num_str)
        return int(match.group()) if match else None
    
    def _extract_special_cases(self, original: str) -> Dict:
        """Extract special cases like letter suffixes, slash notation, etc."""
        special = {}
        
        # Find letter suffixes: "4a", "31a"
        letter_matches = re.findall(r'\d+[a-z]+', original, re.IGNORECASE)
        for match in letter_matches:
            special[match] = True
        
        # Find slash notation: "9/11", "2/4"  
        slash_matches = re.findall(r'\d+/\d+', original)
        for match in slash_matches:
            special[match] = True
        
        return special


class DatabaseMigrator:
    """Handles the migration from old to normalized database structure."""
    
    def __init__(self, source_db_path: str, target_db_path: str):
        self.source_db_path = source_db_path
        self.target_db_path = target_db_path
        self.parser = HouseNumberParser()
    
    def migrate(self):
        """Perform the full migration."""
        logger.info("Starting database migration...")
        
        # Create new database structure
        self._create_normalized_schema()
        
        # Migrate data
        self._migrate_data()
        
        # Create indexes
        self._create_indexes()
        
        # Validate migration
        self._validate_migration()
        
        logger.info("Migration completed successfully!")
    
    def _create_normalized_schema(self):
        """Create the new normalized database schema."""
        logger.info("Creating normalized database schema...")
        
        with sqlite3.connect(self.target_db_path) as conn:
            cursor = conn.cursor()
            
            # Main postal codes table (unchanged for compatibility)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS postal_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    postal_code TEXT NOT NULL,
                    city TEXT,
                    street TEXT,
                    house_numbers TEXT,
                    municipality TEXT,
                    county TEXT,
                    province TEXT
                )
            ''')
            
            # New normalized house ranges table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS house_ranges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    postal_code TEXT NOT NULL,
                    city TEXT,
                    street TEXT,
                    municipality TEXT,
                    county TEXT,
                    province TEXT,
                    
                    -- Parsed range information
                    range_type TEXT NOT NULL,           -- 'simple', 'odd', 'even', 'dk', 'individual', 'complex'
                    start_number INTEGER,
                    end_number INTEGER,                 -- NULL for DK ranges
                    is_odd BOOLEAN,                     -- TRUE for odd-only ranges
                    is_even BOOLEAN,                    -- TRUE for even-only ranges
                    has_letters BOOLEAN DEFAULT FALSE,
                    
                    -- Metadata
                    original_range_text TEXT,
                    special_cases TEXT,                 -- JSON string of special cases
                    created_from_id INTEGER,            -- Reference to original postal_codes record
                    
                    FOREIGN KEY (created_from_id) REFERENCES postal_codes (id)
                )
            ''')
            
            # Statistics table for monitoring
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS migration_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    original_records INTEGER,
                    normalized_records INTEGER,
                    parsing_errors INTEGER,
                    complex_patterns INTEGER
                )
            ''')
            
            conn.commit()
        
        logger.info("Schema created successfully")
    
    def _migrate_data(self):
        """Migrate data from source to normalized target database."""
        logger.info("Starting data migration...")
        
        stats = {
            'original_records': 0,
            'normalized_records': 0,
            'parsing_errors': 0,
            'complex_patterns': 0
        }
        
        with sqlite3.connect(self.source_db_path) as source_conn:
            with sqlite3.connect(self.target_db_path) as target_conn:
                source_cursor = source_conn.cursor()
                target_cursor = target_conn.cursor()
                
                # Copy original postal_codes table as-is
                logger.info("Copying original postal_codes table...")
                source_cursor.execute("SELECT * FROM postal_codes")
                
                for row in source_cursor.fetchall():
                    target_cursor.execute('''
                        INSERT INTO postal_codes 
                        (id, postal_code, city, street, house_numbers, municipality, county, province)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', row)
                    stats['original_records'] += 1
                
                # Process and normalize house ranges
                logger.info("Parsing and normalizing house ranges...")
                source_cursor.execute("SELECT * FROM postal_codes")
                
                batch_size = 1000
                batch_count = 0
                
                for row in source_cursor.fetchall():
                    original_id, postal_code, city, street, house_numbers, municipality, county, province = row
                    
                    try:
                        # Parse house numbers into ranges
                        ranges = self.parser.parse_house_numbers(house_numbers)
                        
                        # Insert each range as a separate record
                        for range_obj in ranges:
                            target_cursor.execute('''
                                INSERT INTO house_ranges 
                                (postal_code, city, street, municipality, county, province,
                                 range_type, start_number, end_number, is_odd, is_even, has_letters,
                                 original_range_text, special_cases, created_from_id)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                postal_code, city, street, municipality, county, province,
                                range_obj.range_type, range_obj.start_number, range_obj.end_number,
                                range_obj.is_odd, range_obj.is_even, range_obj.has_letters,
                                range_obj.original_text, json.dumps(range_obj.special_cases),
                                original_id
                            ))
                            stats['normalized_records'] += 1
                            
                            if range_obj.range_type == 'complex':
                                stats['complex_patterns'] += 1
                    
                    except Exception as e:
                        logger.error(f"Error processing record {original_id}: {e}")
                        logger.error(f"House numbers: '{house_numbers}'")
                        stats['parsing_errors'] += 1
                    
                    batch_count += 1
                    if batch_count % batch_size == 0:
                        target_conn.commit()
                        logger.info(f"Processed {batch_count} records...")
                
                target_conn.commit()
                
                # Record migration statistics
                target_cursor.execute('''
                    INSERT INTO migration_stats 
                    (original_records, normalized_records, parsing_errors, complex_patterns)
                    VALUES (?, ?, ?, ?)
                ''', (stats['original_records'], stats['normalized_records'], 
                      stats['parsing_errors'], stats['complex_patterns']))
                
                target_conn.commit()
        
        logger.info(f"Data migration completed:")
        logger.info(f"  Original records: {stats['original_records']}")
        logger.info(f"  Normalized records: {stats['normalized_records']}")
        logger.info(f"  Parsing errors: {stats['parsing_errors']}")
        logger.info(f"  Complex patterns: {stats['complex_patterns']}")
    
    def _create_indexes(self):
        """Create indexes for optimal query performance."""
        logger.info("Creating database indexes...")
        
        with sqlite3.connect(self.target_db_path) as conn:
            cursor = conn.cursor()
            
            # Original table indexes (for compatibility)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_postal_code ON postal_codes(postal_code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_city ON postal_codes(LOWER(city))")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_street ON postal_codes(LOWER(street))")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_province ON postal_codes(LOWER(province))")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_county ON postal_codes(LOWER(county))")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_municipality ON postal_codes(LOWER(municipality))")
            
            # New table indexes for fast house number lookups
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hr_lookup ON house_ranges(LOWER(city), LOWER(street))")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hr_range ON house_ranges(start_number, end_number)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hr_sides ON house_ranges(is_odd, is_even)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hr_postal ON house_ranges(postal_code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hr_type ON house_ranges(range_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hr_composite ON house_ranges(LOWER(city), LOWER(street), start_number, end_number, is_odd, is_even)")
            
            conn.commit()
        
        logger.info("Indexes created successfully")
    
    def _validate_migration(self):
        """Validate the migration by running some test queries."""
        logger.info("Validating migration...")
        
        with sqlite3.connect(self.target_db_path) as conn:
            cursor = conn.cursor()
            
            # Basic counts
            cursor.execute("SELECT COUNT(*) FROM postal_codes")
            original_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM house_ranges")
            normalized_count = cursor.fetchone()[0]
            
            # Test specific patterns
            cursor.execute("SELECT COUNT(*) FROM house_ranges WHERE range_type = 'dk'")
            dk_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM house_ranges WHERE is_odd = 1")
            odd_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM house_ranges WHERE is_even = 1") 
            even_count = cursor.fetchone()[0]
            
            logger.info(f"Validation results:")
            logger.info(f"  Original records: {original_count}")
            logger.info(f"  Normalized records: {normalized_count}")
            logger.info(f"  DK ranges: {dk_count}")
            logger.info(f"  Odd-only ranges: {odd_count}")
            logger.info(f"  Even-only ranges: {even_count}")
            
            # Test the original problematic case
            cursor.execute('''
                SELECT * FROM house_ranges 
                WHERE LOWER(city) LIKE LOWER('Wrocław%') 
                  AND LOWER(street) = LOWER('Jarocińska')
                  AND start_number <= 2 
                  AND (end_number >= 2 OR end_number IS NULL)
                  AND (is_odd IS NULL OR is_even IS NULL OR is_even = 1)
            ''')
            
            test_results = cursor.fetchall()
            logger.info(f"  Test query (house number 2 in Jarocińska): {len(test_results)} results")
            
            if test_results:
                logger.info(f"  Expected postal code: {test_results[0][1]}")  # postal_code column


def main():
    """Main migration function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate postal codes database to normalized structure')
    parser.add_argument('--source', default='postal_codes.db', help='Source database path')
    parser.add_argument('--target', default='postal_codes_normalized.db', help='Target database path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    migrator = DatabaseMigrator(args.source, args.target)
    migrator.migrate()


if __name__ == '__main__':
    main()