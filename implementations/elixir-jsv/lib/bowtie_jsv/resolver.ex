defmodule BowtieJSV.Resolver do
  alias JSV.Resolver.Embedded
  @behaviour JSV.Resolver

  @impl true
  def resolve(uri, opts) do
    registry = make_registry(opts)

    case registry do
      %{^uri => schema} ->
        BowtieJSV.debug(["resolving from registry: ", uri])
        {:ok, schema}

      _ ->
        BowtieJSV.debug(["resolving from embedded: ", uri])
        Embedded.resolve(uri, [])
    end
  end

  defp make_registry(opts) do
    case Keyword.get(opts, :registry) do
      nil -> %{}
      map -> map
    end
  end
end
