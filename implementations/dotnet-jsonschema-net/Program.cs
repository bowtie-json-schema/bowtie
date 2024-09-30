using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Reflection;
using System.Text.RegularExpressions;

using Json.Schema;

ICommandSource cmdSource = args.Length == 0 ? new ConsoleCommandSource() : new FileCommandSource(args[0]);

bool started = false;
var options = new EvaluationOptions();

var drafts = new Dictionary<string, SpecVersion> {
    { "https://json-schema.org/draft/2020-12/schema", SpecVersion.Draft202012 },
    { "https://json-schema.org/draft/2019-09/schema", SpecVersion.Draft201909 },
    { "http://json-schema.org/draft-07/schema#", SpecVersion.Draft7 },
    { "http://json-schema.org/draft-06/schema#", SpecVersion.Draft6 },
};

var unsupportedTests =
    new Dictionary<(string, string),
                   string> { [("float division = inf",
                               "always invalid, but naive implementations may raise an overflow error")] =
                                 "System.Decimal does not support large values like 1e308" };

while (cmdSource.GetNextCommand() is { } line && line != "")
{
    var root = JsonNode.Parse(line);
    var cmd = root["cmd"].GetValue<string>();
    switch (cmd)
    {
        case "start":
            var version = root["version"];
            if (version.GetValue<int>() != 1)
            {
                throw new UnknownVersion(version);
            }
            started = true;
            var startResult = new JsonObject {
                ["version"] = 1,
                ["implementation"] =
                    new JsonObject { ["language"] = "dotnet", ["name"] = "JsonSchema.Net",
                                     ["version"] = GetLibVersion(),
                                     ["homepage"] = "https://json-everything.net/json-schema/",
                                     ["documentation"] = "https://docs.json-everything.net/schema/basics/",
                                     ["issues"] = "https://github.com/gregsdennis/json-everything/issues",
                                     ["source"] = "https://github.com/gregsdennis/json-everything",

                                     ["dialects"] =
                                         new JsonArray {
                                             "https://json-schema.org/draft/2020-12/schema",
                                             "https://json-schema.org/draft/2019-09/schema",
                                             "http://json-schema.org/draft-07/schema#",
                                             "http://json-schema.org/draft-06/schema#",
                                         },
                                     ["os"] = Environment.OSVersion.Platform.ToString(),
                                     ["os_version"] = Environment.OSVersion.Version.ToString(),
                                     ["language_version"] = Environment.Version.ToString() },
            };
            Console.WriteLine(startResult.ToJsonString());
            break;

        case "dialect":
            if (!started)
            {
                throw new NotStarted();
            }
            options = new EvaluationOptions { EvaluateAs = drafts[root["dialect"].GetValue<string>()],
                                              // for local debugging, change this to Verbose
                                              OutputFormat = OutputFormat.Flag };

            var dialectResult = new JsonObject {
                ["ok"] = true,
            };
            Console.WriteLine(dialectResult.ToJsonString());
            break;

        case "run":
            if (!started)
            {
                throw new NotStarted();
            }

            var testCase = root["case"];
            var seq = root["seq"].DeepClone();
            var testCaseDescription = testCase["description"].GetValue<string>();
            string? testDescription = null;
            var schemaText = testCase["schema"];

            JsonNode? nullableRegistry = testCase["registry"];
            if (nullableRegistry is not null)
            {
                var registry = nullableRegistry.AsObject().ToDictionary(x => new Uri(x.Key), x => x.Value);
                options.SchemaRegistry.Fetch = uri => registry[uri].Deserialize<JsonSchema>();
            }

            var schema = schemaText.Deserialize<JsonSchema>();
            var tests = testCase["tests"].AsArray();

            try
            {
                var results = new JsonArray();

                foreach (var test in tests)
                {
                    testDescription = test["description"].GetValue<string>();
                    var validationResult = schema.Evaluate(test["instance"], options);
                    var testResult = JsonSerializer.SerializeToNode(validationResult);
                    results.Add(testResult);
                }

                var runResult = new JsonObject {
                    ["seq"] = seq,
                    ["results"] = results,
                };
                Console.WriteLine(runResult.ToJsonString());
            }
            catch (Exception)
                when (unsupportedTests.TryGetValue((testCaseDescription, testDescription), out var message))
            {
                var skipResult = new JsonObject { ["seq"] = seq, ["skipped"] = true, ["message"] = message };
                Console.WriteLine(skipResult.ToJsonString());
            }
            catch (Exception e)
            {
                var errorResult = new JsonObject {
                    ["seq"] = seq,
                    ["errored"] = true,
                    ["context"] =
                        new JsonObject {
                            ["message"] = e.ToString(),
                            ["traceback"] = Environment.StackTrace,
                        },
                };
                Console.WriteLine(errorResult.ToJsonString());
            }
            break;

        case "stop":
            if (!started)
            {
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

static string GetLibVersion()
{
    var attribute = typeof(JsonSchema).Assembly.GetCustomAttribute<AssemblyInformationalVersionAttribute>();
    return Regex.Match(attribute!.InformationalVersion, @"\d+(\.\d+)+").Value;
}

class UnknownCommand : Exception
{
    public UnknownCommand(string message) { }
}

class UnknownVersion : Exception
{
    public UnknownVersion(JsonNode version) { }
}

class NotStarted : Exception
{
}

interface ICommandSource
{
    string? GetNextCommand();
}

class ConsoleCommandSource : ICommandSource
{
    public string? GetNextCommand()
    {
        return Console.ReadLine();
    }
}

class FileCommandSource : ICommandSource
{
    private readonly string[] _fileContents;
    private int _line;

    public FileCommandSource(string fileName)
    {
        _fileContents = File.ReadAllLines(fileName);
    }

    public string? GetNextCommand()
    {
        if (_line < _fileContents.Length)
        {
            return _fileContents[_line++];
        }

        return null;
    }
}
