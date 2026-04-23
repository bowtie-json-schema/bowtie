using System.Reflection;
using System.Runtime.Loader;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;
using Corvus.Json;
using Corvus.Json.CodeGeneration;
using Corvus.Json.Validator;

ICommandSource cmdSource = args.Length == 0 ? new ConsoleCommandSource() : new FileCommandSource(args[0]);

bool started = false;

var unsupportedTests = new Dictionary<(string, string), string> {};

var builders = new Dictionary<string, (Func<IVocabulary>, bool)> {
    ["https://json-schema.org/draft/2020-12/schema"] =
        (() => Corvus.Json.CodeGeneration.Draft202012.VocabularyAnalyser.DefaultVocabulary, false),
    ["https://json-schema.org/draft/2019-09/schema"] =
        (() => Corvus.Json.CodeGeneration.Draft201909.VocabularyAnalyser.DefaultVocabulary, false),
    ["http://json-schema.org/draft-07/schema#"] =
        (() => Corvus.Json.CodeGeneration.Draft7.VocabularyAnalyser.DefaultVocabulary, true),
    ["http://json-schema.org/draft-06/schema#"] =
        (() => Corvus.Json.CodeGeneration.Draft6.VocabularyAnalyser.DefaultVocabulary, true),
    ["http://json-schema.org/draft-04/schema#"] =
        (() => Corvus.Json.CodeGeneration.Draft4.VocabularyAnalyser.DefaultVocabulary, true),
};

IVocabulary? defaultVocabulary = null;
bool validateFormat = false;

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
            var startResult = new System.Text.Json.Nodes.JsonObject {
                ["version"] = 1,
                ["implementation"] =
                    new System.Text.Json.Nodes
                        .JsonObject { ["language"] = "dotnet", ["name"] = "Corvus.JsonSchema",
                                      ["version"] = GetLibVersion(),
                                      ["homepage"] = "https://github.com/corvus-dotnet/corvus.jsonschema",
                                      ["documentation"] =
                                          "https://github.com/corvus-dotnet/Corvus.JsonSchema/blob/main/README.md",
                                      ["issues"] = "https://github.com/corvus-dotnet/corvus.jsonschema/issues",
                                      ["source"] = "https://github.com/corvus-dotnet/corvus.jsonschema",

                                      ["dialects"] =
                                          new System.Text.Json.Nodes.JsonArray {
                                              "https://json-schema.org/draft/2020-12/schema",
                                              "https://json-schema.org/draft/2019-09/schema",
                                              "http://json-schema.org/draft-07/schema#",
                                              "http://json-schema.org/draft-06/schema#",
                                              "http://json-schema.org/draft-04/schema#",
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

            string? dialect = root["dialect"]?.GetValue<string>() ?? throw new MissingDialect(root);
            (Func<IVocabulary>? vocabularyFactory, validateFormat) = builders[dialect];
            defaultVocabulary = vocabularyFactory();
            var dialectResult = new System.Text.Json.Nodes.JsonObject {
                ["ok"] = true,
            };

            Console.WriteLine(dialectResult.ToJsonString());
            break;

        case "run":
            if (!started)
            {
                throw new NotStarted();
            }

            JsonNode? testCase = root["case"] ?? throw new MissingCase(root);
            string? nullableTestCaseDescription = testCase["description"]?.GetValue<string>();

            if (nullableTestCaseDescription is not string testCaseDescription)
            {
                throw new MissingTestCaseDescription(testCase);
            }

            string? schemaText = testCase["schema"]?.ToJsonString() ?? throw new MissingSchema(testCase);
            JsonNode? registry = testCase["registry"];

            if (defaultVocabulary is null)
            {
                throw new CannotRunBeforeDialectIsChosen();
            }

            PrepopulatedDocumentResolver resolver = new();

            if (registry is not null)
            {
                foreach ((string key, JsonNode? value) in registry.AsObject())
                {
                    if (value is JsonNode v)
                    {
                        resolver.AddDocument(key, JsonDocument.Parse(value.ToJsonString()));
                    }
                }
            }

            string fakeURI = $"https://example.com/bowtie-sent-schema-{root["seq"]?.ToJsonString()}.json";

            string testDescription = string.Empty;

            var schema = JsonSchema.FromText(
                schemaText, fakeURI,
                new JsonSchema.Options(additionalDocumentResolver: resolver, fallbackVocabulary: defaultVocabulary,
                                       alwaysAssertFormat: validateFormat, allowFileSystemAndHttpResolution: false));
            System.Text.Json.Nodes.JsonArray? tests = testCase["tests"]?.AsArray() ?? throw new MissingTests(testCase);

            try
            {
                var results = new System.Text.Json.Nodes.JsonArray();

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
                    using var doc = JsonDocument.Parse(testInstance);
                    bool validationResult = schema.Validate(doc.RootElement).IsValid;
                    results.Add(new System.Text.Json.Nodes.JsonObject { ["valid"] = validationResult });
                }

                var runResult = new System.Text.Json.Nodes.JsonObject {
                    ["seq"] = root["seq"]?.DeepClone(),
                    ["results"] = results,
                };

                Console.WriteLine(runResult.ToJsonString());
            }
            catch (Exception)
                when (unsupportedTests.TryGetValue((testCaseDescription, testDescription), out string? message))
            {
                var skipResult = new System.Text.Json.Nodes.JsonObject { ["seq"] = root["seq"]?.DeepClone(),
                                                                         ["skipped"] = true, ["message"] = message };
                Console.WriteLine(skipResult.ToJsonString());
            }
            catch (Exception e)
            {
                var errorResult = new System.Text.Json.Nodes.JsonObject {
                    ["seq"] = root["seq"]?.DeepClone(),
                    ["errored"] = true,
                    ["context"] =
                        new System.Text.Json.Nodes.JsonObject {
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
        typeof(Corvus.Json.CodeGeneration.JsonSchemaTypeBuilder)
            .Assembly.GetCustomAttribute<AssemblyInformationalVersionAttribute>();
#pragma warning disable SYSLIB1045 // Convert to 'GeneratedRegexAttribute'.
    return Regex.Match(attribute!.InformationalVersion, @"\d+\.\d+\.\d+").Value;
#pragma warning restore SYSLIB1045 // Convert to 'GeneratedRegexAttribute'.
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

internal class TestAssemblyLoadContext : AssemblyLoadContext
{
    public TestAssemblyLoadContext() : base($"TestAssemblyLoadContext_{Guid.NewGuid():N}", isCollectible: true) { }
}
