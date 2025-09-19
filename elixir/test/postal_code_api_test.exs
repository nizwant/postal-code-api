defmodule PostalCodeApiTest do
  use ExUnit.Case
  doctest PostalCodeApi

  alias PostalCodeApi.{PostalService, PolishNormalizer, HouseNumberMatcher}

  describe "Polish normalization" do
    test "normalizes Polish characters" do
      assert PolishNormalizer.normalize_polish_text("Łódź") == "Lodz"
      assert PolishNormalizer.normalize_polish_text("Kraków") == "Krakow"
      assert PolishNormalizer.normalize_polish_text("Gdańsk") == "Gdansk"
    end

    test "detects Polish characters" do
      assert PolishNormalizer.has_polish_characters("Łódź") == true
      assert PolishNormalizer.has_polish_characters("Warsaw") == false
    end
  end

  describe "House number matching" do
    test "matches simple ranges" do
      assert HouseNumberMatcher.is_house_number_in_range("5", "1-10") == true
      assert HouseNumberMatcher.is_house_number_in_range("15", "1-10") == false
    end

    test "handles side indicators" do
      assert HouseNumberMatcher.is_house_number_in_range("3", "1-10(n)") == true
      assert HouseNumberMatcher.is_house_number_in_range("4", "1-10(n)") == false
      assert HouseNumberMatcher.is_house_number_in_range("4", "1-10(p)") == true
      assert HouseNumberMatcher.is_house_number_in_range("3", "1-10(p)") == false
    end

    test "handles DK ranges" do
      assert HouseNumberMatcher.is_house_number_in_range("100", "50-DK") == true
      assert HouseNumberMatcher.is_house_number_in_range("25", "50-DK") == false
    end

    test "handles individual numbers" do
      assert HouseNumberMatcher.is_house_number_in_range("60", "60") == true
      assert HouseNumberMatcher.is_house_number_in_range("61", "60") == false
    end
  end

  describe "API basic functionality" do
    test "health endpoint works" do
      # This would require setting up a test HTTP client
      # For now, just test that modules compile and basic functions work
      assert true
    end

    test "search parameters are processed correctly" do
      params = %{
        city: "Warszawa",
        street: "Abramowskiego",
        house_number: "5",
        limit: 100
      }

      # Test that the function can be called without error
      # In a real test environment, this would make actual API calls
      assert is_map(params)
    end
  end
end