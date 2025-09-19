package routes

import (
	"fmt"
	"net/http"
	"strconv"
	"strings"

	"postal-api/internal/services"
	"postal-api/internal/utils"

	"github.com/gin-gonic/gin"
)

// trimParam trims whitespace from parameter value if it exists
func trimParam(value string) string {
	return strings.TrimSpace(value)
}

// stringPtr returns a pointer to the string if it's not empty, otherwise nil
func stringPtr(s string) *string {
	if s == "" {
		return nil
	}
	return &s
}

// RegisterRoutes registers all routes with the Gin router
func RegisterRoutes(router *gin.Engine) {
	// Postal codes search endpoint
	router.GET("/postal-codes", searchPostalCodesHandler)

	// Direct postal code lookup
	router.GET("/postal-codes/:postal_code", getPostalCodeHandler)

	// Location endpoints directory
	router.GET("/locations", getLocationsHandler)

	// Location hierarchy endpoints
	router.GET("/locations/provinces", getProvincesHandler)
	router.GET("/locations/counties", getCountiesHandler)
	router.GET("/locations/municipalities", getMunicipalitiesHandler)
	router.GET("/locations/cities", getCitiesHandler)
	router.GET("/locations/streets", getStreetsHandler)

	// Health check endpoint
	router.GET("/health", healthCheckHandler)
}

// searchPostalCodesHandler handles the postal codes search endpoint
func searchPostalCodesHandler(c *gin.Context) {
	// Get query parameters and trim whitespace
	city := trimParam(c.Query("city"))
	street := trimParam(c.Query("street"))
	houseNumber := trimParam(c.Query("house_number"))
	province := trimParam(c.Query("province"))
	county := trimParam(c.Query("county"))
	municipality := trimParam(c.Query("municipality"))
	limitStr := c.DefaultQuery("limit", "100")

	// City parameter is mandatory
	if city == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "City parameter is required"})
		return
	}

	// Parse limit
	limit, err := strconv.Atoi(limitStr)
	if err != nil || limit < 1 {
		limit = 100
	}

	// Create search parameters
	params := utils.SearchParams{
		City:         stringPtr(city),
		Street:       stringPtr(street),
		HouseNumber:  stringPtr(houseNumber),
		Province:     stringPtr(province),
		County:       stringPtr(county),
		Municipality: stringPtr(municipality),
		Limit:        limit,
	}

	// Execute search
	response, err := services.SearchPostalCodes(params)
	if err != nil {
		// Log the actual error for debugging
		fmt.Printf("Search error: %v\n", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Internal server error: %v", err)})
		return
	}

	c.JSON(http.StatusOK, response)
}

// getPostalCodeHandler handles direct postal code lookup
func getPostalCodeHandler(c *gin.Context) {
	postalCode := c.Param("postal_code")
	if postalCode == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Postal code parameter is required"})
		return
	}

	result, err := services.GetPostalCodeByCode(postalCode)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	if result == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Postal code not found"})
		return
	}

	c.JSON(http.StatusOK, result)
}

// getLocationsHandler returns available location endpoints
func getLocationsHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"available_endpoints": gin.H{
			"provinces":      "/locations/provinces",
			"counties":       "/locations/counties",
			"municipalities": "/locations/municipalities",
			"cities":         "/locations/cities",
			"streets":        "/locations/streets",
		},
	})
}

// getProvincesHandler handles provinces endpoint
func getProvincesHandler(c *gin.Context) {
	prefix := trimParam(c.Query("prefix"))

	response, err := services.GetProvinces(stringPtr(prefix))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	c.JSON(http.StatusOK, response)
}

// getCountiesHandler handles counties endpoint
func getCountiesHandler(c *gin.Context) {
	province := trimParam(c.Query("province"))
	prefix := trimParam(c.Query("prefix"))

	response, err := services.GetCounties(stringPtr(province), stringPtr(prefix))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	c.JSON(http.StatusOK, response)
}

// getMunicipalitiesHandler handles municipalities endpoint
func getMunicipalitiesHandler(c *gin.Context) {
	province := trimParam(c.Query("province"))
	county := trimParam(c.Query("county"))
	prefix := trimParam(c.Query("prefix"))

	response, err := services.GetMunicipalities(stringPtr(province), stringPtr(county), stringPtr(prefix))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	c.JSON(http.StatusOK, response)
}

// getCitiesHandler handles cities endpoint
func getCitiesHandler(c *gin.Context) {
	province := trimParam(c.Query("province"))
	county := trimParam(c.Query("county"))
	municipality := trimParam(c.Query("municipality"))
	prefix := trimParam(c.Query("prefix"))

	response, err := services.GetCities(stringPtr(province), stringPtr(county), stringPtr(municipality), stringPtr(prefix))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	c.JSON(http.StatusOK, response)
}

// getStreetsHandler handles streets endpoint
func getStreetsHandler(c *gin.Context) {
	city := trimParam(c.Query("city"))
	province := trimParam(c.Query("province"))
	county := trimParam(c.Query("county"))
	municipality := trimParam(c.Query("municipality"))
	prefix := trimParam(c.Query("prefix"))

	response, err := services.GetStreets(stringPtr(city), stringPtr(province), stringPtr(county), stringPtr(municipality), stringPtr(prefix))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	c.JSON(http.StatusOK, response)
}

// healthCheckHandler handles health check endpoint
func healthCheckHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"status": "healthy"})
}