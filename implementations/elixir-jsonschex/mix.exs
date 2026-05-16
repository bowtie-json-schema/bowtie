defmodule BowtieJSONSchex.MixProject do
  use Mix.Project

  def project do
    [
      app: :bowtie_jsonschex,
      version: "0.1.0",
      elixir: "~> 1.17",
      start_permanent: Mix.env() == :prod,
      deps: deps(),
      escript: [
        main_module: BowtieJSONSchex,
        name: "bowtie_jsonschex",
        include_priv_for: [:jsonschex]
      ]
    ]
  end


  def application do
    [
      extra_applications: [:logger]
    ]
  end


  defp deps do
    [
      {:jsonschex, "~> 0.5"},
      {:idna, "~> 7.1"},
      {:decimal, "~> 3.0"}
    ]
  end
end
