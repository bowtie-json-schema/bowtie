#include <jsoncons/json.hpp>
#include <jsoncons_ext/jsonschema/jsonschema.hpp>

#include <cassert>
#include <cstdlib>
#include <iostream>
#include <optional>
#include <string>
#include <utility>

using namespace jsoncons;

int main() {
  bool started{false};

  jsonschema::evaluation_options options{};

  std::string line;
  while (std::getline(std::cin, line)) {
    const json message{json::parse(line)};

    assert(message.contains("cmd"));
    assert(message.at("cmd").is_string());

    const std::string command{message.at("cmd").as<std::string>()};

    if (command == "start") {
      // Validate protocol version
      started = true;
      assert(message.contains("version") && message.at("version").is_integer());
      assert(message.at("version").as<int64_t>() == 1);

      // Respond with implementation details
      json response;
      response["version"] = 1;

      json implementation;
      implementation["language"] = "c++";
      implementation["version"] = std::to_string(JSONCONS_VERSION_MAJOR) + "." +
                                  std::to_string(JSONCONS_VERSION_MINOR) + "." +
                                  std::to_string(JSONCONS_VERSION_PATCH);
      implementation["name"] = "jsoncons";
      implementation["homepage"] = "https://danielaparker.github.io/jsoncons/";
      implementation["issues"] =
          "https://github.com/danielaparker/jsoncons/issues";
      implementation["source"] = "https://github.com/danielaparker/jsoncons";

      json dialects(json_array_arg,
                    {"https://json-schema.org/draft/2020-12/schema",
                     "https://json-schema.org/draft/2019-09/schema",
                     "http://json-schema.org/draft-07/schema#",
                     "http://json-schema.org/draft-06/schema#",
                     "http://json-schema.org/draft-04/schema#"});
      implementation["dialects"] = std::move(dialects);

      response["implementation"] = std::move(implementation);

      std::cout << print(response) << std::endl;
    } else if (command == "dialect") {
      // Set the dialect and respond
      assert(started);
      assert(message.contains("dialect") && message.at("dialect").is_string());
      options.default_version(message.at("dialect").as<std::string>());

      json response;
      response["ok"] = true;
      std::cout << print(response) << std::endl;
    } else if (command == "run") {
      assert(started);
      assert(message.contains("seq"));
      assert(message.contains("case") && message.at("case").is_object());
      assert(message.at("case").contains("schema"));

      const auto schema = message.at("case").at("schema");

      try {
        // Compile the schema and validate test cases
        assert(message.at("case").contains("tests") &&
               message.at("case").at("tests").is_array());

        std::unordered_map<std::string, jsoncons::json> schema_registry;
        if (message.at("case").contains("registry")) {
          for (const auto &[key, value] :
               message.at("case").at("registry").object_range()) {
            std::error_code ec;
            auto uri = jsoncons::uri::parse(key, ec);
            if (!ec) {
              schema_registry.emplace(uri.path(), value);
            }
          }
        }
        auto resolver = [&](const jsoncons::uri &uri) {
          auto it = schema_registry.find(uri.path());
          if (it != schema_registry.end()) {
            return it->second;
          }
          return jsoncons::json::null();
        };

        const auto compiled =
            jsonschema::make_json_schema(schema, resolver, options);

        json response;
        response["seq"] = message.at("seq");
        response["results"] = json(json_array_arg);

        for (const auto &test : message.at("case").at("tests").array_range()) {
          assert(test.contains("instance"));

          // Validate this test case and skip error messages
          auto valid = true;
          auto reporter =
              [&valid](const jsonschema::validation_message &message)
              -> jsonschema::walk_result {
            valid = false;
            // TODO Capture error messages
            return jsonschema::walk_result::abort;
          };
          compiled.validate(test.at("instance"), reporter);

          json test_result;
          test_result["valid"] = std::move(valid);
          response["results"].push_back(std::move(test_result));
        }

        std::cout << print(response) << std::endl;
      } catch (const std::exception &error) {
        // Report any errors during compilation or validation
        json response;
        response["seq"] = message.at("seq");
        response["errored"] = true;
        json context;
        context["message"] = error.what();
        response["context"] = std::move(context);

        std::cout << print(response) << std::endl;
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
