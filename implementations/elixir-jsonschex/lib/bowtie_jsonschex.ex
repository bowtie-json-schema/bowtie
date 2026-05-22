defmodule BowtieJSONSchex do

  @dialects [
    "https://json-schema.org/draft/2020-12/schema"
  ]

  def main(_argv), do: run()
  def run() do
    debug("starting")

    IO.stream(:stdio, :line)
    |> Stream.each(&debug(&1, "[input]"))
    |> Stream.transform(init(), fn input, state ->
      {output, state} = loop(input, state)
      {[output], state}
    end)
    |> Stream.map(&JSON.encode!/1)
    |> Stream.each(&debug(&1, "[output]"))
    |> Enum.each(&IO.puts/1)
  end

  def init, do: %{default_dialect: hd(@dialects)}

  defp loop(line, state) do
    {:reply, resp, state} = handle_raw_command(line, state)

    {resp, state}
  rescue
    e ->
      {errored(e, __STACKTRACE__), state}
  end


  def debug(msg) do
    if debug?() do
      IO.puts(:stderr, msg)
    end

    if log?() do
      log_to_file(msg)
    end

    :ok
  end

  def debug(value, label) do
    if debug?() do
      IO.inspect(:stderr, value, label: label)
    end

    if log?() do
      log_to_file([label, ": ", inspect(value)])
    end

    :ok
  end

  defp log_to_file(msg) do
    msg =
      msg
      |> List.wrap()
      |> Enum.map(&to_string/1)

    File.write!("/var/log/jsonschex/debug.log", [msg, "\n"], [:append])
  end

  defp debug?, do: System.get_env("JSONSCHEX_DEBUG") == "true"
  defp log?, do: System.get_env("JSONSCHEX_LOG") == "true"

  defp handle_raw_command(json, state) do
    json
    |> JSON.decode!()
    |> handle_command(state)
  end

  defp handle_command(%{"cmd" => "start", "version" => 1}, state) do
    {:reply, start_response(), state}
  end

  defp handle_command(%{"cmd" => "start"}, state) do
    {:reply,
     %{
       errored: true,
       context: %{
         message: "Unsupported protocol version"
       }
     }, state}
  end

  defp handle_command(%{"cmd" => "stop"}, _state) do
    System.halt(0)
  end

  defp handle_command(%{"cmd" => "dialect", "dialect" => dialect}, state) do
    {:reply, %{ok: true}, Map.put(state, :default_dialect, dialect)}
  end

  defp handle_command(%{"cmd" => "run", "seq" => tseq, "case" => tcase}, state) do
    %{"schema" => raw_schema, "tests" => tests} = tcase
    registry = Map.get(tcase, "registry", %{})
    debug(tcase, "tcase")

    root = build_schema(raw_schema, registry, state)
    results = Enum.map(tests, &run_test(&1, root))

    {:reply, %{seq: tseq, results: results}, state}
  rescue
    e ->
      {:reply, errored(e, __STACKTRACE__, %{seq: tseq}), state}
  end

  defp handle_command(command, state) do
    {:reply,
     %{
       errored: true,
       context: %{
         message: "Unsupported command",
         command: command
       }
     }, state}
  end

  defp build_schema(raw_schema, registry, state) do
    loader = build_loader(registry)

    opts =
      [external_loader: loader]
      |> maybe_put_default_dialect(state)

    case JSONSchex.compile(raw_schema, opts) do
      {:ok, schema} -> schema
      {:error, err} -> raise "Compile error: #{JSONSchex.format_error(err)}"
    end
  end

  defp build_loader(registry) do
    registry = registry || %{}

    fn uri ->
      base_uri =
        uri
        |> to_string()
        |> String.split("#")
        |> List.first()

      Map.fetch(registry, base_uri)
    end
  end

  defp maybe_put_default_dialect(opts, %{default_dialect: dialect}),
    do: Keyword.put(opts, :default_meta, dialect)

  defp run_test(test, root) do
    %{"instance" => data} = test

    case JSONSchex.validate(root, data) do
      :ok -> %{valid: true}
      {:error, _errors} -> %{valid: false}
    end
  rescue
    e -> errored(e, __STACKTRACE__)
  end

  defp start_response() do
    %{
      version: 1,
      implementation: %{
        language: "elixir",
        name: "jsonschex",
        version: jsonschex_vsn(),
        dialects: @dialects,
        documentation: "https://hexdocs.pm/jsonschex/",
        homepage: "https://github.com/xinz/jsonschex",
        issues: "https://github.com/xinz/jsonschex/issues",
        source: "https://github.com/xinz/jsonschex"
      }
    }
  end

  defp jsonschex_vsn do
    {:ok, vsn} = :application.get_key(:jsonschex, :vsn)
    List.to_string(vsn)
  end

  defp errored(e, stacktrace, additional_data \\ %{}) do
    errored_payload = %{
      errored: true,
      context: %{
        message: Exception.message(e),
        traceback: Exception.format_stacktrace(stacktrace) |> to_string()
      }
    }

    Map.merge(errored_payload, additional_data)
  end
end
