import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.*;
import java.net.URI;
import java.util.List;
import java.util.jar.Attributes;
import java.util.jar.Manifest;
import net.jimblackler.jsonschemafriend.Loader;
import net.jimblackler.jsonschemafriend.Schema;
import net.jimblackler.jsonschemafriend.SchemaStore;
import net.jimblackler.jsonschemafriend.ValidationException;
import net.jimblackler.jsonschemafriend.Validator;

public class BowtieJsonSchemaFriend {

  private final ObjectMapper objectMapper = new ObjectMapper().configure(
      DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
  private final PrintStream output;

  public static void main(String[] args) {
    BufferedReader reader =
        new BufferedReader(new InputStreamReader(System.in));
    new BowtieJsonSchemaFriend(System.out).run(reader);
  }

  public BowtieJsonSchemaFriend(PrintStream output) { this.output = output; }

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
                       "http://json-schema.org/draft-04/schema#",
                       "http://json-schema.org/draft-03/schema#"),
               "https://github.com/jimblackler/jsonschemafriend",
               "https://github.com/jimblackler/jsonschemafriend/issues",
               "https://github.com/jimblackler/jsonschemafriend",
               System.getProperty("os.name"), System.getProperty("os.version"),
               Runtime.version().toString(),
               List.of(new Link(createMavenUrl("Provider", attributes),
                                "Maven Central - used JSON provider"))));
    output.println(objectMapper.writeValueAsString(startResponse));
  }

  @SuppressWarnings("PMD.UnusedFormalParameter")
  private void dialect(JsonNode node) throws JsonProcessingException {
    // FIXME: This implementation doesn't appear to have a way to
    //        explicitly configure dialect, it seems to always want to
    //        autodetect it, and its test suite works by overriding schemas
    //        that don't contain $schema to then contain it.
    output.println(objectMapper.writeValueAsString(new DialectResponse(false)));
  }

  private void run(JsonNode node) throws JsonProcessingException {
    RunRequest runRequest = objectMapper.treeToValue(node, RunRequest.class);

    Loader registryLoader = new Loader() {
      public String load(URI uri, boolean cacheSchema) throws IOException {
        if (runRequest.testCase().registry() == null) {
          throw new IOException("No such schema");
        }

        JsonNode schema = runRequest.testCase().registry().get(uri.toString());
        if (schema == null) {
          throw new IOException("No such schema");
        }
        return schema.toString();
      }
    };

    SchemaStore schemaStore = new SchemaStore(registryLoader);
    Validator validator = new Validator();

    try {
      // using loadSchema and the loaded value directly (a JsonNode)
      // complains that this implementation is looking for a Map not an
      // ObjectNode, but that's quite inconvienient considering it can
      // also be a boolean.
      Schema schema =
          schemaStore.loadSchemaJson(runRequest.testCase().schema().toString());

      List<TestResult> results =
          runRequest.testCase()
              .tests()
              .stream()
              .map(test -> {
                try {
                  validator.validateJson(schema, test.instance().toString());
                } catch (ValidationException e) {
                  return new TestResult(false);
                }
                return new TestResult(true);
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
                      List<String> dialects, String homepage, String issues,
                      String source, String os, String os_version,
                      String language_version, List<Link> links) {}

record Link(String url, String description) {}

record TestCase(String description, String comment, JsonNode schema,
                JsonNode registry, List<Test> tests) {}

record Test(String description, String comment, JsonNode instance,
            boolean valid) {}

record TestResult(boolean valid) {}
