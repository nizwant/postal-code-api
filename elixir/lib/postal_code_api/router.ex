defmodule PostalCodeApi.Router do
  @moduledoc """
  HTTP router for the postal code API matching Flask/FastAPI/Go implementations.
  """

  use Plug.Router
  alias PostalCodeApi.PostalService

  plug :match
  plug Plug.Parsers, parsers: [:json], json_decoder: Jason
  plug :dispatch

  @doc """
  Trim whitespace from parameter value if it exists
  """
  defp trim_param(nil), do: nil
  defp trim_param(""), do: nil
  defp trim_param(value) when is_binary(value) do
    trimmed = String.trim(value)
    if trimmed == "", do: nil, else: trimmed
  end

  @doc """
  Extract query parameters and trim whitespace
  """
  defp extract_search_params(conn) do
    %{
      city: trim_param(conn.params["city"]),
      street: trim_param(conn.params["street"]),
      house_number: trim_param(conn.params["house_number"]),
      province: trim_param(conn.params["province"]),
      county: trim_param(conn.params["county"]),
      municipality: trim_param(conn.params["municipality"]),
      limit: parse_limit(conn.params["limit"])
    }
  end

  defp parse_limit(nil), do: 100
  defp parse_limit(""), do: 100
  defp parse_limit(limit_str) when is_binary(limit_str) do
    case Integer.parse(limit_str) do
      {limit, _} when limit > 0 -> limit
      _ -> 100
    end
  end
  defp parse_limit(limit) when is_integer(limit) and limit > 0, do: limit
  defp parse_limit(_), do: 100

  # Multi-parameter postal code search
  get "/postal-codes" do
    params = extract_search_params(conn)

    # City parameter is mandatory
    if is_nil(params[:city]) do
      conn
      |> put_resp_content_type("application/json")
      |> send_resp(400, Jason.encode!(%{error: "City parameter is required"}))
    else
      response = PostalService.search_postal_codes(params)

      conn
      |> put_resp_content_type("application/json")
      |> send_resp(200, Jason.encode!(response))
    end
  end

  # Direct postal code lookup
  get "/postal-codes/:postal_code" do
    case PostalService.get_postal_code_by_code(postal_code) do
      nil ->
        conn
        |> put_resp_content_type("application/json")
        |> send_resp(404, Jason.encode!(%{error: "Postal code not found"}))

      result ->
        conn
        |> put_resp_content_type("application/json")
        |> send_resp(200, Jason.encode!(result))
    end
  end

  # Location discovery endpoint
  get "/locations" do
    response = %{
      available_endpoints: %{
        provinces: "/locations/provinces",
        counties: "/locations/counties",
        municipalities: "/locations/municipalities",
        cities: "/locations/cities",
        streets: "/locations/streets"
      }
    }

    conn
    |> put_resp_content_type("application/json")
    |> send_resp(200, Jason.encode!(response))
  end

  # Get provinces
  get "/locations/provinces" do
    prefix = trim_param(conn.params["prefix"])
    response = PostalService.get_provinces(prefix)

    conn
    |> put_resp_content_type("application/json")
    |> send_resp(200, Jason.encode!(response))
  end

  # Get counties
  get "/locations/counties" do
    province = trim_param(conn.params["province"])
    prefix = trim_param(conn.params["prefix"])
    response = PostalService.get_counties(province, prefix)

    conn
    |> put_resp_content_type("application/json")
    |> send_resp(200, Jason.encode!(response))
  end

  # Get municipalities
  get "/locations/municipalities" do
    province = trim_param(conn.params["province"])
    county = trim_param(conn.params["county"])
    prefix = trim_param(conn.params["prefix"])
    response = PostalService.get_municipalities(province, county, prefix)

    conn
    |> put_resp_content_type("application/json")
    |> send_resp(200, Jason.encode!(response))
  end

  # Get cities
  get "/locations/cities" do
    province = trim_param(conn.params["province"])
    county = trim_param(conn.params["county"])
    municipality = trim_param(conn.params["municipality"])
    prefix = trim_param(conn.params["prefix"])
    response = PostalService.get_cities(province, county, municipality, prefix)

    conn
    |> put_resp_content_type("application/json")
    |> send_resp(200, Jason.encode!(response))
  end

  # Get streets
  get "/locations/streets" do
    city = trim_param(conn.params["city"])
    province = trim_param(conn.params["province"])
    county = trim_param(conn.params["county"])
    municipality = trim_param(conn.params["municipality"])
    prefix = trim_param(conn.params["prefix"])
    response = PostalService.get_streets(city, province, county, municipality, prefix)

    conn
    |> put_resp_content_type("application/json")
    |> send_resp(200, Jason.encode!(response))
  end

  # Health check endpoint
  get "/health" do
    conn
    |> put_resp_content_type("application/json")
    |> send_resp(200, Jason.encode!(%{status: "healthy"}))
  end

  # Catch-all for unmatched routes
  match _ do
    conn
    |> put_resp_content_type("application/json")
    |> send_resp(404, Jason.encode!(%{error: "Not found"}))
  end
end