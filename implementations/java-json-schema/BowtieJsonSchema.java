import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import dev.harrel.jsonschema.Dialect;
import dev.harrel.jsonschema.SchemaResolver;
import dev.harrel.jsonschema.SpecificationVersion;
import dev.harrel.jsonschema.Validator;
import dev.harrel.jsonschema.ValidatorFactory;
import java.io.*;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.jar.Attributes;
import java.util.jar.Manifest;

public class BowtieJsonSchema {

  private static final String RECOGNIZING_IDENTIFIERS =
      "Determining if a specific location is a schema or not is not supported.";
  private static final Map<String, String> UNSUPPORTED;

  private static final Attributes MANIFEST_ATTRIBUTES;
  private static final String IMPLEMENTATION_VERSION;

  private final ValidatorFactory validatorFactory = new ValidatorFactory();

  private final ObjectMapper objectMapper = new ObjectMapper().configure(
      DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
  private final PrintStream output;
  private boolean started;

  static {
    MANIFEST_ATTRIBUTES = readManifestAttributes();

    IMPLEMENTATION_VERSION =
        MANIFEST_ATTRIBUTES.getValue("Implementation-Version");
    UNSUPPORTED =
        IMPLEMENTATION_VERSION.compareTo("1.7.0") >= 0
            ? Map.of("$ref prevents a sibling $id from changing the base uri",
                     RECOGNIZING_IDENTIFIERS)
            : Map.of("$id inside an enum is not a real identifier",
                     RECOGNIZING_IDENTIFIERS,
                     "$id inside an unknown keyword is not a real identifier",
                     RECOGNIZING_IDENTIFIERS,
                     "$anchor inside an enum is not a real identifier",
                     RECOGNIZING_IDENTIFIERS);
  }

  private static Attributes readManifestAttributes() {
    try (InputStream is = BowtieJsonSchema.class.getResourceAsStream(
             "META-INF/MANIFEST.MF")) {
      return new Manifest(is).getMainAttributes();
    } catch (IOException e) {
      throw new RuntimeException("Failed to read manifest", e);
    }
  }

  public static void main(String[] args) {
    BufferedReader reader =
        new BufferedReader(new InputStreamReader(System.in));
    new BowtieJsonSchema(System.out).run(reader);
  }

  public BowtieJsonSchema(PrintStream output) { this.output = output; }

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
        default -> throw new IllegalArgumentException(
          "Unknown cmd [%s]".formatted(cmd)
        );
      }
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
  }

  private void start(JsonNode node) throws IOException {
    started = true;
    StartRequest startRequest = objectMapper.treeToValue(
      node,
      StartRequest.class
    );
    if (startRequest.version() != 1) {
      throw new IllegalArgumentException(
        "Unsupported IHOP version [%d]".formatted(startRequest.version())
      );
    }

    String fullName = "%s.%s".formatted(
      MANIFEST_ATTRIBUTES.getValue("Implementation-Group"),
      MANIFEST_ATTRIBUTES.getValue("Implementation-Name")
    );
    StartResponse startResponse = new StartResponse(
      1,
      new Implementation(
        "java",
        fullName,
        IMPLEMENTATION_VERSION,
        Arrays.stream(SpecificationVersion.values()).map(SpecificationVersion::getId).toList(),
        "https://github.com/harrel56/json-schema",
        "https://javadoc.io/doc/dev.harrel/json-schema/latest/dev/harrel/jsonschema/package-summary.html",
        "https://github.com/harrel56/json-schema/issues",
        "https://github.com/harrel56/json-schema",
        System.getProperty("os.name"),
        System.getProperty("os.version"),
        Runtime.version().toString(),
        List.of(
            new Link("https://harrel.dev", "Group homepage"),
            new Link(createMavenUrl("Implementation"), "Maven Central - implementation"),
            new Link(createMavenUrl("Provider"), "Maven Central - used JSON provider")
        )
      )
    );
    output.println(objectMapper.writeValueAsString(startResponse));
  }

  private void dialect(JsonNode node) throws JsonProcessingException {
    if (!started) {
      throw new IllegalArgumentException("Not started!");
    }

    DialectRequest dialectRequest = objectMapper.treeToValue(
      node,
      DialectRequest.class
    );

    try {
      if (getSpecificationVersionFor("DRAFT2020_12").getId().equals(dialectRequest.dialect())) {
        setDialect(Class.forName("dev.harrel.jsonschema.Dialects$Draft2020Dialect"));
      } else if (getSpecificationVersionFor("DRAFT2019_09").getId().equals(dialectRequest.dialect())) {
        setDialect(Class.forName("dev.harrel.jsonschema.Dialects$Draft2019Dialect"));
      } else if (getSpecificationVersionFor("DRAFT7").getId().equals(dialectRequest.dialect())) {
        setDialect(Class.forName("dev.harrel.jsonschema.Dialects$Draft7Dialect"));
      }
    } catch (ClassNotFoundException e) {
      throw new RuntimeException("Failed to setDialect", e);
    } catch (Exception e) {
      throw new RuntimeException("Failed to retrieve SpecificationVersion", e);
    }

    DialectResponse dialectResponse = new DialectResponse(true);
    output.println(objectMapper.writeValueAsString(dialectResponse));
  }

  private void setDialect(Class<?> dialectClass) throws Exception {
    Object dialectInstance;
    try {
      dialectInstance = dialectClass.getDeclaredConstructor().newInstance();
    } catch (Exception e) {
      throw new RuntimeException("Failed to create dialect instance", e);
    }

    try {
        Method withDefaultDialectMethod = validatorFactory
                                              .getClass()
                                              .getMethod(
                                                "withDefaultDialect", 
                                                Dialect.class
                                              );
        withDefaultDialectMethod.invoke(validatorFactory, dialectInstance);
    } catch (NoSuchMethodException e) {
        try {
            Method withDialectMethod = validatorFactory
                                            .getClass()
                                            .getMethod(
                                              "withDialect", 
                                              Dialect.class
                                            );
            withDialectMethod.invoke(validatorFactory, dialectInstance);
        } catch (NoSuchMethodException ex) {
            throw new RuntimeException(
              "Failed to setDialect: Neither withDefaultDialect nor withDialect method found", 
              ex
            );
        } catch (Exception ex) {
            throw new RuntimeException("Failed to invoke withDialect method", ex);
        }
    } catch (Exception e) {
        throw new RuntimeException("Failed to invoke withDefaultDialect method", e);
    }
  }

  private SpecificationVersion getSpecificationVersionFor(String draftName) throws Exception {
    try {
      Field draftField = SpecificationVersion.class.getDeclaredField(draftName);
      return (SpecificationVersion) draftField.get(null);
    } catch (NoSuchFieldException | IllegalAccessException e) {
      throw new RuntimeException(
        "Failed to retrieve SpecificationVersion for: " + draftName, e
      );
    }
  }

  private void run(JsonNode node) throws JsonProcessingException {
    if (!started) {
      throw new IllegalArgumentException("Not started!");
    }
    RunRequest runRequest = objectMapper.treeToValue(node, RunRequest.class);

    if (UNSUPPORTED.containsKey(runRequest.testCase().description())) {
      RunSkippedResponse response = new RunSkippedResponse(
        runRequest.seq(),
        true,
        UNSUPPORTED.get(runRequest.testCase().description()),
        null
      );
      output.println(objectMapper.writeValueAsString(response));
      return;
    }

    try {

      if (runRequest.testCase().registry() != null) {
        validatorFactory.withSchemaResolver(new RegistrySchemaResolver(runRequest.testCase().registry()));
      }

      List<TestResult> results = runRequest
        .testCase()
        .tests()
        .stream()
        .map(test -> {
          Validator.Result result = validatorFactory.validate(
            runRequest.testCase().schema(),
            test.instance()
          );
          return new TestResult(result.isValid());
        })
        .toList();
        output.println(
          objectMapper.writeValueAsString(
            new RunResponse(runRequest.seq(), results)
          )
        );
      } catch (Exception e) {
        StringWriter stringWriter = new StringWriter();
        PrintWriter printWriter = new PrintWriter(stringWriter);
        e.printStackTrace(printWriter);
        RunErroredResponse response = new RunErroredResponse(
          runRequest.seq(),
          true,
          new ErrorContext(e.getMessage(), stackTraceToString(e))
        );
        output.println(objectMapper.writeValueAsString(response));
      }
    }

  private String createMavenUrl(String prefix) {
      return "https://mvnrepository.com/artifact/%s/%s/%s".formatted(
              MANIFEST_ATTRIBUTES.getValue(prefix + "-Group"),
              MANIFEST_ATTRIBUTES.getValue(prefix + "-Name"),
              MANIFEST_ATTRIBUTES.getValue(prefix + "-Version")
      );
  }

  private String stackTraceToString(Exception e) {
    StringWriter stringWriter = new StringWriter();
    e.printStackTrace(new PrintWriter(stringWriter));
    return stringWriter.toString();
  }

  class RegistrySchemaResolver implements SchemaResolver {

    private final Map<String, JsonNode> registry;

    RegistrySchemaResolver(JsonNode registryNode) {
      this.registry = objectMapper.convertValue(registryNode, new TypeReference<>() {});
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

record RunSkippedResponse(JsonNode seq, boolean skipped, String message, String issue_url) {}

record RunErroredResponse(JsonNode seq, boolean errored, ErrorContext context) {}

record ErrorContext(String message, String traceback) {}

record Implementation(String language,
                      String name,
                      String version,
                      List<String> dialects,
                      String homepage,
                      String documentation,
                      String issues,
                      String source,
                      String os,
                      String os_version,
                      String language_version,
                      List<Link> links) {}

record Link(String url, String description) {}

record TestCase(String description, String comment, JsonNode schema, JsonNode registry, List<Test> tests) {}

record Test(String description, String comment, JsonNode instance, boolean valid) {}

record TestResult(boolean valid) {}
