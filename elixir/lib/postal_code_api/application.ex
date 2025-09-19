defmodule PostalCodeApi.Application do
  @moduledoc """
  The PostalCodeApi Application.
  """

  use Application

  @impl true
  def start(_type, _args) do
    children = [
      {PostalCodeApi.Database, []},
      {Plug.Cowboy, scheme: :http, plug: PostalCodeApi.Router, options: [port: 5004]}
    ]

    opts = [strategy: :one_for_one, name: PostalCodeApi.Supervisor]
    Supervisor.start_link(children, opts)
  end
end