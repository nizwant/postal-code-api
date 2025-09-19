defmodule PostalCodeApi.HouseNumberMatcher do
  @moduledoc """
  House number matching logic for Polish postal code database.

  This module handles matching a specific house number against complex Polish address
  range patterns like "270-336(p), 283-335(n)" or "4a-9/11, 7-29/31(n), 33/37".

  The patterns are now normalized (split by comma) so this function only needs to handle
  individual range patterns, not comma-separated combinations.
  """

  @doc """
  Extract the numeric part from a house number like "123a" -> 123.
  """
  def extract_numeric_part(nil), do: nil
  def extract_numeric_part(""), do: nil

  def extract_numeric_part(house_number) when is_binary(house_number) do
    case Regex.run(~r/^(\d+)/, String.trim(house_number)) do
      [_, num_str] -> String.to_integer(num_str)
      nil -> nil
    end
  end

  def extract_numeric_part(house_number) when is_integer(house_number), do: house_number

  @doc """
  Check if a number is odd.
  """
  def is_odd(number) when is_integer(number), do: rem(number, 2) == 1

  @doc """
  Check if a number is even.
  """
  def is_even(number) when is_integer(number), do: rem(number, 2) == 0

  @doc """
  Parse range endpoints from strings like "270-336", "4a-9", "55-DK".
  Returns {start_num, end_num, is_dk, has_letter_start, has_letter_end}
  """
  def parse_range_endpoints(range_part) do
    # Handle DK (do końca / to the end) ranges
    case Regex.run(~r/^(\d+[a-z]?)-DK/i, range_part) do
      [_, start_str] ->
        start_num = extract_numeric_part(start_str)
        has_letter_start = Regex.match?(~r/[a-z]/, start_str)
        {start_num, nil, true, has_letter_start, false}

      nil ->
        # Handle regular ranges like "270-336" or "4a-9b"
        case Regex.run(~r/^(\d+[a-z]?)-(\d+[a-z]?)$/, range_part) do
          [_, start_str, end_str] ->
            start_num = extract_numeric_part(start_str)
            end_num = extract_numeric_part(end_str)
            has_letter_start = Regex.match?(~r/[a-z]/, start_str)
            has_letter_end = Regex.match?(~r/[a-z]/, end_str)
            {start_num, end_num, false, has_letter_start, has_letter_end}

          nil ->
            {nil, nil, false, false, false}
        end
    end
  end

  @doc """
  Handle slash notation patterns like "2/4", "55-69/71", "2/4-10", "1/3-23/25(n)".
  """
  def handle_slash_notation(house_number, range_string) do
    house_num = extract_numeric_part(house_number)

    if house_num == nil do
      false
    else
      cond do
        # Pattern: "1/3-23/25(n)" - complex pattern with multiple slashes and ranges
        match = Regex.run(~r/^(\d+)\/(\d+)-(\d+)\/(\d+)(\([np]\))?$/, range_string) ->
          [_, start1_str, start2_str, end1_str, end2_str, side_indicator] = match
          start1 = String.to_integer(start1_str)
          start2 = String.to_integer(start2_str)
          end1 = String.to_integer(end1_str)
          end2 = String.to_integer(end2_str)

          # This pattern means: house_num in [start1, start2] OR house_num in [end1, end2]
          in_range = house_num in [start1, start2] or house_num in [end1, end2]

          if in_range do
            case side_indicator do
              "(n)" -> is_odd(house_num)
              "(p)" -> is_even(house_num)
              _ -> true
            end
          else
            false
          end

        # Pattern: "2/4" - individual numbers separated by slash
        Regex.match?(~r/^\d+\/\d+$/, range_string) ->
          numbers = String.split(range_string, "/")
                   |> Enum.map(&extract_numeric_part/1)
                   |> Enum.filter(&(!is_nil(&1)))
          house_num in numbers

        # Pattern: "55-69/71" or "55-69/71(n)" - range with specific end points
        match = Regex.run(~r/^(\d+)-(\d+)\/(\d+)(\([np]\))?$/, range_string) ->
          [_, start_str, mid_str, end_str, side_indicator] = match
          start = String.to_integer(start_str)
          mid = String.to_integer(mid_str)
          end_num = String.to_integer(end_str)

          # Check if house number is in the range [start, mid] or equals end
          in_range = (start <= house_num and house_num <= mid) or house_num == end_num

          if in_range do
            case side_indicator do
              "(n)" -> is_odd(house_num)
              "(p)" -> is_even(house_num)
              _ -> true
            end
          else
            false
          end

        # Pattern: "2/4-10" or "2/4-10(p)" - slash number plus range
        match = Regex.run(~r/^(\d+)\/(\d+)-(\d+)(\([np]\))?$/, range_string) ->
          [_, _start1_str, start2_str, end_str, side_indicator] = match
          start2 = String.to_integer(start2_str)
          end_num = String.to_integer(end_str)

          # For slash-range patterns like "2/4-10(p)", the range only covers [start2, end]
          in_range = start2 <= house_num and house_num <= end_num

          if in_range do
            case side_indicator do
              "(n)" -> is_odd(house_num)
              "(p)" -> is_even(house_num)
              _ -> true
            end
          else
            false
          end

        true ->
          false
      end
    end
  end

  @doc """
  Check if a house number matches a Polish address range pattern.

  This function handles individual range patterns (after normalization splits
  comma-separated ranges). It supports:

  - Simple ranges: "1-12"
  - Side indicators: "1-41(n)" (odd), "2-38(p)" (even)
  - DK ranges: "337-DK", "2-DK(p)" (open-ended)
  - Letter suffixes: "4a-9/11", "31-31a"
  - Slash notation: "55-69/71(n)", "2/4"
  - Individual numbers: "60", "35c"
  """
  def is_house_number_in_range(house_number, range_string) do
    # Handle empty/null inputs
    if is_nil(house_number) or is_nil(range_string) or
       house_number == "" or range_string == "" do
      false
    else
      house_number = String.trim(to_string(house_number))
      range_string = String.trim(to_string(range_string))

      if house_number == "" or range_string == "" do
        false
      else
        house_num = extract_numeric_part(house_number)

        if house_num == nil do
          false
        else
          cond do
            # Handle individual numbers (exact match)
            Regex.match?(~r/^\d+[a-z]?$/, range_string) ->
              if Regex.match?(~r/[a-z]/, range_string) do
                # For individual numbers with letters, require exact match
                house_number == range_string
              else
                # For pure numeric individual numbers, allow numeric match
                individual_num = extract_numeric_part(range_string)
                individual_num != nil and house_num == individual_num
              end

            # Handle slash notation patterns
            String.contains?(range_string, "/") ->
              handle_slash_notation(house_number, range_string)

            true ->
              # Extract side indicator and base range
              {side_indicator, base_range} = extract_side_indicator(range_string)

              # Parse the range
              {start_num, end_num, is_dk, has_letter_start, _has_letter_end} =
                parse_range_endpoints(base_range)

              if start_num == nil do
                false
              else
                # Check if house number is within the numeric range
                in_range = cond do
                  is_dk ->
                    # DK range: house_num >= start_num
                    # Special case: if start has letter (e.g., "6a-DK"), plain number equal to start should NOT match
                    if has_letter_start and not Regex.match?(~r/[a-z]/, house_number) and house_num == start_num do
                      false  # "6" should not match "6a-DK", but "8" should
                    else
                      house_num >= start_num
                    end

                  end_num != nil ->
                    # Regular range: start_num <= house_num <= end_num
                    start_num <= house_num and house_num <= end_num

                  true ->
                    # Single number (start_num only)
                    house_num == start_num
                end

                if in_range do
                  # Apply side indicator constraints
                  case side_indicator do
                    "n" -> is_odd(house_num)  # nieparzyste (odd)
                    "p" -> is_even(house_num)  # parzyste (even)
                    _ -> true  # No side constraint
                  end
                else
                  false
                end
              end
          end
        end
      end
    end
  end

  defp extract_side_indicator(range_string) do
    case Regex.run(~r/\(([np])\)$/, range_string) do
      [match, side] ->
        base_range = String.replace_suffix(range_string, match, "")
        {side, base_range}
      nil ->
        {nil, range_string}
    end
  end
end