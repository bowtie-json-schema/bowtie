defmodule BowtieJSV do
  @dialects [
    "http://json-schema.org/draft-07/schema#",
    "https://json-schema.org/draft/2020-12/schema"
  ]

  def main(_argv) do
    debug("starting")
    loop_lines(%{})
    debug("finished")
  end

  def debug(msg) do
    IO.puts(:stderr, msg)
  end

  def debug_value(value, label) do
    IO.inspect(:stderr, value, label: label)
  end

  defp loop_lines(state) do
    debug("loop")

    case IO.read(:stdio, :line) do
      :eof ->
        debug("EOF received")

      line ->
        {:reply, resp, state} = handle_raw_command(line, state)
        IO.puts(JSON.encode!(resp))
        loop_lines(state)
    end
  end

  defp handle_raw_command(json, state) do
    with {:ok, cmd} <- JSON.decode(json) do
      handle_command(cmd, state)
    end
  end

  defp handle_command(%{"cmd" => "start", "version" => 1}, state) do
    start_response = %{
      version: 1,
      implementation: %{
        language: "elixir",
        name: "jsv",
        source: "https://github.com/lud/jsv",
        homepage: "https://github.com/lud/jsv",
        issues: "https://github.com/lud/jsv/issues",
        dialects: @dialects
      }
    }

    {:reply, start_response, state}
  end

  defp handle_command(%{"cmd" => "stop"}, _state) do
    System.halt()
  end

  defp handle_command(%{"cmd" => "dialect", "dialect" => dialect}, state) do
    true = dialect in @dialects
    {:reply, %{ok: true}, Map.put(state, :default_dialect, dialect)}
  end

  defp handle_command(%{"cmd" => "run", "seq" => tseq, "case" => tcase}, state) do
    %{"schema" => raw_schema, "tests" => tests} = tcase
    registry = Map.get(tcase, "registry")
    debug_value(tcase, "tcase")

    root = build_schema(raw_schema, registry, state)

    results =
      Enum.map(tests, fn test ->
        %{"instance" => data} = test

        case JSV.validate(data, root) do
          {:ok, _} -> %{valid: true}
          {:error, verr} -> %{valid: false, output: JSV.normalize_error(verr)}
        end
      end)

    {:reply, %{seq: tseq, results: results}, state}
  end

  defp build_schema(raw_schema, registry, state) do
    JSV.build!(raw_schema,
      resolver: {BowtieJSV.Resolver, registry: registry},
      default_meta: state.default_dialect
    )
  end
end
