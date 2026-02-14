
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.PrintStream;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.io.UncheckedIOException;
import java.net.URI;
import java.util.List;
import java.util.jar.Manifest;
import org.sjf4j.JsonObject;
import org.sjf4j.Sjf4j;
import org.sjf4j.annotation.node.NodeProperty;
import org.sjf4j.schema.JsonSchema;
import org.sjf4j.schema.SchemaStore;

public class BowtieSjf4jValidator {

  public static void main(String[] args) {
    BufferedReader reader =
        new BufferedReader(new InputStreamReader(System.in));
    new BowtieSjf4jValidator(System.out).run(reader);
  }

  private final List<String> dialects =
      List.of("https://json-schema.org/draft/2020-12/schema");

  private final PrintStream output;
  private boolean started;

  public BowtieSjf4jValidator(PrintStream output) { this.output = output; }

  private void run(BufferedReader reader) {
    reader.lines().forEach(this::handle);
  }

  private void handle(String data) {
    try {
      JsonObject jo = JsonObject.fromJson(data);
      String cmd = jo.getString("cmd");
      switch (cmd) {
      case "start" -> start(jo);
      case "dialect" -> dialect(jo);
      case "run" -> run(jo);
      case "stop" -> System.exit(0);
      default ->
        throw new IllegalArgumentException("Unknown cmd [%s]".formatted(cmd));
      }
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
  }

  private void start(JsonObject jo) throws IOException {
    started = true;
    StartRequest startRequest = jo.toNode(StartRequest.class);
    if (startRequest.version() != 1) {
      throw new IllegalArgumentException(
          "Unsupported IHOP version [%d]".formatted(startRequest.version()));
    }

    InputStream is = getClass().getResourceAsStream("META-INF/MANIFEST.MF");
    var attributes = new Manifest(is).getMainAttributes();

    String fullName =
        "%s-%s".formatted(attributes.getValue("Implementation-Group"),
                            attributes.getValue("Implementation-Name"));
    StartResponse startResponse = new StartResponse(
        1, new Implementation(
               "java", fullName, attributes.getValue("Implementation-Version"),
               dialects, "https://sjf4j.org",
               "https://github.com/sjf4j-projects/sjf4j",
               "https://github.com/sjf4j-projects/sjf4j/issues",
               "https://github.com/sjf4j-projects/sjf4j",
               System.getProperty("os.name"), System.getProperty("os.version"),
               Runtime.version().toString(), List.of()));
    output.println(Sjf4j.toJsonString(startResponse));
  }

  private void dialect(JsonObject jo) {
    if (!started) {
      throw new IllegalArgumentException("Not started!");
    }

    DialectRequest dialectRequest = Sjf4j.fromNode(jo, DialectRequest.class);
    if (dialects.contains(dialectRequest.dialect())) {
      output.println(Sjf4j.toJsonString(new DialectResponse(true)));
    } else {
      output.println(Sjf4j.toJsonString(new DialectResponse(false)));
    }
  }

  private void run(JsonObject jo) {
    if (!started) {
      throw new IllegalArgumentException("Not started!");
    }
    RunRequest runRequest = Sjf4j.fromNode(jo, RunRequest.class);

    try {
      SchemaStore store = new SchemaStore();
      if (runRequest.testCase().registry() != null) {
        runRequest.testCase().registry().forEach((k, v) -> {
          store.register(URI.create(k), JsonSchema.fromNode(v));
        });
      }

      JsonSchema schema = JsonSchema.fromNode(runRequest.testCase().schema());
      schema.compile(store);

      List<TestResult> results =
          runRequest.testCase()
              .tests()
              .stream()
              .map(test -> new TestResult(schema.isValid(test.instance())))
              .toList();

      output.println(
          Sjf4j.toJsonString(new RunResponse(runRequest.seq(), results)));
    } catch (Exception e) {
      StringWriter stringWriter = new StringWriter();
      PrintWriter printWriter = new PrintWriter(stringWriter);
      e.printStackTrace(printWriter);
      RunErroredResponse response = new RunErroredResponse(
          runRequest.seq(), true,
          new ErrorContext(e.getMessage(), stackTraceToString(e)));
      output.println(Sjf4j.toJsonString(response));
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

record RunRequest(Object seq, @NodeProperty("case") TestCase testCase) {}

record RunResponse(Object seq, List<TestResult> results) {}

record RunSkippedResponse(Object seq, boolean skipped, String message,
                          String issue_url) {}

record RunErroredResponse(Object seq, boolean errored, ErrorContext context) {}

record ErrorContext(String message, String traceback) {}

record
    Implementation(String language, String name, String version,
                   List<String> dialects, String homepage, String documentation,
                   String issues, String source, String os, String os_version,
                   String language_version, List<Link> links) {}

record Link(String url, String description) {}

record TestCase(String description, String comment, Object schema,
                JsonObject registry, List<Test> tests) {}

record
    Test(String description, String comment, Object instance, boolean valid) {}

record TestResult(boolean valid) {}
