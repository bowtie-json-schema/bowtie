using System;
using System.Text.Json;
using System.Text.Json.Nodes;

using Json.Schema;


bool started = false;


while (Console.ReadLine() is { } line && line != "")
{
	var root = JsonNode.Parse(line);
	var cmd = root["cmd"].GetValue<string>();
	switch (cmd)
	{
		case "start":
			var version = root["version"];
			if (version.GetValue<int>() != 1) {
				throw new UnknownVersion(version);
			}
			started = true;
			var startResult = new JsonObject
			{
				["ready"] = true,
				["version"] = 1,
				["implementation"] = new JsonObject
				{
					["language"] = "dotnet",
					["name"] = "json-everything",
					["homepage"] = "https://json-everything.net/json-schema/",
					["issues"] = "https://github.com/gregsdennis/json-everything/issues",
				},
			};
			Console.WriteLine(startResult.ToJsonString());
			break;

		case "run":
			if (!started) {
				throw new NotStarted();
			}

			var testCase = root["case"];
			var schemaText = testCase["schema"];
			var schema = schemaText.Deserialize<JsonSchema>();
			var tests = testCase["tests"].AsArray();
                        try {
                            var results = new JsonArray();

                            foreach (var test in tests)
                            {
                                    var validationResult = schema.Validate(test["instance"]);
                                    var testResult = new JsonObject
                                    {
                                            ["valid"] = validationResult.IsValid,
                                    };
                                    results.Add(testResult);
                            };

                            var runResult = new JsonObject
                            {
                                    ["seq"] = root["seq"].GetValue<int>(),
                                    ["results"] = results,
                            };
                            Console.WriteLine(runResult.ToJsonString());
                        }
                        catch (Exception e)
                        {
                            var errorResult = new JsonObject
                            {
                                    ["seq"] = root["seq"].GetValue<int>(),
                                    ["errored"] = true,
                                    ["context"] = new JsonObject {
                                        ["Exception"] = e.ToString(),
                                        ["StackTrace"] = Environment.StackTrace,
                                    },
                            };
                            Console.WriteLine(errorResult.ToJsonString());
                        }
			break;

		case "stop":
			if (!started) {
				throw new NotStarted();
			}
			Environment.Exit(0);
			break;

		case null:
			throw new UnknownCommand("Missing command!");

		default:
			throw new UnknownCommand(cmd);

	}
}

class UnknownCommand : Exception
{
    public UnknownCommand(string message) {}
}

class UnknownVersion : Exception
{
    public UnknownVersion(JsonNode version) {}
}

class NotStarted : Exception
{
}
