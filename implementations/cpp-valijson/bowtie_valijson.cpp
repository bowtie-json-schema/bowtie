#include <cassert>
#include <iostream>
#include <string>

#include "rapidjson/document.h"
#include "rapidjson/stringbuffer.h"
#include "rapidjson/writer.h"
#include "valijson/adapters/rapidjson_adapter.hpp"
#include "valijson/schema.hpp"
#include "valijson/schema_parser.hpp"
#include "valijson/utils/rapidjson_utils.hpp"
#include "valijson/validator.hpp"

using namespace rapidjson;
using namespace std;
using placeholders::_1;
using valijson::Schema;
using valijson::SchemaParser;
using valijson::adapters::RapidJsonAdapter;

const unordered_map<string, SchemaParser::Version> DIALECTS{
    {"http://json-schema.org/draft-07/schema#", SchemaParser::kDraft7},
    {"http://json-schema.org/draft-04/schema#", SchemaParser::kDraft4},
    {"http://json-schema.org/draft-03/schema#", SchemaParser::kDraft3},
};

class Registry {
  const Value *contents;

public:
  Registry(const Value *registryContents) { contents = registryContents; }

  const Document *fetchDocument(const string &uri) {
    Document *fetchedRoot = new Document();
    auto registry = contents->GetObject();
    fetchedRoot->CopyFrom(registry[uri.c_str()], fetchedRoot->GetAllocator());
    return fetchedRoot;
  }
};

void freeDocument(const Document *adapter) { delete adapter; }

int main() {

  string dialect;
  bool started = false;

  for (string line; getline(cin, line);) {
    Document request;

    Value response(kObjectType);
    Document::AllocatorType &allocator = request.GetAllocator();

    request.Parse(line.c_str());
    string cmd = request["cmd"].GetString();

    if (cmd == "start") {
      int version = request["version"].GetInt();
      assert(version == 1);

      started = true;

      response.AddMember("ready", true, allocator);
      response.AddMember("version", 1, allocator);

      Value implementation(kObjectType);
      implementation.AddMember("language", "c++", allocator);
      implementation.AddMember("name", "valijson", allocator);
      implementation.AddMember(
          "homepage", "https://github.com/tristanpenman/valijson", allocator);
      implementation.AddMember(
          "issues", "https://github.com/tristanpenman/valijson/issues",
          allocator);

      Value dialects(kArrayType);
      dialects.PushBack("http://json-schema.org/draft-07/schema#", allocator);
      dialects.PushBack("http://json-schema.org/draft-04/schema#", allocator);
      dialects.PushBack("http://json-schema.org/draft-03/schema#", allocator);
      implementation.AddMember("dialects", dialects, allocator);

      response.AddMember("implementation", implementation, allocator);
    } else if (cmd == "dialect") {
      if (!started) {
        throw runtime_error("Bowtie hasn't started!");
      }

      dialect = request["dialect"].GetString();
      // TODO: Check me
      response.AddMember("ok", true, allocator);
    } else if (cmd == "run") {
      if (!started) {
        throw runtime_error("Bowtie hasn't started!");
      }

      response.AddMember("seq", request["seq"], allocator);
      Value results(kArrayType);

      valijson::Validator validator;

      const Value &testCase = request["case"].GetObject();

      Schema schema;
      SchemaParser parser(DIALECTS.at(dialect));
      RapidJsonAdapter schemaAdapter(testCase["schema"]);

      auto registry = Registry{&testCase["registry"]};
      parser.populateSchema(schemaAdapter, schema,
                            bind(&Registry::fetchDocument, registry, _1),
                            freeDocument);

      for (auto &each : testCase["tests"].GetArray()) {
        RapidJsonAdapter instance(each["instance"]);

        Value result(kObjectType);
        result.AddMember("valid", validator.validate(schema, instance, NULL),
                         allocator);

        results.PushBack(result, allocator);
      }

      response.AddMember("results", results, allocator);
    } else if (cmd == "stop") {
      if (!started) {
        throw runtime_error("Bowtie hasn't started!");
      }
      return 0;
    } else {
      string message = "Unknown command: ";
      message += cmd;
      throw runtime_error(message);
    }

    StringBuffer buffer;
    Writer<StringBuffer> writer(buffer);
    response.Accept(writer);

    std::cout << buffer.GetString() << std::endl;
  }
}
