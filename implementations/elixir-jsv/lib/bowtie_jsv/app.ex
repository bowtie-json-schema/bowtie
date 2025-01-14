defmodule BowtieJSV.App do
  def start(_, _) do
    children = [{Task, fn -> BowtieJSV.run() end}]

    opts = [strategy: :one_for_one, name: BowtieJSV.Supervisor]
    Supervisor.start_link(children, opts)
  end
end
