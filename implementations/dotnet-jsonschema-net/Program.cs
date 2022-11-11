using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Reflection;
using System.Text.RegularExpressions;

using Json.Schema;

ICommandSource cmdSource = args.Length == 0 ? new ConsoleCommandSource() : new FileCommandSource(args[0]);

bool started = false;
var options = new ValidationOptions();

var drafts = new Dictionary<string, Draft> {
    { "https://json-schema.org/draft/2020-12/schema", Draft.Draft202012 },
    { "https://json-schema.org/draft/2019-09/schema", Draft.Draft201909 },
    { "http://json-schema.org/draft-07/schema#", Draft.Draft7 },
    { "http://json-schema.org/draft-06/schema#", Draft.Draft6 },
};

while (cmdSource.GetNextCommand() is {} line && line != "")
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
                ["ready"] = true,
                ["version"] = 1,
                ["implementation"] =
                    new JsonObject {
                        ["language"] = "dotnet",
                        ["name"] = "JsonSchema.Net",
                        ["version"] = GetLibVersion(),
                        ["homepage"] = "https://json-everything.net/json-schema/",
                        ["issues"] = "https://github.com/gregsdennis/json-everything/issues",

                        ["dialects"] =
                            new JsonArray {
                                "https://json-schema.org/draft/2020-12/schema",
                                "https://json-schema.org/draft/2019-09/schema",
                                "http://json-schema.org/draft-07/schema#",
                                "http://json-schema.org/draft-06/schema#",
                            },
                    },
            };
            Console.WriteLine(startResult.ToJsonString());
            break;

        case "dialect":
            if (!started)
            {
                throw new NotStarted();
            }
            options = new ValidationOptions { ValidateAs = drafts[root["dialect"].GetValue<string>()],
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
            var schemaText = testCase["schema"];
            var registry = testCase["registry"];

            options.SchemaRegistry.Fetch = uri =>
            { return registry[uri.ToString()].Deserialize<JsonSchema>(); };

            var schema = schemaText.Deserialize<JsonSchema>();
            var tests = testCase["tests"].AsArray();

            try
            {
                var results = new JsonArray();

                foreach (var test in tests)
                {
                    var validationResult = schema.Validate(test["instance"], options);
                    var testResult = JsonSerializer.SerializeToNode(validationResult);
                    results.Add(testResult);
                }

                var runResult = new JsonObject {
                    ["seq"] = root["seq"].GetValue<int>(),
                    ["results"] = results,
                };
                Console.WriteLine(runResult.ToJsonString());
            }
            catch (Exception e)
            {
                var errorResult = new JsonObject {
                    ["seq"] = root["seq"].GetValue<int>(),
                    ["errored"] = true,
                    ["context"] =
                        new JsonObject {
                            ["Exception"] = e.ToString(),
                            ["StackTrace"] = Environment.StackTrace,
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
    return Regex.Match(attribute!.InformationalVersion, @"\d+\.\d+\.\d+").Value;
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
