import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.fge.jsonschema.SchemaVersion;
import com.github.fge.jsonschema.cfg.ValidationConfiguration;
import com.github.fge.jsonschema.core.exceptions.ProcessingException;
import com.github.fge.jsonschema.core.load.configuration.LoadingConfiguration;
import com.github.fge.jsonschema.core.load.configuration.LoadingConfigurationBuilder;
import com.github.fge.jsonschema.core.report.ProcessingReport;
import com.github.fge.jsonschema.main.JsonSchemaFactory;
import com.github.fge.jsonschema.main.JsonValidator;
import java.io.*;
import java.util.List;
import java.util.jar.Manifest;

public class BowtieJsonSchemaValidator {

  private SchemaVersion getVersionFromDialect(String dialect) {
    switch (dialect) {
    case "http://json-schema.org/draft-04/schema#":
      return SchemaVersion.DRAFTV4;
    case "http://json-schema.org/draft-03/schema#":
      return SchemaVersion.DRAFTV3;
    default:
      throw new IllegalArgumentException("Unsupported value" + dialect);
    }
  }

  private ValidationConfiguration validationConfiguration;

  private final ObjectMapper objectMapper = new ObjectMapper().configure(
      DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
  private final PrintStream output;
  private boolean started;

  public static void main(String[] args) {
    BufferedReader reader =
        new BufferedReader(new InputStreamReader(System.in));
    new BowtieJsonSchemaValidator(System.out).run(reader);
  }

  public BowtieJsonSchemaValidator(PrintStream output) { this.output = output; }

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

    StartResponse startResponse = new StartResponse(
        1,
        new Implementation(
            "java", attributes.getValue("Implementation-Name"),
            attributes.getValue("Implementation-Version"),
            List.of("http://json-schema.org/draft-04/schema#",
                    "http://json-schema.org/draft-03/schema#"),
            "https://github.com/java-json-tools/json-schema-validator",
            "https://github.com/java-json-tools/json-schema-validator",
            "https://github.com/java-json-tools/json-schema-validator/issues",
            "https://github.com/java-json-tools/json-schema-validator",
            System.getProperty("os.name"), System.getProperty("os.version"),
            Runtime.version().toString(), List.of()));
    output.println(objectMapper.writeValueAsString(startResponse));
  }

  private void dialect(JsonNode node) throws JsonProcessingException {
    if (!started) {
      throw new IllegalArgumentException("Not started!");
    }

    DialectRequest dialectRequest =
        objectMapper.treeToValue(node, DialectRequest.class);

    SchemaVersion schemaVersion =
        getVersionFromDialect(dialectRequest.dialect());
    validationConfiguration = ValidationConfiguration.newBuilder()
                                  .setDefaultVersion(schemaVersion)
                                  .freeze();

    DialectResponse dialectResponse = new DialectResponse(true);
    output.println(objectMapper.writeValueAsString(dialectResponse));
  }

  private void run(JsonNode node) throws JsonProcessingException {
    if (!started) {
      throw new IllegalArgumentException("Not started!");
    }
    RunRequest runRequest = objectMapper.treeToValue(node, RunRequest.class);
    try {
      final LoadingConfigurationBuilder builder =
          LoadingConfiguration.newBuilder();

      if (runRequest.testCase().registry() != null) {
        runRequest.testCase().registry().fields().forEachRemaining(
            entry -> builder.preloadSchema(entry.getKey(), entry.getValue()));
      }

      JsonSchemaFactory factory =
          JsonSchemaFactory.newBuilder()
              .setLoadingConfiguration(builder.freeze())
              .setValidationConfiguration(validationConfiguration)
              .freeze();
      final JsonValidator validator;

      validator = factory.getValidator();
      List<Record> results =
          runRequest.testCase()
              .tests()
              .stream()
              .map(test -> {
                try {
                  ProcessingReport report = validator.validate(
                      runRequest.testCase().schema(), test.instance());
                  return new TestResult(report.isSuccess());
                } catch (ProcessingException e) {
                  return new TestErrored(
                      true,
                      new ErrorContext(e.getMessage(), stackTraceToString(e)));
                }
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

  private String stackTraceToString(Exception e) {
    StringWriter stringWriter = new StringWriter();
    e.printStackTrace(new PrintWriter(stringWriter));
    return stringWriter.toString();
  }
}

record StartRequest(int version) {}

record StartResponse(int version, Implementation implementation) {}

record DialectRequest(String dialect) {}

record DialectResponse(boolean ok) {}

record RunRequest(JsonNode seq, @JsonProperty("case") TestCase testCase) {}

record RunResponse(JsonNode seq, List<Record> results) {}

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
record TestErrored(boolean errored, ErrorContext context) {}
