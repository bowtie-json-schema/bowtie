import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import dev.harrel.jsonschema.Dialect;
import dev.harrel.jsonschema.Dialects;
import dev.harrel.jsonschema.SchemaResolver;
import dev.harrel.jsonschema.SpecificationVersion;
import dev.harrel.jsonschema.Validator;
import dev.harrel.jsonschema.ValidatorFactory;
import java.io.*;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.function.Function;
import java.util.jar.Attributes;
import java.util.jar.Manifest;
import java.util.stream.Collectors;

public class BowtieJsonSchema {
  private final Map<String, Dialect> dialectsMap;
  private final ValidatorFactory validatorFactory = new ValidatorFactory();

  private final ObjectMapper objectMapper = new ObjectMapper().configure(
      DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
  private final PrintStream output;
  private boolean started;

  public static void main(String[] args) {
    BufferedReader reader =
        new BufferedReader(new InputStreamReader(System.in));
    new BowtieJsonSchema(System.out).run(reader);
  }

  public BowtieJsonSchema(PrintStream output) {
    this.output = output;
    this.dialectsMap =
        Arrays.stream(Dialects.class.getClasses())
            .filter(Dialect.class ::isAssignableFrom)
            .map(clazz -> {
              try {
                return (Dialect)clazz.getConstructor().newInstance();
              } catch (Exception e) {
                throw new IllegalStateException("Failed to instantiate Dialect",
                                                e);
              }
            })
            .collect(Collectors.collectingAndThen(
                Collectors.toMap(dialect
                                 -> dialect.getSpecificationVersion().getId(),
                                 Function.identity()),
                Collections::unmodifiableMap));
  }

  private void run(BufferedReader reader) {
    reader.lines().forEach(this::handle);
  }

  private void handle(String data) {
    try {
      JsonNode node = objectMapper.readTree(data);
      String cmd = node.get("cmd").asText();
      switch (cmd) {
      case "start" -> start(node);
      case "dialect" -> dialect(node);
      case "run" -> run(node);
      case "stop" -> System.exit(0);
      default ->
        throw new IllegalArgumentException("Unknown cmd [%s]".formatted(cmd));
      }
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
  }

  private void start(JsonNode node) throws IOException {
    started = true;
    StartRequest startRequest =
        objectMapper.treeToValue(node, StartRequest.class);
    if (startRequest.version() != 1) {
      throw new IllegalArgumentException(
          "Unsupported IHOP version [%d]".formatted(startRequest.version()));
    }

    InputStream is = getClass().getResourceAsStream("META-INF/MANIFEST.MF");
    var attributes = new Manifest(is).getMainAttributes();

    String fullName =
        "%s.%s".formatted(attributes.getValue("Implementation-Group"),
                            attributes.getValue("Implementation-Name"));
    StartResponse startResponse = new StartResponse(
        1, new Implementation(
               "java", fullName, attributes.getValue("Implementation-Version"),
               Arrays.stream(SpecificationVersion.values())
                   .map(SpecificationVersion::getId)
                   .toList(),
               "https://github.com/harrel56/json-schema",
               "https://javadoc.io/doc/dev.harrel/json-schema/latest/dev/"
                   + "harrel/jsonschema/package-summary.html",
               "https://github.com/harrel56/json-schema/issues",
               "https://github.com/harrel56/json-schema",
               System.getProperty("os.name"), System.getProperty("os.version"),
               Runtime.version().toString(),
               List.of(new Link("https://harrel.dev", "Group homepage"),
                       new Link(createMavenUrl("Implementation", attributes),
                                "Maven Central - implementation"),
                       new Link(createMavenUrl("Provider", attributes),
                                "Maven Central - used JSON provider"))));
    output.println(objectMapper.writeValueAsString(startResponse));
  }

  private void dialect(JsonNode node) throws JsonProcessingException {
    if (!started) {
      throw new IllegalArgumentException("Not started!");
    }

    DialectRequest dialectRequest =
        objectMapper.treeToValue(node, DialectRequest.class);

    try {
      setDialectFor(this.dialectsMap.get(dialectRequest.dialect()));
    } catch (Exception e) {
      throw new IllegalStateException("Failed to set Dialect", e);
    }

    DialectResponse dialectResponse = new DialectResponse(true);
    output.println(objectMapper.writeValueAsString(dialectResponse));
  }

  private void setDialectFor(Dialect dialect) throws Exception {
    try {
      validatorFactory.getClass()
          .getMethod("withDefaultDialect", Dialect.class)
          .invoke(validatorFactory, dialect);
    } catch (NoSuchMethodException e) {
      validatorFactory.withDialect(dialect);
    }
  }

  private void run(JsonNode node) throws JsonProcessingException {
    if (!started) {
      throw new IllegalArgumentException("Not started!");
    }
    RunRequest runRequest = objectMapper.treeToValue(node, RunRequest.class);

    try {

      if (runRequest.testCase().registry() != null) {
        validatorFactory.withSchemaResolver(
            new RegistrySchemaResolver(runRequest.testCase().registry()));
      }

      List<TestResult> results =
          runRequest.testCase()
              .tests()
              .stream()
              .map(test -> {
                Validator.Result result = validatorFactory.validate(
                    runRequest.testCase().schema(), test.instance());
                return new TestResult(result.isValid());
              })
              .toList();
      output.println(objectMapper.writeValueAsString(
          new RunResponse(runRequest.seq(), results)));
    } catch (Exception e) {
      StringWriter stringWriter = new StringWriter();
      PrintWriter printWriter = new PrintWriter(stringWriter);
      e.printStackTrace(printWriter);
      RunErroredResponse response = new RunErroredResponse(
          runRequest.seq(), true,
          new ErrorContext(e.getMessage(), stackTraceToString(e)));
      output.println(objectMapper.writeValueAsString(response));
    }
  }

  private String createMavenUrl(String prefix, Attributes attributes) {
    return "https://mvnrepository.com/artifact/%s/%s/%s".formatted(
        attributes.getValue(prefix + "-Group"),
        attributes.getValue(prefix + "-Name"),
        attributes.getValue(prefix + "-Version"));
  }

  private String stackTraceToString(Exception e) {
    StringWriter stringWriter = new StringWriter();
    e.printStackTrace(new PrintWriter(stringWriter));
    return stringWriter.toString();
  }

  class RegistrySchemaResolver implements SchemaResolver {

    private final Map<String, JsonNode> registry;

    RegistrySchemaResolver(JsonNode registryNode) {
      this.registry =
          objectMapper.convertValue(registryNode, new TypeReference<>() {});
    }

    @Override
    public SchemaResolver.Result resolve(String uri) {
      return Optional.ofNullable(registry.get(uri))
          .map(Result::fromProviderNode)
          .orElse(SchemaResolver.Result.empty());
    }
  }
}

record StartRequest(int version) {}

record StartResponse(int version, Implementation implementation) {}

record DialectRequest(String dialect) {}

record DialectResponse(boolean ok) {}

record RunRequest(JsonNode seq, @JsonProperty("case") TestCase testCase) {}

record RunResponse(JsonNode seq, List<TestResult> results) {}

record RunSkippedResponse(JsonNode seq, boolean skipped, String message,
                          String issue_url) {}

record RunErroredResponse(JsonNode seq, boolean errored, ErrorContext context) {
}

record ErrorContext(String message, String traceback) {}

record Implementation(String language, String name, String version,
                      List<String> dialects, String homepage,
                      String documentation, String issues, String source,
                      String os, String os_version, String language_version,
                      List<Link> links) {}

record Link(String url, String description) {}

record TestCase(String description, String comment, JsonNode schema,
                JsonNode registry, List<Test> tests) {}

record Test(String description, String comment, JsonNode instance,
            boolean valid) {}

record TestResult(boolean valid) {}
