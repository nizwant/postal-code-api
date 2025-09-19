defmodule PostalCodeApi.Database do
  @moduledoc """
  Database connection manager for SQLite postal codes database.
  Simple implementation using system sqlite3 command.
  """

  use GenServer
  require Logger

  @db_path "../postal_codes.db"

  def start_link(_) do
    GenServer.start_link(__MODULE__, nil, name: __MODULE__)
  end

  def init(_) do
    case validate_database() do
      :ok ->
        Logger.info("Database validation successful")
        {:ok, nil}
      {:error, reason} ->
        Logger.error("Database validation failed: #{reason}")
        {:stop, reason}
    end
  end

  @doc """
  Execute a query with parameters.
  """
  def query(sql, params \\ []) do
    GenServer.call(__MODULE__, {:query, sql, params})
  end

  def handle_call({:query, sql, params}, _from, state) do
    # Replace ? with actual parameters (simple substitution)
    sql_with_params = replace_params(sql, params)

    # Execute query using system sqlite3 command
    case System.cmd("sqlite3", [@db_path, "-header", "-json", sql_with_params]) do
      {output, 0} ->
        case Jason.decode(output) do
          {:ok, results} when is_list(results) ->
            # Convert string keys to atoms for compatibility
            formatted_results = Enum.map(results, fn result ->
              result
              |> Enum.map(fn {k, v} -> {String.to_atom(k), v} end)
              |> Enum.into(%{})
            end)
            {:reply, {:ok, formatted_results}, state}
          {:ok, _} ->
            {:reply, {:ok, []}, state}
          {:error, reason} ->
            Logger.error("JSON decode failed: #{inspect(reason)}")
            {:reply, {:error, reason}, state}
        end
      {error_output, exit_code} ->
        Logger.error("Database query failed: #{error_output} (exit code: #{exit_code})")
        {:reply, {:error, "Database query failed: #{error_output}"}, state}
    end
  end

  defp replace_params(sql, []), do: sql
  defp replace_params(sql, params) do
    # Simple parameter replacement - replace ? with actual values
    # Note: This is a simplified approach for demonstration
    Enum.reduce(params, sql, fn param, acc ->
      escaped_param = escape_param(param)
      String.replace(acc, "?", escaped_param, global: false)
    end)
  end

  defp escape_param(param) when is_binary(param) do
    # Escape single quotes and wrap in quotes
    "'#{String.replace(param, "'", "''")}'"
  end
  defp escape_param(param) when is_integer(param), do: to_string(param)
  defp escape_param(param), do: "'#{param}'"

  defp validate_database do
    if File.exists?(@db_path) do
      case System.cmd("sqlite3", [@db_path, "SELECT COUNT(*) FROM postal_codes LIMIT 1;"]) do
        {output, 0} ->
          case String.trim(output) |> Integer.parse() do
            {count, _} when count > 0 ->
              :ok
            _ ->
              {:error, "Database exists but appears empty"}
          end
        {error_output, _} ->
          {:error, "Database connection failed: #{error_output}"}
      end
    else
      {:error, "Database file not found at #{@db_path}. Please run 'python create_db.py' from the project root."}
    end
  end
end