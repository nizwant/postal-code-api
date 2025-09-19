package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

func main() {
	baseURL := "http://localhost:5003"

	// Wait a moment for server to start
	fmt.Println("Testing Go postal code API...")
	time.Sleep(2 * time.Second)

	// Test health endpoint
	fmt.Println("\n1. Testing health endpoint...")
	resp, err := http.Get(baseURL + "/health")
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	fmt.Printf("Status: %d\n", resp.StatusCode)
	fmt.Printf("Response: %s\n", string(body))

	// Test postal code search
	fmt.Println("\n2. Testing postal code search...")
	resp, err = http.Get(baseURL + "/postal-codes?city=Warszawa&limit=3")
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}
	defer resp.Body.Close()

	body, _ = io.ReadAll(resp.Body)
	fmt.Printf("Status: %d\n", resp.StatusCode)

	var result map[string]interface{}
	json.Unmarshal(body, &result)
	if count, ok := result["count"]; ok {
		fmt.Printf("Found %v results\n", count)
	}

	// Test provinces endpoint
	fmt.Println("\n3. Testing provinces endpoint...")
	resp, err = http.Get(baseURL + "/locations/provinces")
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}
	defer resp.Body.Close()

	body, _ = io.ReadAll(resp.Body)
	fmt.Printf("Status: %d\n", resp.StatusCode)

	json.Unmarshal(body, &result)
	if count, ok := result["count"]; ok {
		fmt.Printf("Found %v provinces\n", count)
	}

	fmt.Println("\nGo API tests completed!")
}