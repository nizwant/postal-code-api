defmodule PostalCodeApi.PostalService do
  @moduledoc """
  Core postal code search service implementing the four-tier search strategy:
  1. Exact search with original parameters
  2. Polish character normalization search
  3. Fallback logic (house_number → street → city-only)
  4. Polish normalization fallback logic
  """

  alias PostalCodeApi.Database
  alias PostalCodeApi.PolishNormalizer
  alias PostalCodeApi.HouseNumberMatcher

  @doc """
  Build a search query with the given parameters.
  """
  def build_search_query(params, use_normalized \\ false) do
    base_query = "SELECT * FROM postal_codes WHERE 1=1"
    conditions = []
    bind_params = []

    # Choose column names based on whether we're using normalized search
    city_col = if use_normalized, do: "city_normalized", else: "city"
    street_col = if use_normalized, do: "street_normalized", else: "street"

    {conditions, bind_params} = add_condition(conditions, bind_params, params[:city], "#{city_col} LIKE ? COLLATE NOCASE", fn city -> "#{city}%" end)
    {conditions, bind_params} = add_condition(conditions, bind_params, params[:street], "#{street_col} LIKE ? COLLATE NOCASE", fn street -> "%#{street}%" end)
    {conditions, bind_params} = add_condition(conditions, bind_params, params[:province], "province = ? COLLATE NOCASE")
    {conditions, bind_params} = add_condition(conditions, bind_params, params[:county], "county = ? COLLATE NOCASE")
    {conditions, bind_params} = add_condition(conditions, bind_params, params[:municipality], "municipality = ? COLLATE NOCASE")

    # Use a larger limit since we'll filter in Elixir
    limit = params[:limit] || 100
    sql_limit = if params[:house_number], do: min(limit * 5, 1000), else: limit

    query = base_query <> " " <> Enum.join(conditions, " ") <> " LIMIT ?"
    bind_params = bind_params ++ [sql_limit]

    {query, bind_params}
  end

  defp add_condition(conditions, bind_params, value, condition_template, transform_fn \\ nil)

  defp add_condition(conditions, bind_params, nil, _condition_template, _transform_fn) do
    {conditions, bind_params}
  end

  defp add_condition(conditions, bind_params, "", _condition_template, _transform_fn) do
    {conditions, bind_params}
  end

  defp add_condition(conditions, bind_params, value, condition_template, transform_fn) do
    condition = "AND #{condition_template}"
    param = if transform_fn, do: transform_fn.(value), else: value
    {conditions ++ [condition], bind_params ++ [param]}
  end

  @doc """
  Filter database results by house number using the range matching logic.
  """
  def filter_by_house_number(results, nil, limit) do
    Enum.take(results, limit)
  end

  def filter_by_house_number(results, "", limit) do
    Enum.take(results, limit)
  end

  def filter_by_house_number(results, house_number, limit) do
    results
    |> Enum.reduce_while([], fn row, acc ->
      house_numbers = Map.get(row, :house_numbers)

      # Records without house_numbers don't match specific house number searches
      if house_numbers && house_numbers != "" do
        if HouseNumberMatcher.is_house_number_in_range(house_number, house_numbers) do
          new_acc = [row | acc]
          if length(new_acc) >= limit do
            {:halt, new_acc}
          else
            {:cont, new_acc}
          end
        else
          {:cont, acc}
        end
      else
        {:cont, acc}
      end
    end)
    |> Enum.reverse()
  end

  @doc """
  Execute fallback search logic when initial search returned no results.
  """
  def execute_fallback_search(params, use_normalized \\ false) do
    city = params[:city]
    street = params[:street]
    house_number = params[:house_number]
    province = params[:province]
    county = params[:county]
    municipality = params[:municipality]
    limit = params[:limit] || 100

    fallback_used = false
    fallback_message = ""
    results = []

    # Fallback 1: Remove house_number if present
    if house_number && house_number != "" do
      fallback_params = Map.put(params, :house_number, nil)
      {query, bind_params} = build_search_query(fallback_params, use_normalized)

      case Database.query(query, bind_params) do
        {:ok, db_results} when length(db_results) > 0 ->
          results = Enum.take(db_results, limit)
          fallback_used = true

          location_desc = []
          if street && street != "", do: location_desc = location_desc ++ ["street '#{street}'"]
          if city && city != "", do: location_desc = location_desc ++ ["city '#{city}'"]

          location_str = if length(location_desc) > 0 do
            " in " <> Enum.join(location_desc, " in ")
          else
            ""
          end

          fallback_message = "House number '#{house_number}' not found#{location_str}. Showing all results#{location_str}."

        _ ->
          :continue
      end
    end

    # Fallback 2: Remove street if still no results and we have city + street
    if length(results) == 0 && city && city != "" && street && street != "" do
      fallback_params = params |> Map.put(:street, nil) |> Map.put(:house_number, nil)
      {query, bind_params} = build_search_query(fallback_params, use_normalized)

      case Database.query(query, bind_params) do
        {:ok, db_results} when length(db_results) > 0 ->
          results = Enum.take(db_results, limit)
          fallback_used = true

          if house_number && house_number != "" do
            fallback_message = "Street '#{street}' with house number '#{house_number}' not found in #{city}. Showing all results for #{city}."
          else
            fallback_message = "Street '#{street}' not found in #{city}. Showing all results for #{city}."
          end

        _ ->
          :continue
      end
    end

    {results, fallback_used, fallback_message}
  end

  @doc """
  Search postal codes with four-tier approach: exact, Polish normalization, fallbacks, then Polish fallbacks.
  """
  def search_postal_codes(params) do
    # Pre-calculate normalized parameters once
    normalized_params = PolishNormalizer.get_normalized_search_params(params)

    polish_fallback_used = false
    search_type = "exact"
    fallback_used = false
    fallback_message = ""

    # Tier 1: Exact search with original parameters
    {query, bind_params} = build_search_query(params)

    case Database.query(query, bind_params) do
      {:ok, sql_results} ->
        exact_results = filter_by_house_number(sql_results, params[:house_number], params[:limit] || 100)

        results = if length(exact_results) > 0 do
          exact_results
        else
          # Tier 2: Polish character normalization search
          {norm_query, norm_bind_params} = build_search_query(normalized_params, true)

          case Database.query(norm_query, norm_bind_params) do
            {:ok, norm_sql_results} ->
              polish_results = filter_by_house_number(norm_sql_results, normalized_params[:house_number], normalized_params[:limit])

              if length(polish_results) > 0 do
                polish_fallback_used = true
                search_type = "polish_characters"
                polish_results
              else
                # Tier 3: Original fallback logic
                {fallback_results, tier3_fallback_used, tier3_message} = execute_fallback_search(params)

                if length(fallback_results) > 0 do
                  fallback_used = tier3_fallback_used
                  fallback_message = tier3_message
                  fallback_results
                else
                  # Tier 4: Polish normalization fallback logic
                  {tier4_results, tier4_fallback_used, tier4_message} = execute_fallback_search(normalized_params, true)

                  if length(tier4_results) > 0 do
                    fallback_used = tier4_fallback_used
                    fallback_message = tier4_message
                    polish_fallback_used = true
                    search_type = "polish_characters"
                    tier4_results
                  else
                    []
                  end
                end
              end

            {:error, _} ->
              []
          end
        end

        # Format results
        postal_codes = Enum.map(results, fn row ->
          %{
            postal_code: Map.get(row, :postal_code),
            city: Map.get(row, :city),
            street: Map.get(row, :street),
            house_numbers: Map.get(row, :house_numbers),
            municipality: Map.get(row, :municipality),
            county: Map.get(row, :county),
            province: Map.get(row, :province)
          }
        end)

        response = %{
          results: postal_codes,
          count: length(postal_codes),
          search_type: search_type
        }

        response = if fallback_used do
          response
          |> Map.put(:message, fallback_message)
          |> Map.put(:fallback_used, true)
        else
          response
        end

        response = if polish_fallback_used do
          message = if Map.has_key?(response, :message) do
            Map.get(response, :message) <> " Polish characters were normalized for search."
          else
            "Search performed with Polish character normalization."
          end

          response
          |> Map.put(:message, message)
          |> Map.put(:polish_normalization_used, true)
        else
          response
        end

        response

      {:error, _} ->
        %{results: [], count: 0, search_type: "exact"}
    end
  end

  @doc """
  Get postal code records by postal code.
  """
  def get_postal_code_by_code(postal_code) do
    query = "SELECT * FROM postal_codes WHERE postal_code = ?"

    case Database.query(query, [postal_code]) do
      {:ok, results} when length(results) > 0 ->
        postal_codes = Enum.map(results, fn row ->
          %{
            postal_code: Map.get(row, :postal_code),
            city: Map.get(row, :city),
            street: Map.get(row, :street),
            house_numbers: Map.get(row, :house_numbers),
            municipality: Map.get(row, :municipality),
            county: Map.get(row, :county),
            province: Map.get(row, :province)
          }
        end)

        %{results: postal_codes, count: length(postal_codes)}

      _ ->
        nil
    end
  end

  @doc """
  Get all provinces, optionally filtered by prefix.
  """
  def get_provinces(prefix \\ nil) do
    if prefix do
      # Get all provinces and filter with Polish character normalization
      query = "SELECT DISTINCT province FROM postal_codes WHERE province IS NOT NULL ORDER BY province"

      case Database.query(query) do
        {:ok, provinces} ->
          normalized_prefix = PolishNormalizer.normalize_polish_text(prefix) |> String.downcase()
          original_prefix = String.downcase(prefix)

          filtered_provinces = Enum.filter(provinces, fn row ->
            province = Map.get(row, :province)
            String.starts_with?(String.downcase(province), original_prefix) ||
            String.starts_with?(String.downcase(PolishNormalizer.normalize_polish_text(province)), normalized_prefix)
          end)

          %{
            provinces: Enum.map(filtered_provinces, &Map.get(&1, :province)),
            count: length(filtered_provinces),
            filtered_by_prefix: prefix
          }

        {:error, _} ->
          %{provinces: [], count: 0, filtered_by_prefix: prefix}
      end
    else
      query = "SELECT DISTINCT province FROM postal_codes WHERE province IS NOT NULL ORDER BY province"

      case Database.query(query) do
        {:ok, provinces} ->
          %{
            provinces: Enum.map(provinces, &Map.get(&1, :province)),
            count: length(provinces),
            filtered_by_prefix: nil
          }

        {:error, _} ->
          %{provinces: [], count: 0, filtered_by_prefix: nil}
      end
    end
  end

  @doc """
  Get counties, optionally filtered by province and/or prefix.
  """
  def get_counties(province \\ nil, prefix \\ nil) do
    base_query = "SELECT DISTINCT county FROM postal_codes WHERE county IS NOT NULL"
    conditions = []
    bind_params = []

    {conditions, bind_params} = add_condition(conditions, bind_params, province, "province = ? COLLATE NOCASE")

    query = base_query <> " " <> Enum.join(conditions, " ") <> " ORDER BY county"

    case Database.query(query, bind_params) do
      {:ok, counties} ->
        filtered_counties = if prefix do
          normalized_prefix = PolishNormalizer.normalize_polish_text(prefix) |> String.downcase()
          original_prefix = String.downcase(prefix)

          Enum.filter(counties, fn row ->
            county = Map.get(row, :county)
            String.starts_with?(String.downcase(county), original_prefix) ||
            String.starts_with?(String.downcase(PolishNormalizer.normalize_polish_text(county)), normalized_prefix)
          end)
        else
          counties
        end

        %{
          counties: Enum.map(filtered_counties, &Map.get(&1, :county)),
          count: length(filtered_counties),
          filtered_by_province: province,
          filtered_by_prefix: prefix
        }

      {:error, _} ->
        %{counties: [], count: 0, filtered_by_province: province, filtered_by_prefix: prefix}
    end
  end

  @doc """
  Get municipalities, optionally filtered by province, county, and/or prefix.
  """
  def get_municipalities(province \\ nil, county \\ nil, prefix \\ nil) do
    base_query = "SELECT DISTINCT municipality FROM postal_codes WHERE municipality IS NOT NULL"
    conditions = []
    bind_params = []

    {conditions, bind_params} = add_condition(conditions, bind_params, province, "province = ? COLLATE NOCASE")
    {conditions, bind_params} = add_condition(conditions, bind_params, county, "county = ? COLLATE NOCASE")

    query = base_query <> " " <> Enum.join(conditions, " ") <> " ORDER BY municipality"

    case Database.query(query, bind_params) do
      {:ok, municipalities} ->
        filtered_municipalities = if prefix do
          normalized_prefix = PolishNormalizer.normalize_polish_text(prefix) |> String.downcase()
          original_prefix = String.downcase(prefix)

          Enum.filter(municipalities, fn row ->
            municipality = Map.get(row, :municipality)
            String.starts_with?(String.downcase(municipality), original_prefix) ||
            String.starts_with?(String.downcase(PolishNormalizer.normalize_polish_text(municipality)), normalized_prefix)
          end)
        else
          municipalities
        end

        %{
          municipalities: Enum.map(filtered_municipalities, &Map.get(&1, :municipality)),
          count: length(filtered_municipalities),
          filtered_by_province: province,
          filtered_by_county: county,
          filtered_by_prefix: prefix
        }

      {:error, _} ->
        %{municipalities: [], count: 0, filtered_by_province: province, filtered_by_county: county, filtered_by_prefix: prefix}
    end
  end

  @doc """
  Get cities, optionally filtered by province, county, municipality, and/or prefix.
  """
  def get_cities(province \\ nil, county \\ nil, municipality \\ nil, prefix \\ nil) do
    base_query = "SELECT DISTINCT city FROM postal_codes WHERE city IS NOT NULL"
    conditions = []
    bind_params = []

    {conditions, bind_params} = add_condition(conditions, bind_params, province, "province = ? COLLATE NOCASE")
    {conditions, bind_params} = add_condition(conditions, bind_params, county, "county = ? COLLATE NOCASE")
    {conditions, bind_params} = add_condition(conditions, bind_params, municipality, "municipality = ? COLLATE NOCASE")

    {conditions, bind_params} = if prefix do
      normalized_prefix = PolishNormalizer.normalize_polish_text(prefix)
      condition = "AND (city LIKE ? COLLATE NOCASE OR city_normalized LIKE ? COLLATE NOCASE)"
      {conditions ++ [condition], bind_params ++ ["#{prefix}%", "#{normalized_prefix}%"]}
    else
      {conditions, bind_params}
    end

    query = base_query <> " " <> Enum.join(conditions, " ") <> " ORDER BY city"

    case Database.query(query, bind_params) do
      {:ok, cities} ->
        %{
          cities: Enum.map(cities, &Map.get(&1, :city)),
          count: length(cities),
          filtered_by_province: province,
          filtered_by_county: county,
          filtered_by_municipality: municipality,
          filtered_by_prefix: prefix
        }

      {:error, _} ->
        %{cities: [], count: 0, filtered_by_province: province, filtered_by_county: county, filtered_by_municipality: municipality, filtered_by_prefix: prefix}
    end
  end

  @doc """
  Get streets, optionally filtered by city, province, county, municipality, and/or prefix.
  """
  def get_streets(city \\ nil, province \\ nil, county \\ nil, municipality \\ nil, prefix \\ nil) do
    base_query = "SELECT DISTINCT street FROM postal_codes WHERE street IS NOT NULL AND street != ''"
    conditions = []
    bind_params = []

    {conditions, bind_params} = add_condition(conditions, bind_params, city, "city = ? COLLATE NOCASE")
    {conditions, bind_params} = add_condition(conditions, bind_params, province, "province = ? COLLATE NOCASE")
    {conditions, bind_params} = add_condition(conditions, bind_params, county, "county = ? COLLATE NOCASE")
    {conditions, bind_params} = add_condition(conditions, bind_params, municipality, "municipality = ? COLLATE NOCASE")

    {conditions, bind_params} = if prefix do
      normalized_prefix = PolishNormalizer.normalize_polish_text(prefix)
      condition = "AND (street LIKE ? COLLATE NOCASE OR street_normalized LIKE ? COLLATE NOCASE)"
      {conditions ++ [condition], bind_params ++ ["#{prefix}%", "#{normalized_prefix}%"]}
    else
      {conditions, bind_params}
    end

    query = base_query <> " " <> Enum.join(conditions, " ") <> " ORDER BY street"

    case Database.query(query, bind_params) do
      {:ok, streets} ->
        %{
          streets: Enum.map(streets, &Map.get(&1, :street)),
          count: length(streets),
          filtered_by_city: city,
          filtered_by_province: province,
          filtered_by_county: county,
          filtered_by_municipality: municipality,
          filtered_by_prefix: prefix
        }

      {:error, _} ->
        %{streets: [], count: 0, filtered_by_city: city, filtered_by_province: province, filtered_by_county: county, filtered_by_municipality: municipality, filtered_by_prefix: prefix}
    end
  end
end