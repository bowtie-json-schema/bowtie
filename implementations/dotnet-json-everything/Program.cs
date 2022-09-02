using System;
using System.IO;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Text.Json.Nodes;

using Json.Schema;


bool Started = false;


string line;
while ((line = Console.In.ReadLine()) != null && line != "") {
    using (JsonDocument document = JsonDocument.Parse(line)) {
        JsonElement root = document.RootElement;
        string cmd = root.GetProperty("cmd").GetString();
        switch (cmd)
        {
            case "start":
                JsonElement version = root.GetProperty("version");
                if (version.GetInt32() != 1) {
                    throw new UnknownVersion(version);
                }
                Started = true;
                Console.Out.WriteLine("{\"ready\": true, \"version\": 1}");
                break;

            case "run":
                if (!Started) {
                    throw new NotStarted();
                }

                JsonElement testCase = root.GetProperty("case");
                // FIXME: JsonDocument -> JsonSchema ?
                JsonSchema schema = JsonSchema.FromText(
                    JsonObject.Create(testCase.GetProperty("schema")).ToJsonString()
                );
                JsonElement tests = testCase.GetProperty("tests");
                var results = new JsonArray();

                foreach (JsonElement test in tests.EnumerateArray())
                {
                    var validationResult = schema.Validate(test.GetProperty("instance"));
                    JsonObject testResult = new JsonObject
                    {
                        ["valid"] = validationResult.IsValid,
                    };
                    results.Add(testResult);
                };

                JsonObject result = new JsonObject
                {
                    ["seq"] = root.GetProperty("seq").GetInt64(),
                    ["tests"] = results,
                };
                Console.Out.WriteLine(result);
                break;

            case "stop":
                if (!Started) {
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
}

class UnknownCommand : Exception
{
    public UnknownCommand(string message) {}
}

class UnknownVersion : Exception
{
    public UnknownVersion(JsonElement version) {}
}

class NotStarted : Exception
{
    public NotStarted() {}
}
