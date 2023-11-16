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
  @meta_schema = nil
  @meta_schema_refs = {
    JSONSchemer::Draft202012::BASE_URI => JSONSchemer::Draft202012::SCHEMA,
    JSONSchemer::Draft201909::BASE_URI => JSONSchemer::Draft201909::SCHEMA,
    JSONSchemer::Draft7::BASE_URI => JSONSchemer::Draft7::SCHEMA,
    JSONSchemer::Draft6::BASE_URI => JSONSchemer::Draft6::SCHEMA,
    JSONSchemer::Draft4::BASE_URI => JSONSchemer::Draft4::SCHEMA,
  }
  @meta_schema_refs.merge!(JSONSchemer::Draft202012::Meta::SCHEMAS)
  @meta_schema_refs.merge!(JSONSchemer::Draft201909::Meta::SCHEMAS)
  @meta_schema_refs.transform_keys! { |uri| uri.dup.tap { _1.fragment = nil } }

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
          version: Gem::Specification.find_by_name('json_schemer').version,
          homepage: 'https://github.com/davishmcclurg/json_schemer',
          issues: 'https://github.com/davishmcclurg/json_schemer/issues',

          dialects: [
            'https://json-schema.org/draft/2020-12/schema',
            'https://json-schema.org/draft/2019-09/schema',
            'http://json-schema.org/draft-07/schema#',
            'http://json-schema.org/draft-06/schema#',
            'http://json-schema.org/draft-04/schema#',
          ],
        },
      }
      puts "#{JSON.generate(response)}\n"
    when 'dialect'
      raise NotStarted unless @started

      @meta_schema = JSONSchemer::META_SCHEMAS_BY_BASE_URI_STR[request['dialect']]
      response = { ok: true }
      puts "#{JSON.generate(response)}\n"
    when 'run'
      raise NotStarted unless @started

      schemer = JSONSchemer.schema(
        request['case']['schema'],
        meta_schema: @meta_schema,
        format: false,
        regexp_resolver: 'ecma',
        ref_resolver: proc do |uri|
          request.dig('case', 'registry', uri.to_s) || @meta_schema_refs[uri]
        end,
      )
      begin
        response = {
          seq: request['seq'],
          results: request['case']['tests'].map do |test|
            { valid: schemer.valid?(test['instance']) }
          end,
        }
      rescue StandardError => e
        response = {
          seq: request['seq'],
          errored: true,
          context: {
            traceback: e.backtrace.join('\n'),
          },
        }
      end
      puts "#{JSON.generate(response)}\n"
    when 'stop'
      raise NotStarted unless @started

      exit(0)
    end
  end
end
