using System.Reflection;
using System.Text.Json.Nodes;
using Newtonsoft.Json.Linq;
using Newtonsoft.Json.Schema;

ICommandSource cmdSource = args.Length == 0 ? new ConsoleCommandSource() : new FileCommandSource(args[0]);

bool started = false;
var unsupportedTests = new Dictionary<(string, string), string> {};

var supportedSchemaVersions = new Dictionary<SchemaVersion, string> {
    { SchemaVersion.Draft3, "http://json-schema.org/draft-03/schema#" },
    { SchemaVersion.Draft4, "http://json-schema.org/draft-04/schema#" },
    { SchemaVersion.Draft6, "http://json-schema.org/draft-06/schema#" },
    { SchemaVersion.Draft7, "http://json-schema.org/draft-07/schema#" },
    { SchemaVersion.Draft2019_09, "https://json-schema.org/draft/2019-09/schema" },
    { SchemaVersion.Draft2020_12, "https://json-schema.org/draft/2020-12/schema" },
};
string? dialect = null;

while (cmdSource.GetNextCommand() is { } line && line != string.Empty)
{
    var root = JsonNode.Parse(line);

    if (root is null)
    {
        continue;
    }

    string? cmd = root["cmd"]?.GetValue<string>() ?? throw new MissingCommand(root);
    switch (cmd)
    {
        case "start":
            JsonNode? version = root["version"] ?? throw new MissingVersion(cmd);
            if (version.GetValue<int>() != 1)
            {
                throw new UnknownVersion(version);
            }

            started = true;
            var startResult = new JsonObject {
                ["version"] = 1,
                ["implementation"] =
                    new JsonObject { ["language"] = "dotnet", ["name"] = "Newtonsoft-Json-Schema",
                                     ["version"] = GetLibVersion(),
                                     ["homepage"] = "https://www.newtonsoft.com/jsonschema",
                                     ["documentation"] = "https://www.newtonsoft.com/jsonschema/help",
                                     ["issues"] = "https://github.com/JamesNK/Newtonsoft.Json.Schema/issues",
                                     ["source"] = "https://github.com/JamesNK/Newtonsoft.Json.Schema",
                                     ["dialects"] = new JsonArray(supportedSchemaVersions.OrderBy(x => x.Key)
                                                                      .Select(x => (JsonNode)x.Value)
                                                                      .ToArray()),
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

            dialect = root["dialect"]?.GetValue<string>() ?? throw new MissingDialect(root);
            var dialectResult = new JsonObject { ["ok"] = true };
            Console.WriteLine(dialectResult.ToJsonString());
            break;

        case "run":
            if (!started)
            {
                throw new NotStarted();
            }

            if (dialect is null)
            {
                throw new CannotRunBeforeDialectIsChosen();
            }

            JsonNode? testCase = root["case"] ?? throw new MissingCase(root);
            string? nullableTestCaseDescription = testCase["description"]?.GetValue<string>();

            if (nullableTestCaseDescription is not string testCaseDescription)
            {
                throw new MissingTestCaseDescription(testCase);
            }

            string schemaText = testCase["schema"]?.ToJsonString() ?? throw new MissingSchema(testCase);

            JsonNode? registry = testCase["registry"];
            var resolver = new JSchemaPreloadedResolver(new JSchemaUrlResolver());
            if (registry is not null)
            {
                foreach ((string key, JsonNode? value) in registry.AsObject())
                {
                    if (value is JsonNode v)
                    {
                        resolver.Add(new Uri(key), value.ToJsonString());
                    }
                }
            }

            var settings = new JSchemaReaderSettings();
            settings.Resolver = resolver;
            settings.ResolveSchemaReferences = true;

            string testDescription = string.Empty;

            var schema = JSchema.Parse(schemaText, settings);
            if (schema.SchemaVersion is null)
            {
                schema.SchemaVersion = new Uri(dialect);
            }

            JsonArray? tests = testCase["tests"]?.AsArray() ?? throw new MissingTests(testCase);

            try
            {
                var results = new JsonArray();

                foreach (JsonNode? test in tests)
                {
                    if (test is null)
                    {
                        throw new MissingTest(tests);
                    }

                    string? nullableTestDescription =
                        test["description"]?.GetValue<string>() ?? throw new MissingTestDescription(test);
                    testDescription = nullableTestDescription;

                    string? testInstance = test["instance"]?.ToJsonString() ?? "null";
                    var doc = JToken.Parse(testInstance);
                    bool validationResult = doc.IsValid(schema);
                    results.Add(new JsonObject { ["valid"] = validationResult });
                }

                var runResult = new JsonObject {
                    ["seq"] = root["seq"]?.DeepClone(),
                    ["results"] = results,
                };

                Console.WriteLine(runResult.ToJsonString());
            }
            catch (Exception) when (unsupportedTests.TryGetValue((testCaseDescription, testDescription), out string? message))
            {
                var skipResult =
                    new JsonObject { ["seq"] = root["seq"]?.DeepClone(), ["skipped"] = true, ["message"] = message };
                Console.WriteLine(skipResult.ToJsonString());
            }
            catch (Exception e)
            {
                var errorResult = new JsonObject {
                    ["seq"] = root["seq"]?.DeepClone(),
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
    AssemblyInformationalVersionAttribute? attribute =
        typeof(JSchema).Assembly.GetCustomAttribute<AssemblyInformationalVersionAttribute>();
    return attribute!.InformationalVersion;
}

internal interface ICommandSource
{
    string? GetNextCommand();
}

internal class MissingCommand(JsonNode root) : Exception
{
    public JsonNode Root { get; } = root;
}

internal class MissingTest(JsonNode tests) : Exception
{
    public JsonNode Tests { get; } = tests;
}

internal class MissingCase(JsonNode root) : Exception
{
    public JsonNode Root { get; } = root;
}

internal class MissingSchema(JsonNode testCase) : Exception
{
    public JsonNode TestCase { get; } = testCase;
}

internal class MissingTestDescription(JsonNode testInstance) : Exception
{
    public JsonNode TestInstance { get; } = testInstance;
}

internal class MissingDialect(JsonNode root) : Exception
{
    public JsonNode Root { get; } = root;
}

internal class MissingTestCaseDescription(JsonNode testCase) : Exception
{
    public JsonNode TestCase { get; } = testCase;
}

internal class MissingTests(JsonNode testCase) : Exception
{
    public JsonNode TestCase { get; } = testCase;
}

internal class UnknownCommand(string? message) : Exception
(message) { }

internal class MissingVersion(JsonNode command) : Exception
{
    public JsonNode Command { get; } = command;
}

internal class UnknownVersion(JsonNode version) : Exception
{
    public JsonNode Version { get; } = version;
}

internal class NotStarted : Exception;

internal class CannotRunBeforeDialectIsChosen : Exception;

internal class ConsoleCommandSource : ICommandSource
{
    public string? GetNextCommand()
    {
        return Console.ReadLine();
    }
}

internal class FileCommandSource(string fileName) : ICommandSource
{
    private readonly string[] fileContents = File.ReadAllLines(fileName);
    private int line;

    public string? GetNextCommand()
    {
        if (this.line < this.fileContents.Length)
        {
            return this.fileContents[this.line++];
        }

        return null;
    }
}
