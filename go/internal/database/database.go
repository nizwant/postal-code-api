package database

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"

	_ "github.com/mattn/go-sqlite3"
)

var db *sql.DB

const dbPath = "../postal_codes.db"

// PostalCode represents a postal code record
type PostalCode struct {
	PostalCode   string  `json:"postal_code" db:"postal_code"`
	City         string  `json:"city" db:"city"`
	Street       *string `json:"street,omitempty" db:"street"`
	HouseNumbers *string `json:"house_numbers,omitempty" db:"house_numbers"`
	Municipality *string `json:"municipality,omitempty" db:"municipality"`
	County       *string `json:"county,omitempty" db:"county"`
	Province     string  `json:"province" db:"province"`
}

// CheckDatabaseExists checks if the database file exists
func CheckDatabaseExists() bool {
	_, err := os.Stat(dbPath)
	return err == nil
}

// Initialize initializes the database connection
func Initialize() error {
	absPath, err := filepath.Abs(dbPath)
	if err != nil {
		return fmt.Errorf("failed to get absolute path: %w", err)
	}

	database, err := sql.Open("sqlite3", absPath)
	if err != nil {
		return fmt.Errorf("failed to open database: %w", err)
	}

	// Test the connection
	if err := database.Ping(); err != nil {
		return fmt.Errorf("failed to ping database: %w", err)
	}

	db = database
	return nil
}

// GetDB returns the database connection
func GetDB() *sql.DB {
	return db
}

// Close closes the database connection
func Close() error {
	if db != nil {
		return db.Close()
	}
	return nil
}