defmodule BowtieJSV.MixProject do
  use Mix.Project

  def project do
    [
      app: :bowtie_jsv,
      version: "0.1.0",
      elixir: "~> 1.17",
      start_permanent: Mix.env() == :prod,
      deps: deps(),
      escript: [main_module: BowtieJSV, name: "bowtie_jsv", include_priv_for: [:jsv]],
      releases: [
        bowtie_jsv: [
          include_executables_for: [:unix],
          include_erts: true
        ]
      ]
    ]
  end

  # Run "mix help compile.app" to learn about applications.
  def application do
    [
      extra_applications: [:logger],
      mod: {BowtieJSV.App, []}
    ]
  end

  # Run "mix help deps" to learn about dependencies.
  defp deps do
    [
      {:jsv, "~> 0.3"}
    ]
  end
end