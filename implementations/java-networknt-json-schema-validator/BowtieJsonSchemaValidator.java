import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.networknt.schema.AbsoluteIri;
import com.networknt.schema.Error;
import com.networknt.schema.OutputFormat;
import com.networknt.schema.Schema;
import com.networknt.schema.SchemaRegistry;
import com.networknt.schema.SpecificationVersion;
import com.networknt.schema.output.OutputUnit;
import com.networknt.schema.resource.InputStreamSource;
import com.networknt.schema.resource.ResourceLoader;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.jar.Manifest;
import tools.jackson.core.type.TypeReference;
import tools.jackson.databind.DeserializationFeature;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.ObjectMapper;
import tools.jackson.databind.json.JsonMapper;

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

  private final ObjectMapper objectMapper =
      JsonMapper.builder()
          .disable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)
          .disable(DeserializationFeature.FAIL_ON_NULL_FOR_PRIMITIVES)
          .build();
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
      String cmd = node.get("cmd").asString();
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

  private void dialect(JsonNode node) {
    if (!started) {
      throw new IllegalArgumentException("Not started!");
    }

    DialectRequest dialectRequest =
        objectMapper.treeToValue(node, DialectRequest.class);

    versionFlag = getVersionFromDialect(dialectRequest.dialect());
    DialectResponse dialectResponse = new DialectResponse(true);
    output.println(objectMapper.writeValueAsString(dialectResponse));
  }

  private void collectAnnotations(
    OutputUnit unit,
    Map<String, Map<String, Map<String, Object>>> annotations) {
    if (unit == null) return;

    String instanceLoc = unit.getInstanceLocation() != null ? unit.getInstanceLocation().toString() : "";
    String schemaLoc = unit.getEvaluationPath() != null ? unit.getEvaluationPath().toString() : "";
    if (schemaLoc.isEmpty()) {
      schemaLoc = "#";
    } else if (schemaLoc.startsWith("/")) {
      schemaLoc = "#" + schemaLoc;
    }

    Map<String, Object> unitAnnotations = unit.getAnnotations();
    if (unitAnnotations != null && !unitAnnotations.isEmpty()) {
      for (Map.Entry<String, Object> entry : unitAnnotations.entrySet()) {
        String keyword = entry.getKey();
        Object value = entry.getValue();
        annotations
            .computeIfAbsent(instanceLoc, k -> new LinkedHashMap<>())
            .computeIfAbsent(keyword, k -> new LinkedHashMap<>())
            .put(schemaLoc, value);
      }
    }

    if (unit.getDetails() != null) {
      for (OutputUnit child : unit.getDetails()) {
        collectAnnotations(child, annotations);
      }
    }
  }

  private void run(JsonNode node) {
    if (!started) {
      throw new IllegalArgumentException("Not started!");
    }
    JsonNode testCase = node.get("case");
    JsonNode tests = testCase.get("tests");
    boolean collectAnnotations = node.has("collect_annotations") && node.get("collect_annotations").asBoolean();
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
                   if (testCase.has("registry")) {
                     CustomResourceLoader resourceLoader =
                         new CustomResourceLoader(
                             testCase.get("registry"));
                     resourceLoaders.add(resourceLoader);
                   }
                 }));
      List<TestResult> results = new ArrayList<>();
      for (JsonNode test : tests) {
        Schema jsonSchema = schemaRegistry.getSchema(testCase.get("schema"));
        if (collectAnnotations) {
          try {
            OutputUnit outputUnit = jsonSchema.validate(
                test.get("instance"),
                OutputFormat.HIERARCHICAL,
                executionContext -> {
                  executionContext.executionConfig(builder -> {
                    builder.annotationCollectionEnabled(true);
                    builder.annotationCollectionFilter(keyword -> true);
                  });
                }
            );
            boolean isValid = outputUnit.isValid();
            Map<String, Map<String, Map<String, Object>>> annotations =
                new LinkedHashMap<>();
            collectAnnotations(outputUnit, annotations);
            results.add(new TestResult(isValid, annotations.isEmpty() ? null : annotations));
          } catch (Exception e) {
            List<Error> errors = jsonSchema.validate(test.get("instance"));
            boolean isValid = errors == null || errors.isEmpty();
            results.add(new TestResult(isValid, null));
          }
        } else {
          List<Error> errors = jsonSchema.validate(test.get("instance"));
          boolean isValid = errors == null || errors.isEmpty();
          results.add(new TestResult(isValid, null));
        }
      }
      String responseString = objectMapper.writeValueAsString(
          new RunResponse(node.get("seq"), results));
      output.println(responseString);
    } catch (Exception e) {
      StringWriter stringWriter = new StringWriter();
      PrintWriter printWriter = new PrintWriter(stringWriter);
      e.printStackTrace(printWriter);
      RunErroredResponse response = new RunErroredResponse(
          node.get("seq"), true,
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
    Test(String description, String comment, JsonNode instance, JsonNode valid, JsonNode assertions) {
}

@JsonInclude(JsonInclude.Include.NON_NULL)
record TestResult(boolean valid, Map<String, Map<String, Map<String, Object>>> annotations) {}
