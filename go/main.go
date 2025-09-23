package main

import (
	"fmt"
	"log"
	"net/http"
	"os"

	"postal-api/internal/database"
	"postal-api/internal/routes"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

func main() {
	// Check if database exists
	if !database.CheckDatabaseExists() {
		fmt.Println("Database file postal_codes.db not found. Please run create_db.py first.")
		os.Exit(1)
	}

	// Initialize database connection
	if err := database.Initialize(); err != nil {
		log.Fatalf("Failed to initialize database: %v", err)
	}
	defer database.Close()

	// Create Gin router with logging
	gin.SetMode(gin.DebugMode)
	router := gin.Default()

	// Configure CORS to allow requests from the frontend
	config := cors.DefaultConfig()
	config.AllowOrigins = []string{"http://localhost:3000"}
	config.AllowMethods = []string{"GET", "POST", "OPTIONS"}
	config.AllowHeaders = []string{"*"}
	router.Use(cors.New(config))

	// Add logging middleware for errors
	router.Use(gin.Logger(), gin.Recovery())

	// Register routes
	routes.RegisterRoutes(router)

	// Start server on port 5003
	fmt.Println("Starting postal code API server on :5003")
	if err := http.ListenAndServe(":5003", router); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}