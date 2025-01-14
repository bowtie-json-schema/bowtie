defmodule BowtieJSV do
  @dialects [
    "http://json-schema.org/draft-07/schema#",
    "https://json-schema.org/draft/2020-12/schema"
  ]

  def run() do
    debug("starting")
    loop_lines(%{})
    debug("finished")
  end

  def debug(msg) do
    IO.puts(:stderr, msg)
  end

  def debug(value, label) do
    IO.inspect(:stderr, value, label: label)
  end

  defp loop_lines(state) do
    case IO.read(:stdio, :line) do
      :eof ->
        debug("EOF received")

      line ->
        {:reply, resp, state} = handle_raw_command(line, state)
        debug(resp, "resp")
        IO.puts(JSON.encode!(resp))
        loop_lines(state)
    end
  end

  defp handle_raw_command(json, state) do
    cmd = JSON.decode!(json)
    handle_command(cmd, state)
  end

  defp handle_command(%{"cmd" => "start", "version" => 1}, state) do
    {:reply, start_response(), state}
  end

  defp handle_command(%{"cmd" => "stop"}, _state) do
    System.halt()
  end

  defp handle_command(%{"cmd" => "dialect", "dialect" => dialect}, state) do
    {:reply, %{ok: true}, Map.put(state, :default_dialect, dialect)}
  end

  defp handle_command(%{"cmd" => "run", "seq" => tseq, "case" => tcase}, state) do
    %{"schema" => raw_schema, "tests" => tests} = tcase
    registry = Map.get(tcase, "registry")
    debug(tcase, "tcase")

    root = build_schema(raw_schema, registry, state)

    results = Enum.map(tests, fn test -> run_test(test, root) end)

    {:reply, %{seq: tseq, results: results}, state}
  rescue
    e -> {:reply, %{
      errored: true,
      seq: tseq,
      message: Exception.message(e),
      traceback: Exception.format_stacktrace(__STACKTRACE__),
    }, state}
  end

  defp build_schema(raw_schema, registry, state) do
    JSV.build!(raw_schema,
      resolver: {BowtieJSV.Resolver, registry: registry},
      default_meta: state.default_dialect
    )
  end

  defp run_test(test, root) do
    %{"instance" => data} = test

    case JSV.validate(data, root) do
      {:ok, _} -> %{valid: true}
      {:error, _} -> %{valid: false}
    end
  end

  defp start_response do
    %{
      version: 1,
      implementation: %{
        language: "elixir",
        name: "jsv",
        version: jsv_vsn(),
        dialects: @dialects,
        documentation: "https://hexdocs.pm/jsv/",
        homepage: "https://github.com/lud/jsv",
        issues: "https://github.com/lud/jsv/issues",
        source: "https://github.com/lud/jsv"
      }
    }
  end

  defp jsv_vsn do
    {:ok, jsv_vsn} = :application.get_key(:jsv, :vsn)
    List.to_string(jsv_vsn)
  end
end
