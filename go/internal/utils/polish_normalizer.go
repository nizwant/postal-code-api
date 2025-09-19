package utils

import (
	"strings"
)

// polishCharMap maps Polish characters to ASCII equivalents
var polishCharMap = map[rune]rune{
	// Lowercase Polish characters
	'ą': 'a',
	'ć': 'c',
	'ę': 'e',
	'ł': 'l',
	'ń': 'n',
	'ó': 'o',
	'ś': 's',
	'ź': 'z',
	'ż': 'z',

	// Uppercase Polish characters
	'Ą': 'A',
	'Ć': 'C',
	'Ę': 'E',
	'Ł': 'L',
	'Ń': 'N',
	'Ó': 'O',
	'Ś': 'S',
	'Ź': 'Z',
	'Ż': 'Z',
}

// NormalizePolishText converts Polish characters to ASCII equivalents
func NormalizePolishText(text string) string {
	if text == "" {
		return text
	}

	var result strings.Builder
	result.Grow(len(text))

	for _, char := range text {
		if normalizedChar, exists := polishCharMap[char]; exists {
			result.WriteRune(normalizedChar)
		} else {
			result.WriteRune(char)
		}
	}

	return result.String()
}

// HasPolishCharacters checks if text contains Polish diacritical characters
func HasPolishCharacters(text string) bool {
	if text == "" {
		return false
	}

	for _, char := range text {
		if _, exists := polishCharMap[char]; exists {
			return true
		}
	}
	return false
}

// SearchParams represents search parameters that can be normalized
type SearchParams struct {
	City         *string
	Street       *string
	HouseNumber  *string
	Province     *string
	County       *string
	Municipality *string
	Limit        int
}

// GetNormalizedSearchParams returns normalized search parameters for Polish character fallback
func GetNormalizedSearchParams(params SearchParams) SearchParams {
	normalized := SearchParams{
		Limit: params.Limit,
	}

	if params.City != nil {
		city := NormalizePolishText(*params.City)
		normalized.City = &city
	}

	if params.Street != nil {
		street := NormalizePolishText(*params.Street)
		normalized.Street = &street
	}

	if params.HouseNumber != nil {
		houseNumber := NormalizePolishText(*params.HouseNumber)
		normalized.HouseNumber = &houseNumber
	}

	if params.Province != nil {
		province := NormalizePolishText(*params.Province)
		normalized.Province = &province
	}

	if params.County != nil {
		county := NormalizePolishText(*params.County)
		normalized.County = &county
	}

	if params.Municipality != nil {
		municipality := NormalizePolishText(*params.Municipality)
		normalized.Municipality = &municipality
	}

	return normalized
}