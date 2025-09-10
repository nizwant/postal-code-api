import sqlite3
import pandas as pd
import os

def create_database():
    # Read CSV file
    csv_path = '../postal_codes_poland.csv'
    df = pd.read_csv(csv_path)
    
    # Create SQLite database
    db_path = 'postal_codes.db'
    conn = sqlite3.connect(db_path)
    
    # Create table with proper column names
    cursor = conn.cursor()
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
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_postal_code ON postal_codes(postal_code)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_city ON postal_codes(LOWER(city))')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_street ON postal_codes(LOWER(street))')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_province ON postal_codes(LOWER(province))')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_county ON postal_codes(LOWER(county))')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_municipality ON postal_codes(LOWER(municipality))')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_house_numbers ON postal_codes(house_numbers)')
    
    # Insert data
    for _, row in df.iterrows():
        cursor.execute('''
            INSERT INTO postal_codes 
            (postal_code, city, street, house_numbers, municipality, county, province)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            row['PNA'],
            row['Miejscowość'],
            row['Ulica'] if pd.notna(row['Ulica']) else None,
            row['Numery'] if pd.notna(row['Numery']) else None,
            row['Gmina'],
            row['Powiat'],
            row['Województwo']
        ))
    
    conn.commit()
    conn.close()
    
    print(f"Database created successfully with {len(df)} records")
    print(f"Database file: {os.path.abspath(db_path)}")

if __name__ == '__main__':
    create_database()