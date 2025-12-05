import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.networknt.schema.AbsoluteIri;
import com.networknt.schema.Error;
import com.networknt.schema.Schema;
import com.networknt.schema.SchemaRegistry;
import com.networknt.schema.SpecificationVersion;
import com.networknt.schema.resource.InputStreamSource;
import com.networknt.schema.resource.ResourceLoader;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.jar.Manifest;

public class BowtieJsonSchemaValidator {

  private SpecificationVersion getVersionFromDialect(String dialect) {
    switch (dialect) {
    case "https://json-schema.org/draft/2020-12/schema":
      return SpecificationVersion.DRAFT_2020_12;
    case "https://json-schema.org/draft/2019-09/schema":
      return SpecificationVersion.DRAFT_2019_09;
    case "http://json-schema.org/draft-07/schema#":
      return SpecificationVersion.DRAFT_7;
    case "http://json-schema.org/draft-06/schema#":
      return SpecificationVersion.DRAFT_6;
    case "http://json-schema.org/draft-04/schema#":
      return SpecificationVersion.DRAFT_4;
    default:
      throw new IllegalArgumentException("Unsupported value" + dialect);
    }
  }

  private SpecificationVersion versionFlag;

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
        1, new Implementation(
               "java", attributes.getValue("Implementation-Name"),
               attributes.getValue("Implementation-Version"),
               List.of("https://json-schema.org/draft/2020-12/schema",
                       "https://json-schema.org/draft/2019-09/schema",
                       "http://json-schema.org/draft-07/schema#",
                       "http://json-schema.org/draft-06/schema#",
                       "http://json-schema.org/draft-04/schema#"),
               "https://github.com/networknt/json-schema-validator/",
               "https://doc.networknt.com/library/json-schema-validator/",
               "https://github.com/networknt/json-schema-validator/issues",
               "https://github.com/networknt/json-schema-validator/",
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

    versionFlag = getVersionFromDialect(dialectRequest.dialect());
    DialectResponse dialectResponse = new DialectResponse(true);
    output.println(objectMapper.writeValueAsString(dialectResponse));
  }

  private void run(JsonNode node) throws JsonProcessingException {
    if (!started) {
      throw new IllegalArgumentException("Not started!");
    }
    RunRequest runRequest = objectMapper.treeToValue(node, RunRequest.class);
    try {
      SchemaRegistry schemaRegistry = SchemaRegistry.withDefaultDialect(
          versionFlag,
          builder
          -> builder
                 .schemaIdResolvers(
                     schemaIdResolvers
                     -> schemaIdResolvers
                            .mapPrefix("https://json-schema.org", "classpath:")
                            .mapPrefix("http://json-schema.org", "classpath:"))
                 .resourceLoaders(resourceLoaders -> {
                   if (runRequest.testCase().registry() != null) {
                     CustomResourceLoader resourceLoader =
                         new CustomResourceLoader(
                             runRequest.testCase().registry());
                     resourceLoaders.add(resourceLoader);
                   }
                 }));
      List<TestResult> results =
          runRequest.testCase()
              .tests()
              .stream()
              .map(test -> {
                Schema jsonSchema =
                    schemaRegistry.getSchema(runRequest.testCase().schema());
                List<Error> errors = jsonSchema.validate(test.instance());
                boolean isValid = errors == null || errors.isEmpty();
                return new TestResult(isValid);
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

  class CustomResourceLoader implements ResourceLoader {

    private final Map<String, JsonNode> registry;

    CustomResourceLoader(JsonNode registryNode) {
      this.registry =
          objectMapper.convertValue(registryNode, new TypeReference<>() {});
    }

    @Override
    public InputStreamSource getResource(AbsoluteIri iri) {
      String iriString = iri.toString();

      if (registry.containsKey(iriString)) {
        JsonNode mappingSchema = registry.get(iriString);
        String mappingSchemaString = mappingSchema.toString();
        return ()
                   -> new ByteArrayInputStream(
                       mappingSchemaString.getBytes(StandardCharsets.UTF_8));
      }
      if (iriString.startsWith("classpath:")) {
        return null;
      }
      String emptySchema = "{}";
      return ()
                 -> new ByteArrayInputStream(
                     emptySchema.getBytes(StandardCharsets.UTF_8));
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

record
    Implementation(String language, String name, String version,
                   List<String> dialects, String homepage, String documentation,
                   String issues, String source, String os, String os_version,
                   String language_version, List<Link> links) {}

record Link(String url, String description) {}

record TestCase(String description, String comment, JsonNode schema,
                JsonNode registry, List<Test> tests) {}

record
    Test(String description, String comment, JsonNode instance, boolean valid) {
}

record TestResult(boolean valid) {}
