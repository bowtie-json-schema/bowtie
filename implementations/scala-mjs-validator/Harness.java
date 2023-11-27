import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.circe.Json;
import java.io.*;
import java.util.List;
import java.util.Map;
import java.util.jar.Manifest;
import main.MainClass$;
import scala.Tuple3;

public class Harness {

  private static final String NOT_IMPLEMENTED =
      "This case is not yet implemented.";
  private static final Map<String, String> UNSUPPORTED = Map.of(
      "escaped pointer ref", NOT_IMPLEMENTED,
      "empty tokens in $ref json-pointer", NOT_IMPLEMENTED,
      "maxLength validation", NOT_IMPLEMENTED, "minLength validation",
      NOT_IMPLEMENTED, "$id inside an unknown keyword is not a real identifier",
      NOT_IMPLEMENTED,
      "schema that uses custom metaschema with with no validation vocabulary",
      NOT_IMPLEMENTED, "small multiple of large integer", NOT_IMPLEMENTED,
      "$ref to $ref finds detached $anchor", NOT_IMPLEMENTED,
      "$ref to $dynamicRef finds detached $dynamicAnchor", NOT_IMPLEMENTED);

  private final MainClass$ mjs = MainClass$.MODULE$;

  private final ObjectMapper objectMapper = new ObjectMapper().configure(
      DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
  private final PrintStream output;
  private boolean started;

  public static void main(String[] args) {
    BufferedReader reader =
        new BufferedReader(new InputStreamReader(System.in));
    new Harness(System.out).run(reader);
  }

  public Harness(PrintStream output) { this.output = output; }

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

    InputStream is = getClass().getResourceAsStream("META-INF/MANIFEST.MF");
    var attributes = new Manifest(is).getMainAttributes();

    StartResponse startResponse = new StartResponse(
      1,
      true,
      new Implementation(
        "scala",
        attributes.getValue("Implementation-Name"),
        attributes.getValue("Implementation-Version"),
        List.of("https://json-schema.org/draft/2020-12/schema"),
        "https://gitlab.lip6.fr/jsonschema/modernjsonschemavalidator",
        "https://gitlab.lip6.fr/jsonschema/modernjsonschemavalidator/issues",
        System.getProperty("os.name"),
        System.getProperty("os.version"),
        Runtime.version().toString(),
        List.of()
      )
    );
    output.println(objectMapper.writeValueAsString(startResponse));
    }

    @SuppressWarnings("PMD.UnusedFormalParameter")
    private void dialect(JsonNode node) throws JsonProcessingException {
    if (!started) {
      throw new IllegalArgumentException("Not started!");
    }

    DialectResponse dialectResponse = new DialectResponse(false);
    output.println(objectMapper.writeValueAsString(dialectResponse));
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

      List<TestResult> results = runRequest
        .testCase()
        .tests()
        .stream()
        .map(test -> {
            Tuple3<Object, Json, String> result = mjs.validateInstance(
                runRequest.testCase().schema().toString(),
                test.instance().toString()
            );
          return new TestResult((boolean)result._1());
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


  private String stackTraceToString(Exception e) {
    StringWriter stringWriter = new StringWriter();
    e.printStackTrace(new PrintWriter(stringWriter));
    return stringWriter.toString();
  }
}

record StartRequest(int version) {}

record StartResponse(int version, boolean ready, Implementation implementation) {}

record DialectRequest(String dialect) {}

record DialectResponse(boolean ok) {}

record RunRequest(JsonNode seq, @JsonProperty("case") TestCase testCase) {}

record RunResponse(JsonNode seq, List<TestResult> results) {}

record RunSkippedResponse(JsonNode seq, boolean skipped, String message, String issue_url) {}

record RunErroredResponse(JsonNode seq, boolean errored, ErrorContext context) {}

record ErrorContext(String message, String traceback) {}

record Implementation(String language, String name, String version,
                      List<String> dialects, String homepage, String issues,
                      String os, String os_version, String language_version,
                      List<Link> links) {}

record Link(String url, String description) {}

record TestCase(String description, String comment, JsonNode schema,
                JsonNode registry, List<Test> tests) {}

record Test(String description, String comment, JsonNode instance,
            boolean valid) {}

record TestResult(boolean valid) {}
