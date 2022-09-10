# frozen_string_literal: true

require 'json'
require 'json_schemer'

$stdout.sync = true

class WrongVersion < StandardError
end

class NotStarted < StandardError
end

module BowtieJsonSchemer

  started = false

  ARGF.each_line do |line|
    request = JSON.parse(line)
    case request["cmd"]
    when "start"
      raise WrongVersion if request["version"] != 1
      started = true
      response = {
        :ready => true,
        :version => 1,
        :implementation => {
          :language => :ruby,
          :name => :json_schemer,
          :homepage => "https://github.com/davishmcclurg/json_schemer",
          :issues => "https://github.com/davishmcclurg/json_schemer/issues",
        }
      }
      puts "#{JSON.generate(response)}\n"
    when "run"
      raise NotStarted if not started
      schemer = JSONSchemer.schema(request["case"]["schema"])
      response = {
        :seq => request["seq"],
        :results => request["case"]["tests"].map{ |test|
          {:valid => schemer.valid?(test["instance"]) }
        },
      }
      puts "#{JSON.generate(response)}\n"
    when "stop"
      raise NotStarted if not started
      exit(0)
    end
  end

end
