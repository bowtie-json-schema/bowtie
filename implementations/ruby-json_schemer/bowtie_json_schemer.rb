# frozen_string_literal: true

require 'json'
require 'json_schemer'

$stdout.sync = true

class WrongVersion < StandardError
end

class NotStarted < StandardError
end

# Bowtie implementation for json_schemer
module BowtieJsonSchemer
  @started = false
  @draft = nil

  ARGF.each_line do |line|  # rubocop:disable Metrics/BlockLength
    request = JSON.parse(line)
    case request['cmd']
    when 'start'
      raise WrongVersion if request['version'] != 1

      @started = true
      response = {
        ready: true,
        version: 1,
        implementation: {
          language: :ruby,
          name: :json_schemer,
          homepage: 'https://github.com/davishmcclurg/json_schemer',
          issues: 'https://github.com/davishmcclurg/json_schemer/issues',

          dialects: [
            'http://json-schema.org/draft-07/schema#',
            'http://json-schema.org/draft-06/schema#',
            'http://json-schema.org/draft-04/schema#',
          ],
        },
      }
      puts "#{JSON.generate(response)}\n"
    when 'dialect'
      raise NotStarted unless @started

      @draft = JSONSchemer::DRAFT_CLASS_BY_META_SCHEMA[request['dialect']]
      response = { ok: true }
      puts "#{JSON.generate(response)}\n"
    when 'run'
      raise NotStarted unless @started

      schemer = @draft.new(
        request['case']['schema'],
        ref_resolver: proc { |uri| request['case']['registry'][uri.to_s] },
      )
      response = {
        seq: request['seq'],
        results: request['case']['tests'].map do |test|
          { valid: schemer.valid?(test['instance']) }
        end,
      }
      puts "#{JSON.generate(response)}\n"
    when 'stop'
      raise NotStarted unless @started

      exit(0)
    end
  end
end
