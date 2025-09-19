defmodule PostalCodeApi.PolishNormalizer do
  @moduledoc """
  Polish Character Normalizer

  Utility for converting Polish diacritical characters to ASCII equivalents
  for user-friendly search functionality. Port of the Python implementation.
  """

  @polish_char_map %{
    # Lowercase Polish characters
    "ą" => "a",
    "ć" => "c",
    "ę" => "e",
    "ł" => "l",
    "ń" => "n",
    "ó" => "o",
    "ś" => "s",
    "ź" => "z",
    "ż" => "z",

    # Uppercase Polish characters
    "Ą" => "A",
    "Ć" => "C",
    "Ę" => "E",
    "Ł" => "L",
    "Ń" => "N",
    "Ó" => "O",
    "Ś" => "S",
    "Ź" => "Z",
    "Ż" => "Z"
  }

  @doc """
  Convert Polish characters to ASCII equivalents.

  ## Examples

      iex> PostalCodeApi.PolishNormalizer.normalize_polish_text("Łódź")
      "Lodz"

      iex> PostalCodeApi.PolishNormalizer.normalize_polish_text("Kraków")
      "Krakow"

      iex> PostalCodeApi.PolishNormalizer.normalize_polish_text(nil)
      nil
  """
  def normalize_polish_text(nil), do: nil
  def normalize_polish_text(""), do: ""

  def normalize_polish_text(text) when is_binary(text) do
    String.graphemes(text)
    |> Enum.map(fn char ->
      Map.get(@polish_char_map, char, char)
    end)
    |> Enum.join()
  end

  @doc """
  Normalize search parameters by converting Polish characters to ASCII equivalents.
  """
  def normalize_search_params(params) do
    params
    |> Enum.map(fn
      {key, value} when key in [:city, :street, :province, :county, :municipality] ->
        {key, normalize_polish_text(value)}
      {key, value} ->
        {key, value}
    end)
    |> Enum.into(%{})
  end

  @doc """
  Get normalized search parameters for Polish character fallback using database normalized columns.
  """
  def get_normalized_search_params(params) do
    %{
      city: normalize_polish_text(params[:city]),
      street: normalize_polish_text(params[:street]),
      province: normalize_polish_text(params[:province]),
      county: normalize_polish_text(params[:county]),
      municipality: normalize_polish_text(params[:municipality]),
      house_number: params[:house_number],
      limit: params[:limit] || 100
    }
  end

  @doc """
  Check if text contains Polish diacritical characters.

  ## Examples

      iex> PostalCodeApi.PolishNormalizer.has_polish_characters("Łódź")
      true

      iex> PostalCodeApi.PolishNormalizer.has_polish_characters("Warsaw")
      false
  """
  def has_polish_characters(nil), do: false
  def has_polish_characters(""), do: false

  def has_polish_characters(text) when is_binary(text) do
    polish_chars = MapSet.new(Map.keys(@polish_char_map))

    String.graphemes(text)
    |> Enum.any?(&MapSet.member?(polish_chars, &1))
  end
end