# frozen_string_literal: true

require 'json'
require 'json_schemer'

$stdout.sync = true

class UnsupportedCommand < StandardError; end
class UnsupportedVersion < StandardError; end
class UnsupportedDialect < StandardError; end

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

ARGF.each_line do |line| # rubocop:disable Metrics/BlockLength
  request = JSON.parse(line)
  cmd = request.fetch('cmd')

  response = case cmd
  when 'start'
    version = request.fetch('version')
    raise UnsupportedVersion, version unless version == 1

    {
      version: version,
      implementation: {
        language: :ruby,
        name: :json_schemer,
        version: Gem::Specification.find_by_name('json_schemer').version,
        homepage: 'https://github.com/davishmcclurg/json_schemer',
        issues: 'https://github.com/davishmcclurg/json_schemer/issues',
        source: 'https://github.com/davishmcclurg/json_schemer',

        dialects: [
          'https://json-schema.org/draft/2020-12/schema',
          'https://json-schema.org/draft/2019-09/schema',
          'http://json-schema.org/draft-07/schema#',
          'http://json-schema.org/draft-06/schema#',
          'http://json-schema.org/draft-04/schema#',
        ],
        os: RbConfig::CONFIG["host_os"],
        language_version: RUBY_VERSION
      },
    }
  when 'dialect'
    dialect = request.fetch('dialect')
    @meta_schema = JSONSchemer::META_SCHEMAS_BY_BASE_URI_STR[dialect]
    raise UnsupportedDialect, dialect unless @meta_schema

    { ok: true }
  when 'run'
    kase, seq = request.fetch_values('case', 'seq')

    begin
      schemer = JSONSchemer.schema(
        kase.fetch('schema'),
        meta_schema: @meta_schema,
        format: false,
        regexp_resolver: 'ecma',
        ref_resolver: proc do |uri|
          kase.dig('registry', uri.to_s) || @meta_schema_refs[uri]
        end,
      )

      {
        seq: seq,
        results: kase.fetch('tests').map do |test|
          { valid: schemer.valid?(test.fetch('instance')) }
        end,
      }
    rescue StandardError => e
      {
        seq: seq,
        errored: true,
        context: {
          message: e.message,
          traceback: e.backtrace.join('\n'),
        },
      }
    end
  when 'stop'
    exit(0)
  else
    raise UnsupportedCommand, cmd
  end

  $stdout.puts(JSON.generate(response))
end
