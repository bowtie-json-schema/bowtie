defmodule BowtieJSV.MixProject do
  use Mix.Project

  def project do
    [
      app: :bowtie_jsv,
      version: "0.1.0",
      elixir: "~> 1.17",
      start_permanent: Mix.env() == :prod,
      deps: deps(),
      escript: [
        main_module: BowtieJSV,
        name: "bowtie_jsv",
        include_priv_for: [:jsv]
      ]
    ]
  end

  # Run "mix help compile.app" to learn about applications.
  def application do
    [
      extra_applications: [:logger]
    ]
  end

  # Run "mix help deps" to learn about dependencies.
  defp deps do
    [
      {:jsv, "~> 0.7"}
    ]
  end
end
