package services

import (
	"fmt"
	"strings"

	"postal-api/internal/database"
	"postal-api/internal/utils"
)

// SearchResponse represents the response structure for search operations
type SearchResponse struct {
	Results                   []database.PostalCode `json:"results"`
	Count                     int                   `json:"count"`
	SearchType                string                `json:"search_type"`
	Message                   string                `json:"message,omitempty"`
	FallbackUsed              bool                  `json:"fallback_used,omitempty"`
	PolishNormalizationUsed   bool                  `json:"polish_normalization_used,omitempty"`
}

// LocationResponse represents the response structure for location operations
type LocationResponse struct {
	Results            []string `json:"results"`
	Count              int      `json:"count"`
	FilteredByProvince *string  `json:"filtered_by_province,omitempty"`
	FilteredByCounty   *string  `json:"filtered_by_county,omitempty"`
	FilteredByMunicipality *string `json:"filtered_by_municipality,omitempty"`
	FilteredByCity     *string  `json:"filtered_by_city,omitempty"`
	FilteredByPrefix   *string  `json:"filtered_by_prefix,omitempty"`
}

// ProvinceResponse represents the response for provinces
type ProvinceResponse struct {
	Provinces          []string `json:"provinces"`
	Count              int      `json:"count"`
	FilteredByPrefix   *string  `json:"filtered_by_prefix,omitempty"`
}

// CountyResponse represents the response for counties
type CountyResponse struct {
	Counties           []string `json:"counties"`
	Count              int      `json:"count"`
	FilteredByProvince *string  `json:"filtered_by_province,omitempty"`
	FilteredByPrefix   *string  `json:"filtered_by_prefix,omitempty"`
}

// MunicipalityResponse represents the response for municipalities
type MunicipalityResponse struct {
	Municipalities     []string `json:"municipalities"`
	Count              int      `json:"count"`
	FilteredByProvince *string  `json:"filtered_by_province,omitempty"`
	FilteredByCounty   *string  `json:"filtered_by_county,omitempty"`
	FilteredByPrefix   *string  `json:"filtered_by_prefix,omitempty"`
}

// CityResponse represents the response for cities
type CityResponse struct {
	Cities             []string `json:"cities"`
	Count              int      `json:"count"`
	FilteredByProvince *string  `json:"filtered_by_province,omitempty"`
	FilteredByCounty   *string  `json:"filtered_by_county,omitempty"`
	FilteredByMunicipality *string `json:"filtered_by_municipality,omitempty"`
	FilteredByPrefix   *string  `json:"filtered_by_prefix,omitempty"`
}

// StreetResponse represents the response for streets
type StreetResponse struct {
	Streets            []string `json:"streets"`
	Count              int      `json:"count"`
	FilteredByCity     *string  `json:"filtered_by_city,omitempty"`
	FilteredByProvince *string  `json:"filtered_by_province,omitempty"`
	FilteredByCounty   *string  `json:"filtered_by_county,omitempty"`
	FilteredByMunicipality *string `json:"filtered_by_municipality,omitempty"`
	FilteredByPrefix   *string  `json:"filtered_by_prefix,omitempty"`
}

// buildSearchQuery builds a search query with the given parameters
func buildSearchQuery(params utils.SearchParams, useNormalized bool) (string, []interface{}) {
	query := "SELECT * FROM postal_codes WHERE 1=1"
	var args []interface{}

	// Choose column names based on whether we're using normalized search
	cityCol := "city"
	streetCol := "street"
	if useNormalized {
		cityCol = "city_normalized"
		streetCol = "street_normalized"
	}

	if params.City != nil && *params.City != "" {
		query += fmt.Sprintf(" AND %s LIKE ? COLLATE NOCASE", cityCol)
		args = append(args, *params.City+"%")
	}

	if params.Street != nil && *params.Street != "" {
		query += fmt.Sprintf(" AND %s LIKE ? COLLATE NOCASE", streetCol)
		args = append(args, "%"+*params.Street+"%")
	}

	if params.Province != nil && *params.Province != "" {
		query += " AND province = ? COLLATE NOCASE"
		args = append(args, *params.Province)
	}

	if params.County != nil && *params.County != "" {
		query += " AND county = ? COLLATE NOCASE"
		args = append(args, *params.County)
	}

	if params.Municipality != nil && *params.Municipality != "" {
		query += " AND municipality = ? COLLATE NOCASE"
		args = append(args, *params.Municipality)
	}

	// Use a larger limit since we'll filter in Go
	sqlLimit := params.Limit
	if params.HouseNumber != nil && *params.HouseNumber != "" {
		sqlLimit = min(params.Limit*5, 1000)
	}
	query += " LIMIT ?"
	args = append(args, sqlLimit)

	return query, args
}

// min returns the minimum of two integers
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// filterByHouseNumber filters database results by house number using the range matching logic
func filterByHouseNumber(results []database.PostalCode, houseNumber *string, limit int) []database.PostalCode {
	if houseNumber == nil || *houseNumber == "" {
		if len(results) > limit {
			return results[:limit]
		}
		return results
	}

	var filteredResults []database.PostalCode

	for _, row := range results {
		// Records without house_numbers don't match specific house number searches
		if row.HouseNumbers == nil || *row.HouseNumbers == "" {
			continue
		}

		// Use the range matching logic
		if utils.IsHouseNumberInRange(*houseNumber, *row.HouseNumbers) {
			filteredResults = append(filteredResults, row)

			// Stop when we have enough results
			if len(filteredResults) >= limit {
				break
			}
		}
	}

	return filteredResults
}

// executeFallbackSearch executes fallback search logic when initial search returned no results
func executeFallbackSearch(params utils.SearchParams, useNormalized bool) ([]database.PostalCode, bool, string, error) {
	db := database.GetDB()

	fallbackUsed := false
	fallbackMessage := ""
	var results []database.PostalCode

	// Fallback 1: Remove house_number if present
	if params.HouseNumber != nil && *params.HouseNumber != "" {
		// Re-run query without house_number considerations
		fallbackParams := params
		fallbackParams.HouseNumber = nil
		query, args := buildSearchQuery(fallbackParams, useNormalized)
		rows, err := db.Query(query, args...)
		if err != nil {
			return nil, false, "", fmt.Errorf("fallback database query failed: %w", err)
		}
		defer rows.Close()

		results = nil
		for rows.Next() {
			var pc database.PostalCode
			var id int
			var cityNormalized, streetNormalized *string
			err := rows.Scan(&id, &pc.PostalCode, &pc.City, &pc.Street, &pc.HouseNumbers, &pc.Municipality, &pc.County, &pc.Province, &cityNormalized, &streetNormalized)
			if err != nil {
				return nil, false, "", fmt.Errorf("failed to scan fallback row: %w", err)
			}
			results = append(results, pc)
		}

		if len(results) > 0 {
			fallbackUsed = true
			var locationDesc []string
			if params.Street != nil && *params.Street != "" {
				locationDesc = append(locationDesc, fmt.Sprintf("street '%s'", *params.Street))
			}
			if params.City != nil && *params.City != "" {
				locationDesc = append(locationDesc, fmt.Sprintf("city '%s'", *params.City))
			}
			locationStr := ""
			if len(locationDesc) > 0 {
				locationStr = " in " + strings.Join(locationDesc, " in ")
			}
			fallbackMessage = fmt.Sprintf("House number '%s' not found%s. Showing all results%s.", *params.HouseNumber, locationStr, locationStr)
		}
	}

	// Fallback 2: Remove street if still no results and we have city + street
	if len(results) == 0 && params.City != nil && *params.City != "" && params.Street != nil && *params.Street != "" {
		fallbackParams := params
		fallbackParams.Street = nil
		fallbackParams.HouseNumber = nil
		query, args := buildSearchQuery(fallbackParams, useNormalized)
		rows, err := db.Query(query, args...)
		if err != nil {
			return nil, false, "", fmt.Errorf("second fallback database query failed: %w", err)
		}
		defer rows.Close()

		results = nil
		for rows.Next() {
			var pc database.PostalCode
			var id int
			var cityNormalized, streetNormalized *string
			err := rows.Scan(&id, &pc.PostalCode, &pc.City, &pc.Street, &pc.HouseNumbers, &pc.Municipality, &pc.County, &pc.Province, &cityNormalized, &streetNormalized)
			if err != nil {
				return nil, false, "", fmt.Errorf("failed to scan second fallback row: %w", err)
			}
			results = append(results, pc)
		}

		if len(results) > 0 {
			fallbackUsed = true
			if params.HouseNumber != nil && *params.HouseNumber != "" {
				fallbackMessage = fmt.Sprintf("Street '%s' with house number '%s' not found in %s. Showing all results for %s.", *params.Street, *params.HouseNumber, *params.City, *params.City)
			} else {
				fallbackMessage = fmt.Sprintf("Street '%s' not found in %s. Showing all results for %s.", *params.Street, *params.City, *params.City)
			}
		}
	}

	return results, fallbackUsed, fallbackMessage, nil
}

// SearchPostalCodes searches postal codes with four-tier approach: exact, Polish normalization, fallbacks, then Polish fallbacks
func SearchPostalCodes(params utils.SearchParams) (*SearchResponse, error) {
	// Pre-calculate normalized parameters once
	normalizedParams := utils.GetNormalizedSearchParams(params)

	polishFallbackUsed := false
	searchType := "exact"
	fallbackUsed := false
	fallbackMessage := ""

	// Tier 1: Exact search with original parameters
	db := database.GetDB()
	query, args := buildSearchQuery(params, false)
	rows, err := db.Query(query, args...)
	if err != nil {
		return nil, fmt.Errorf("database query failed: %w", err)
	}
	defer rows.Close()

	var sqlResults []database.PostalCode
	for rows.Next() {
		var pc database.PostalCode
		var id int
		var cityNormalized, streetNormalized interface{}
		err := rows.Scan(&id, &pc.PostalCode, &pc.City, &pc.Street, &pc.HouseNumbers, &pc.Municipality, &pc.County, &pc.Province, &cityNormalized, &streetNormalized)
		if err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}
		sqlResults = append(sqlResults, pc)
	}

	exactResults := filterByHouseNumber(sqlResults, params.HouseNumber, params.Limit)
	var results []database.PostalCode

	if len(exactResults) > 0 {
		results = exactResults
	} else {
		// Tier 2: Polish character normalization search
		query, args := buildSearchQuery(normalizedParams, true)
		rows, err := db.Query(query, args...)
		if err != nil {
			return nil, fmt.Errorf("normalized database query failed: %w", err)
		}
		defer rows.Close()

		var polishSqlResults []database.PostalCode
		for rows.Next() {
			var pc database.PostalCode
			var id int
			var cityNormalized, streetNormalized *string
			err := rows.Scan(&id, &pc.PostalCode, &pc.City, &pc.Street, &pc.HouseNumbers, &pc.Municipality, &pc.County, &pc.Province, &cityNormalized, &streetNormalized)
			if err != nil {
				return nil, fmt.Errorf("failed to scan normalized row: %w", err)
			}
			polishSqlResults = append(polishSqlResults, pc)
		}

		polishResults := filterByHouseNumber(polishSqlResults, normalizedParams.HouseNumber, params.Limit)

		if len(polishResults) > 0 {
			results = polishResults
			polishFallbackUsed = true
			searchType = "polish_characters"
		} else {
			// Tier 3: Original fallback logic (house_number → street → city-only)
			tier3Results, tier3FallbackUsed, tier3FallbackMessage, err := executeFallbackSearch(params, false)
			if err != nil {
				return nil, fmt.Errorf("tier 3 fallback failed: %w", err)
			}

			// Tier 4: Polish normalization fallback logic (only if Tier 3 failed)
			if len(tier3Results) == 0 {
				tier4Results, tier4FallbackUsed, tier4FallbackMessage, err := executeFallbackSearch(normalizedParams, true)
				if err != nil {
					return nil, fmt.Errorf("tier 4 fallback failed: %w", err)
				}

				if len(tier4Results) > 0 {
					results = tier4Results
					fallbackUsed = tier4FallbackUsed
					fallbackMessage = tier4FallbackMessage
					polishFallbackUsed = true
					searchType = "polish_characters"
				}
			} else {
				results = tier3Results
				fallbackUsed = tier3FallbackUsed
				fallbackMessage = tier3FallbackMessage
			}
		}
	}

	response := &SearchResponse{
		Results:    results,
		Count:      len(results),
		SearchType: searchType,
	}

	if fallbackUsed {
		response.Message = fallbackMessage
		response.FallbackUsed = true
	}

	if polishFallbackUsed {
		if response.Message != "" {
			response.Message += " Polish characters were normalized for search."
		} else {
			response.Message = "Search performed with Polish character normalization."
		}
		response.PolishNormalizationUsed = true
	}

	return response, nil
}

// GetPostalCodeByCode gets postal code records by postal code
func GetPostalCodeByCode(postalCode string) (*SearchResponse, error) {
	db := database.GetDB()
	query := "SELECT * FROM postal_codes WHERE postal_code = ?"
	rows, err := db.Query(query, postalCode)
	if err != nil {
		return nil, fmt.Errorf("database query failed: %w", err)
	}
	defer rows.Close()

	var results []database.PostalCode
	for rows.Next() {
		var pc database.PostalCode
		var id int
		var cityNormalized, streetNormalized interface{}
		err := rows.Scan(&id, &pc.PostalCode, &pc.City, &pc.Street, &pc.HouseNumbers, &pc.Municipality, &pc.County, &pc.Province, &cityNormalized, &streetNormalized)
		if err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}
		results = append(results, pc)
	}

	if len(results) == 0 {
		return nil, nil
	}

	return &SearchResponse{
		Results: results,
		Count:   len(results),
	}, nil
}

// GetProvinces gets all provinces, optionally filtered by prefix
func GetProvinces(prefix *string) (*ProvinceResponse, error) {
	db := database.GetDB()
	query := "SELECT DISTINCT province FROM postal_codes WHERE province IS NOT NULL ORDER BY province"
	rows, err := db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("database query failed: %w", err)
	}
	defer rows.Close()

	var allProvinces []string
	for rows.Next() {
		var province string
		if err := rows.Scan(&province); err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}
		allProvinces = append(allProvinces, province)
	}

	var filteredProvinces []string
	if prefix != nil && *prefix != "" {
		normalizedPrefix := strings.ToLower(utils.NormalizePolishText(*prefix))
		originalPrefix := strings.ToLower(*prefix)

		for _, province := range allProvinces {
			provinceLower := strings.ToLower(province)
			normalizedProvince := strings.ToLower(utils.NormalizePolishText(province))
			if strings.HasPrefix(provinceLower, originalPrefix) || strings.HasPrefix(normalizedProvince, normalizedPrefix) {
				filteredProvinces = append(filteredProvinces, province)
			}
		}
	} else {
		filteredProvinces = allProvinces
	}

	return &ProvinceResponse{
		Provinces:        filteredProvinces,
		Count:            len(filteredProvinces),
		FilteredByPrefix: prefix,
	}, nil
}

// GetCounties gets counties, optionally filtered by province and/or prefix
func GetCounties(province, prefix *string) (*CountyResponse, error) {
	db := database.GetDB()
	query := "SELECT DISTINCT county FROM postal_codes WHERE county IS NOT NULL"
	var args []interface{}

	if province != nil && *province != "" {
		query += " AND province = ? COLLATE NOCASE"
		args = append(args, *province)
	}

	query += " ORDER BY county"

	rows, err := db.Query(query, args...)
	if err != nil {
		return nil, fmt.Errorf("database query failed: %w", err)
	}
	defer rows.Close()

	var allCounties []string
	for rows.Next() {
		var county string
		if err := rows.Scan(&county); err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}
		allCounties = append(allCounties, county)
	}

	var filteredCounties []string
	if prefix != nil && *prefix != "" {
		normalizedPrefix := strings.ToLower(utils.NormalizePolishText(*prefix))
		originalPrefix := strings.ToLower(*prefix)

		for _, county := range allCounties {
			countyLower := strings.ToLower(county)
			normalizedCounty := strings.ToLower(utils.NormalizePolishText(county))
			if strings.HasPrefix(countyLower, originalPrefix) || strings.HasPrefix(normalizedCounty, normalizedPrefix) {
				filteredCounties = append(filteredCounties, county)
			}
		}
	} else {
		filteredCounties = allCounties
	}

	return &CountyResponse{
		Counties:           filteredCounties,
		Count:              len(filteredCounties),
		FilteredByProvince: province,
		FilteredByPrefix:   prefix,
	}, nil
}

// GetMunicipalities gets municipalities, optionally filtered by province, county, and/or prefix
func GetMunicipalities(province, county, prefix *string) (*MunicipalityResponse, error) {
	db := database.GetDB()
	query := "SELECT DISTINCT municipality FROM postal_codes WHERE municipality IS NOT NULL"
	var args []interface{}

	if province != nil && *province != "" {
		query += " AND province = ? COLLATE NOCASE"
		args = append(args, *province)
	}

	if county != nil && *county != "" {
		query += " AND county = ? COLLATE NOCASE"
		args = append(args, *county)
	}

	query += " ORDER BY municipality"

	rows, err := db.Query(query, args...)
	if err != nil {
		return nil, fmt.Errorf("database query failed: %w", err)
	}
	defer rows.Close()

	var allMunicipalities []string
	for rows.Next() {
		var municipality string
		if err := rows.Scan(&municipality); err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}
		allMunicipalities = append(allMunicipalities, municipality)
	}

	var filteredMunicipalities []string
	if prefix != nil && *prefix != "" {
		normalizedPrefix := strings.ToLower(utils.NormalizePolishText(*prefix))
		originalPrefix := strings.ToLower(*prefix)

		for _, municipality := range allMunicipalities {
			municipalityLower := strings.ToLower(municipality)
			normalizedMunicipality := strings.ToLower(utils.NormalizePolishText(municipality))
			if strings.HasPrefix(municipalityLower, originalPrefix) || strings.HasPrefix(normalizedMunicipality, normalizedPrefix) {
				filteredMunicipalities = append(filteredMunicipalities, municipality)
			}
		}
	} else {
		filteredMunicipalities = allMunicipalities
	}

	return &MunicipalityResponse{
		Municipalities:     filteredMunicipalities,
		Count:              len(filteredMunicipalities),
		FilteredByProvince: province,
		FilteredByCounty:   county,
		FilteredByPrefix:   prefix,
	}, nil
}

// GetCities gets cities, optionally filtered by province, county, municipality, and/or prefix
func GetCities(province, county, municipality, prefix *string) (*CityResponse, error) {
	db := database.GetDB()
	query := "SELECT DISTINCT city FROM postal_codes WHERE city IS NOT NULL"
	var args []interface{}

	if province != nil && *province != "" {
		query += " AND province = ? COLLATE NOCASE"
		args = append(args, *province)
	}

	if county != nil && *county != "" {
		query += " AND county = ? COLLATE NOCASE"
		args = append(args, *county)
	}

	if municipality != nil && *municipality != "" {
		query += " AND municipality = ? COLLATE NOCASE"
		args = append(args, *municipality)
	}

	if prefix != nil && *prefix != "" {
		normalizedPrefix := utils.NormalizePolishText(*prefix)
		query += " AND (city LIKE ? COLLATE NOCASE OR city_normalized LIKE ? COLLATE NOCASE)"
		args = append(args, *prefix+"%", normalizedPrefix+"%")
	}

	query += " ORDER BY population DESC, city"

	rows, err := db.Query(query, args...)
	if err != nil {
		return nil, fmt.Errorf("database query failed: %w", err)
	}
	defer rows.Close()

	var cities []string
	for rows.Next() {
		var city string
		if err := rows.Scan(&city); err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}
		cities = append(cities, city)
	}

	return &CityResponse{
		Cities:                 cities,
		Count:                  len(cities),
		FilteredByProvince:     province,
		FilteredByCounty:       county,
		FilteredByMunicipality: municipality,
		FilteredByPrefix:       prefix,
	}, nil
}

// GetStreets gets streets, optionally filtered by city, province, county, municipality, and/or prefix
func GetStreets(city, province, county, municipality, prefix *string) (*StreetResponse, error) {
	db := database.GetDB()
	query := "SELECT DISTINCT street FROM postal_codes WHERE street IS NOT NULL AND street != ''"
	var args []interface{}

	if city != nil && *city != "" {
		query += " AND city = ? COLLATE NOCASE"
		args = append(args, *city)
	}

	if province != nil && *province != "" {
		query += " AND province = ? COLLATE NOCASE"
		args = append(args, *province)
	}

	if county != nil && *county != "" {
		query += " AND county = ? COLLATE NOCASE"
		args = append(args, *county)
	}

	if municipality != nil && *municipality != "" {
		query += " AND municipality = ? COLLATE NOCASE"
		args = append(args, *municipality)
	}

	if prefix != nil && *prefix != "" {
		normalizedPrefix := utils.NormalizePolishText(*prefix)
		query += " AND (street LIKE ? COLLATE NOCASE OR street_normalized LIKE ? COLLATE NOCASE)"
		args = append(args, *prefix+"%", normalizedPrefix+"%")
	}

	query += " ORDER BY street"

	rows, err := db.Query(query, args...)
	if err != nil {
		return nil, fmt.Errorf("database query failed: %w", err)
	}
	defer rows.Close()

	var streets []string
	for rows.Next() {
		var street string
		if err := rows.Scan(&street); err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}
		streets = append(streets, street)
	}

	return &StreetResponse{
		Streets:                streets,
		Count:                  len(streets),
		FilteredByCity:         city,
		FilteredByProvince:     province,
		FilteredByCounty:       county,
		FilteredByMunicipality: municipality,
		FilteredByPrefix:       prefix,
	}, nil
}