package utils

import (
	"regexp"
	"strconv"
	"strings"
)

// extractNumericPart extracts the numeric part from a house number like "123a" -> 123
func extractNumericPart(houseNumber string) (int, bool) {
	if houseNumber == "" {
		return 0, false
	}

	re := regexp.MustCompile(`^(\d+)`)
	matches := re.FindStringSubmatch(strings.TrimSpace(houseNumber))
	if len(matches) > 1 {
		if num, err := strconv.Atoi(matches[1]); err == nil {
			return num, true
		}
	}
	return 0, false
}

// isOdd checks if a number is odd
func isOdd(number int) bool {
	return number%2 == 1
}

// isEven checks if a number is even
func isEven(number int) bool {
	return number%2 == 0
}

// rangeEndpoints represents parsed range endpoints
type rangeEndpoints struct {
	startNum        int
	endNum          int
	isDK            bool
	hasLetterStart  bool
	hasLetterEnd    bool
	valid           bool
}

// parseRangeEndpoints parses range endpoints from strings like "270-336", "4a-9", "55-DK"
func parseRangeEndpoints(rangePart string) rangeEndpoints {
	// Handle DK (do końca / to the end) ranges
	if strings.Contains(strings.ToUpper(rangePart), "DK") {
		re := regexp.MustCompile(`^(\d+[a-z]?)-DK`)
		matches := re.FindStringSubmatch(rangePart)
		if len(matches) > 1 {
			startStr := matches[1]
			startNum, hasStart := extractNumericPart(startStr)
			if hasStart {
				hasLetterStart := regexp.MustCompile(`[a-z]`).MatchString(startStr)
				return rangeEndpoints{
					startNum:       startNum,
					endNum:         0,
					isDK:           true,
					hasLetterStart: hasLetterStart,
					hasLetterEnd:   false,
					valid:          true,
				}
			}
		}
	}

	// Handle regular ranges like "270-336" or "4a-9b"
	re := regexp.MustCompile(`^(\d+[a-z]?)-(\d+[a-z]?)$`)
	matches := re.FindStringSubmatch(rangePart)
	if len(matches) > 2 {
		startStr := matches[1]
		endStr := matches[2]
		startNum, hasStart := extractNumericPart(startStr)
		endNum, hasEnd := extractNumericPart(endStr)
		if hasStart && hasEnd {
			hasLetterStart := regexp.MustCompile(`[a-z]`).MatchString(startStr)
			hasLetterEnd := regexp.MustCompile(`[a-z]`).MatchString(endStr)
			return rangeEndpoints{
				startNum:       startNum,
				endNum:         endNum,
				isDK:           false,
				hasLetterStart: hasLetterStart,
				hasLetterEnd:   hasLetterEnd,
				valid:          true,
			}
		}
	}

	return rangeEndpoints{valid: false}
}

// handleSlashNotation handles slash notation patterns like "2/4", "55-69/71", "2/4-10", "1/3-23/25(n)"
func handleSlashNotation(houseNumber, rangeString string) bool {
	houseNum, hasHouseNum := extractNumericPart(houseNumber)
	if !hasHouseNum {
		return false
	}

	// Pattern: "1/3-23/25(n)" - complex pattern with multiple slashes and ranges
	complexSlashRe := regexp.MustCompile(`^(\d+)/(\d+)-(\d+)/(\d+)(\([np]\))?$`)
	if matches := complexSlashRe.FindStringSubmatch(rangeString); len(matches) > 4 {
		start1, _ := strconv.Atoi(matches[1])
		start2, _ := strconv.Atoi(matches[2])
		end1, _ := strconv.Atoi(matches[3])
		end2, _ := strconv.Atoi(matches[4])
		sideIndicator := ""
		if len(matches) > 5 {
			sideIndicator = matches[5]
		}

		// This pattern means: house_num in [start1, start2] OR house_num in [end1, end2]
		inRange := (houseNum == start1 || houseNum == start2) || (houseNum == end1 || houseNum == end2)

		if !inRange {
			return false
		}

		// Apply side indicator if present
		if sideIndicator == "(n)" { // odd only
			return isOdd(houseNum)
		} else if sideIndicator == "(p)" { // even only
			return isEven(houseNum)
		}

		return true
	}

	// Pattern: "2/4" - individual numbers separated by slash
	if regexp.MustCompile(`^\d+/\d+$`).MatchString(rangeString) {
		numbers := strings.Split(rangeString, "/")
		for _, numStr := range numbers {
			if num, err := strconv.Atoi(numStr); err == nil && num == houseNum {
				return true
			}
		}
		return false
	}

	// Pattern: "55-69/71" or "55-69/71(n)" - range with specific end points
	slashRangeRe := regexp.MustCompile(`^(\d+)-(\d+)/(\d+)(\([np]\))?$`)
	if matches := slashRangeRe.FindStringSubmatch(rangeString); len(matches) > 3 {
		start, _ := strconv.Atoi(matches[1])
		mid, _ := strconv.Atoi(matches[2])
		end, _ := strconv.Atoi(matches[3])
		sideIndicator := ""
		if len(matches) > 4 {
			sideIndicator = matches[4]
		}

		// Check if house number is in the range [start, mid] or equals end
		inRange := (start <= houseNum && houseNum <= mid) || (houseNum == end)

		if !inRange {
			return false
		}

		// Apply side indicator if present
		if sideIndicator == "(n)" { // odd only
			return isOdd(houseNum)
		} else if sideIndicator == "(p)" { // even only
			return isEven(houseNum)
		}

		return true
	}

	// Pattern: "2/4-10" or "2/4-10(p)" - slash number plus range
	slashStartRe := regexp.MustCompile(`^(\d+)/(\d+)-(\d+)(\([np]\))?$`)
	if matches := slashStartRe.FindStringSubmatch(rangeString); len(matches) > 3 {
		start2, _ := strconv.Atoi(matches[2])
		end, _ := strconv.Atoi(matches[3])
		sideIndicator := ""
		if len(matches) > 4 {
			sideIndicator = matches[4]
		}

		// For slash-range patterns like "2/4-10(p)", the range only covers [start2, end]
		inRange := false

		// Check if house_num is in the range part
		if start2 <= houseNum && houseNum <= end {
			// Apply side indicator to range numbers
			if sideIndicator == "(n)" { // odd only
				inRange = isOdd(houseNum)
			} else if sideIndicator == "(p)" { // even only
				inRange = isEven(houseNum)
			} else {
				inRange = true
			}
		}

		return inRange
	}

	return false
}

// IsHouseNumberInRange checks if a house number matches a Polish address range pattern
func IsHouseNumberInRange(houseNumber, rangeString string) bool {
	// Handle empty/null inputs
	if houseNumber == "" || rangeString == "" {
		return false
	}

	// Clean inputs
	houseNumber = strings.TrimSpace(houseNumber)
	rangeString = strings.TrimSpace(rangeString)

	if houseNumber == "" || rangeString == "" {
		return false
	}

	// Extract numeric part of the house number
	houseNum, hasHouseNum := extractNumericPart(houseNumber)
	if !hasHouseNum {
		return false
	}

	// Handle individual numbers (exact match)
	if regexp.MustCompile(`^\d+[a-z]?$`).MatchString(rangeString) {
		// For individual numbers with letters, require exact match
		if regexp.MustCompile(`[a-z]`).MatchString(rangeString) {
			return houseNumber == rangeString
		}
		// For pure numeric individual numbers, allow numeric match
		if individualNum, hasIndividual := extractNumericPart(rangeString); hasIndividual {
			return houseNum == individualNum
		}
		return false
	}

	// Handle slash notation patterns
	if strings.Contains(rangeString, "/") {
		return handleSlashNotation(houseNumber, rangeString)
	}

	// Extract side indicator and base range
	sideIndicator := ""
	baseRange := rangeString

	// Check for side indicators: (n) = odd, (p) = even
	sideRe := regexp.MustCompile(`\(([np])\)$`)
	if matches := sideRe.FindStringSubmatch(rangeString); len(matches) > 1 {
		sideIndicator = matches[1]
		baseRange = rangeString[:sideRe.FindStringIndex(rangeString)[0]]
	}

	// Parse the range
	endpoints := parseRangeEndpoints(baseRange)
	if !endpoints.valid {
		return false
	}

	// Check if house number is within the numeric range
	inRange := false

	if endpoints.isDK {
		// DK range: house_num >= start_num
		// Special case: if start has letter (e.g., "6a-DK"), plain number equal to start should NOT match
		if endpoints.hasLetterStart && !regexp.MustCompile(`[a-z]`).MatchString(houseNumber) && houseNum == endpoints.startNum {
			return false // "6" should not match "6a-DK", but "8" should
		}
		inRange = houseNum >= endpoints.startNum
	} else if endpoints.endNum > 0 {
		// Regular range: start_num <= house_num <= end_num
		inRange = endpoints.startNum <= houseNum && houseNum <= endpoints.endNum
	} else {
		// Single number (start_num only)
		inRange = houseNum == endpoints.startNum
	}

	if !inRange {
		return false
	}

	// Apply side indicator constraints
	if sideIndicator == "n" { // nieparzyste (odd)
		return isOdd(houseNum)
	} else if sideIndicator == "p" { // parzyste (even)
		return isEven(houseNum)
	}

	// No side constraint, any house number in range is valid
	return true
}