# frozen_string_literal: true

Gem::Specification.new do |spec|
  spec.name                  = 'bowtie_json_schemer'
  spec.version               = '2.0.0'
  spec.summary               = 'Bowtie + json_schemer'
  spec.authors               = ['Bowtie Authors']
  spec.required_ruby_version = '>= 3.0'

  spec.add_dependency 'json_schemer', '>= 2.0', '< 3.0'
end
