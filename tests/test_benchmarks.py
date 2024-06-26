import pytest

from bowtie._connectables import Connectable, UnknownConnector
from bowtie._containers import (
    IMAGE_REPOSITORY,
    ConnectableContainer,
    ConnectableImage,
)
from bowtie._direct_connectable import Direct, NoDirectConnection

validators = Direct.from_id("python-jsonschema").registry()
validator = validators.for_uri("tag:bowtie.report,2024:benchmark_report")
validated, invalidated = validator.validated, validator.invalidated


# validator = validator_registry().for_uri(
#     "tag:bowtie.report,2024:benchmarks",
# )
# benchmark_report_validator = validator_registry().for_uri(
#     "tag:bowtie.report,2024:benchmark_report",
# )


#
#
# def test_valid_benchmark_files():
#     bowtie_dir = Path(__file__).parent.parent.joinpath("bowtie")
#     benchmark_dir = bowtie_dir.joinpath("benchmarks").iterdir()
#
#     desired_extensions = {".json", ".py"}
#     other_files = (
#         file
#         for file in benchmark_dir
#         if file.is_file() and file.suffix not in desired_extensions and file.name != "__pycache__"
#     )
#
#     assert not any(other_files)
#
#
# def test_validate_benchmarks():
#     default_benchmarks = get_default_benchmarks()
#     for benchmark in default_benchmarks:
#         validator.validate(benchmark)

def test_validate_benchmark_report():
    report = {
  "metadata": {
    "implementations": {
      "python-jsonschema": {
        "name": "jsonschema",
        "language": "python",
        "homepage": "https://python-jsonschema.readthedocs.io/",
        "issues": "https://github.com/python-jsonschema/jsonschema/issues",
        "source": "https://github.com/python-jsonschema/jsonschema",
        "dialects": [
          "https://json-schema.org/draft/2020-12/schema",
          "https://json-schema.org/draft/2019-09/schema",
          "http://json-schema.org/draft-07/schema#",
          "http://json-schema.org/draft-06/schema#",
          "http://json-schema.org/draft-04/schema#",
          "http://json-schema.org/draft-03/schema#"
        ],
        "version": "4.22.0",
        "language_version": "3.12.1",
        "os": "Darwin",
        "os_version": "23.1.0",
        "documentation": "https://python-jsonschema.readthedocs.io/",
        "links": []
      }
    },
    "num_runs": 1,
    "num_values": 2,
    "num_warmups": 1,
    "num_loops": 1,
    "system_metadata": {
      "boot_time": "2024-06-18 21:27:52",
      "command_max_rss": 52740096,
      "cpu_count": 8,
      "date": "2024-06-25 13:39:33.801948",
      "duration": 0.909597791993292,
      "hostname": "Jarviss-MacBook-Air.local",
      "load_avg_1min": 3.65234375,
      "loops": 1,
      "perf_version": "2.7.0",
      "platform": "macOS-14.1.2-arm64-arm-64bit",
      "unit": "second",
      "uptime": 576701.8089289665
    },
    "bowtie_version": "0.1.dev4796+g397733e.d20240623",
    "dialect": "https://json-schema.org/draft/2020-12/schema",
    "started": "2024-06-25T08:09:32.820116+00:00"
  },
  "results": [
    {
      "name": "contains",
      "description": "A benchmark for validation of the `contains` keyword.",
      "benchmark_results": [
        {
          "name": "Array Size - 1000",
          "description": "Validating contains keyword over an array of size 1000",
          "test_results": [
            {
              "description": "Empty array",
              "connectable_results": [
                {
                  "connectable_id": "python-jsonschema",
                  "duration": 0.909597791993292,
                  "values": [
                    0.3537296669965144,
                    0.24272454201127402
                  ]
                }
              ]
            },
            {
              "description": "Beginning of array",
              "connectable_results": [
                {
                  "connectable_id": "python-jsonschema",
                  "duration": 0.7289082090137526,
                  "values": [
                    0.2146655840042513,
                    0.22045312498812564
                  ]
                }
              ]
            },
            {
              "description": "Middle of array",
              "connectable_results": [
                {
                  "connectable_id": "python-jsonschema",
                  "duration": 0.7137991659983527,
                  "values": [
                    0.20859033399028704,
                    0.21103683300316334
                  ]
                }
              ]
            },
            {
              "description": "End of array",
              "connectable_results": [
                {
                  "connectable_id": "python-jsonschema",
                  "duration": 0.7049916250107344,
                  "values": [
                    0.2090633329935372,
                    0.20787358298548497
                  ]
                }
              ]
            },
            {
              "description": "Invalid array",
              "connectable_results": [
                {
                  "connectable_id": "python-jsonschema",
                  "duration": 0.7158431250136346,
                  "values": [
                    0.21100904198829085,
                    0.21038779101218097
                  ]
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "name": "additionalProperties",
      "description": "A benchmark for measuring performance of the implementation for the additionalProperties keyword.",
      "benchmark_results": [
        {
          "name": "Array Size - 1000",
          "description": "Validating additionalProperties keyword over array of size 1000",
          "test_results": [
            {
              "description": "Invalid at first",
              "connectable_results": [
                {
                  "connectable_id": "python-jsonschema",
                  "duration": 0.7399219170038123,
                  "values": [
                    0.21695162501418963,
                    0.21826429100474343
                  ]
                }
              ]
            },
            {
              "description": "Invalid at middle",
              "connectable_results": [
                {
                  "connectable_id": "python-jsonschema",
                  "duration": 0.7381954579905141,
                  "values": [
                    0.219998000015039,
                    0.2151722080016043
                  ]
                }
              ]
            },
            {
              "description": "Invalid at last",
              "connectable_results": [
                {
                  "connectable_id": "python-jsonschema",
                  "duration": 0.7335538750048727,
                  "values": [
                    0.2154197500203736,
                    0.21393262498895638
                  ]
                }
              ]
            },
            {
              "description": "Valid",
              "connectable_results": [
                {
                  "connectable_id": "python-jsonschema",
                  "duration": 0.7229475410131272,
                  "values": [
                    0.21429562498815358,
                    0.21369266699184664
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
    validated(report)
