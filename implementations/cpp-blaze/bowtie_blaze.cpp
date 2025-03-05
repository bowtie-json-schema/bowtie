#include <sourcemeta/core/json.h>
#include <sourcemeta/core/jsonschema.h>

#include <sourcemeta/blaze/compiler.h>
#include <sourcemeta/blaze/evaluator.h>

#include <cassert>
#include <cstdlib>
#include <iostream>
#include <optional>
#include <string>
#include <utility>

int main() {
  using namespace sourcemeta::core;
  using namespace sourcemeta::blaze;
  bool started{false};
  std::optional<std::string> default_dialect{std::nullopt};
  sourcemeta::blaze::Evaluator evaluator;

  std::string line;
  while (std::getline(std::cin, line)) {
    const JSON message{parse_json(line)};

    assert(message.defines("cmd"));
    assert(message.at("cmd").is_string());

    const std::string command{message.at("cmd").to_string()};

    if (command == "start") {
      started = true;
      assert(message.defines("version") && message.at("version").is_integer());
      assert(message.at("version").to_integer() == 1);

      auto response{JSON::make_object()};
      response.assign("version", JSON{1});
      auto implementation{JSON::make_object()};
      implementation.assign("language", JSON{"c++"});
      implementation.assign("version", JSON{BLAZE_VERSION});
      implementation.assign("name", JSON{"blaze"});
      implementation.assign("homepage",
                            JSON{"https://github.com/sourcemeta/blaze"});
      implementation.assign("issues",
                            JSON{"https://github.com/sourcemeta/blaze/issues"});
      implementation.assign("source",
                            JSON{"https://github.com/sourcemeta/blaze"});
      implementation.assign(
          "dialects", JSON{JSON{"https://json-schema.org/draft/2020-12/schema"},
                           JSON{"https://json-schema.org/draft/2019-09/schema"},
                           JSON{"http://json-schema.org/draft-07/schema#"},
                           JSON{"http://json-schema.org/draft-06/schema#"},
                           JSON{"http://json-schema.org/draft-04/schema#"}});

      response.assign("implementation", std::move(implementation));
      stringify(response, std::cout);
      std::cout << std::endl;
    } else if (command == "dialect") {
      assert(started);
      assert(message.defines("dialect") && message.at("dialect").is_string());
      default_dialect = message.at("dialect").to_string();
      auto response{JSON::make_object()};
      response.assign("ok", JSON{true});
      stringify(response, std::cout);
      std::cout << std::endl;
    } else if (command == "run") {
      assert(started);
      assert(message.defines("seq"));
      assert(message.defines("case") && message.at("case").is_object());
      assert(message.at("case").defines("schema") &&
             is_schema(message.at("case").at("schema")));
      assert(message.at("case").defines("tests") &&
             message.at("case").at("tests").is_array());

      sourcemeta::core::SchemaMapResolver resolver{
          sourcemeta::core::schema_official_resolver};
      if (message.at("case").defines("registry")) {
        assert(message.at("case").at("registry").is_object());
        for (const auto &pair : message.at("case").at("registry").as_object()) {
          resolver.add(pair.second, default_dialect, pair.first);
        }
      }

      try {
        const auto schema_template{compile(
            message.at("case").at("schema"), schema_official_walker, resolver,
            default_schema_compiler, Mode::FastValidation, default_dialect)};

        auto response{JSON::make_object()};
        response.assign("seq", message.at("seq"));
        response.assign("results", JSON::make_array());

        for (const auto &test : message.at("case").at("tests").as_array()) {
          assert(test.defines("instance"));
          const bool valid{
              evaluator.validate(schema_template, test.at("instance"))};
          auto test_result{JSON::make_object()};
          test_result.assign("valid", JSON{valid});
          response.at("results").push_back(std::move(test_result));
        }

        stringify(response, std::cout);
        std::cout << std::endl;
      } catch (const std::exception &error) {
        auto response{JSON::make_object()};
        response.assign("errored", JSON{true});
        response.assign("context", JSON::make_object());
        response.at("context").assign("message", JSON{error.what()});
        stringify(response, std::cout);
        std::cout << std::endl;
      }
    } else if (command == "stop") {
      assert(started);
      return EXIT_SUCCESS;
    } else {
      std::cerr << "Unknown command: " << command << "\n";
      return EXIT_FAILURE;
    }
  }

  return EXIT_FAILURE;
}
