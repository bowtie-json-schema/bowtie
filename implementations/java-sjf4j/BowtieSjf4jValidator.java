
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.PrintStream;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.io.UncheckedIOException;
import java.net.URI;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.jar.Manifest;
import org.sjf4j.JsonObject;
import org.sjf4j.node.Nodes;
import org.sjf4j.Sjf4j;
import org.sjf4j.annotation.node.NodeProperty;
import org.sjf4j.schema.JsonSchema;
import org.sjf4j.schema.SchemaDialect;
import org.sjf4j.schema.SchemaPlan;
import org.sjf4j.schema.SchemaRegistry;


public class BowtieSjf4jValidator {

  public static void main(String[] args) {
    BufferedReader reader =
        new BufferedReader(new InputStreamReader(System.in));
    new BowtieSjf4jValidator(System.out).run(reader);
  }

  private static final List<String> DIALECTS =
      List.of("https://json-schema.org/draft/2020-12/schema",
              "https://json-schema.org/draft/2019-09/schema",
              "http://json-schema.org/draft-07/schema#");

  private static final Sjf4j JSONS = Sjf4j.global();

  private final PrintStream output;
  private final String startResponseJson;
  private boolean started;
  private final String dialectOkJson =
      JSONS.toJsonString(new DialectResponse(true));
  private SchemaRegistry registry;


  public BowtieSjf4jValidator(PrintStream output) {
    this.output = output;
    this.startResponseJson = buildStartResponseJson();
  }

  private void run(BufferedReader reader) {
    try {
      String line;
      while ((line = reader.readLine()) != null) {
        handle(line);
      }
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
  }

  private void handle(String data) {
    JsonObject jo = JsonObject.fromJson(data);
    String cmd = jo.getString("cmd");
    switch (cmd) {
    case "start" -> start(jo);
    case "dialect" -> dialect(jo);
    case "run" -> runCase(jo);
    case "stop" -> System.exit(0);
    default ->
      throw new IllegalArgumentException("Unknown cmd [%s]".formatted(cmd));
    }
  }

  private void start(JsonObject jo) {
    started = true;
    StartRequest req = jo.toNode(StartRequest.class);
    if (req.version() != 1) {
      throw new IllegalArgumentException(
          "Unsupported IHOP version [%d]".formatted(req.version()));
    }
    output.println(startResponseJson);
  }

  private void dialect(JsonObject jo) {
    ensureStarted();

    String dialect = jo.getString("dialect");
    switch (dialect) {
      case "https://json-schema.org/draft/2020-12/schema":
        registry = new SchemaRegistry(SchemaDialect.DRAFT_2020_12);
        break;
      case "https://json-schema.org/draft/2019-09/schema":
        registry = new SchemaRegistry(SchemaDialect.DRAFT_2019_09);
        break;
      case "https://json-schema.org/draft-07/schema":
      case "http://json-schema.org/draft-07/schema#":
        registry = new SchemaRegistry(SchemaDialect.DRAFT_07);
        break;
      default:
        throw new IllegalArgumentException("Unsupported dialect " + dialect);
    }
    output.println(dialectOkJson);
  }

  private void runCase(JsonObject jo) {
    ensureStarted();
    if (registry == null) {
      throw new IllegalArgumentException("No dialect configured!");
    }

    try {
      JsonObject tcJo = jo.getJsonObject("case");

      Map<String, Object> registryMap = tcJo.getMap("registry");
      if (registryMap != null) {
        for (Map.Entry<String, Object> e : registryMap.entrySet()) {
          URI id = URI.create(e.getKey());
          if (registry.contains(id)) {
            registry.index(id, JsonSchema.fromNode(e.getValue()));
          }
        }
      }

      JsonSchema schema = JsonSchema.fromNode(tcJo.getNode("schema"));
      SchemaPlan plan = schema.createPlan(registry);

      List<Object> tests = tcJo.getList("tests");
      List<TestResult> results = new ArrayList<>(tests.size());
      for (Object t : tests) {
        Object instance = Nodes.getInObject(t, "instance");
        results.add(new TestResult(plan.isValid(instance)));
      }

      output.println(
          JSONS.toJsonString(new RunResponse(jo.getNode("seq"), results)));
    } catch (Exception e) {
      output.println(JSONS.toJsonString(new RunErroredResponse(
          jo.getNode("seq"), true,
          new ErrorContext(e.getMessage(), stackTraceToString(e)))));
    }
  }

  private void ensureStarted() {
    if (!started) {
      throw new IllegalArgumentException("Not started!");
    }
  }

  private String buildStartResponseJson() {
    try (InputStream is =
             getClass().getResourceAsStream("/META-INF/MANIFEST.MF")) {
      if (is == null) {
        throw new IllegalStateException("Missing MANIFEST.MF");
      }
      var attributes = new Manifest(is).getMainAttributes();

      String fullName =
          "%s-%s".formatted(attributes.getValue("Implementation-Group"),
                              attributes.getValue("Implementation-Name"));

      StartResponse startResponse = new StartResponse(
          1,
          new Implementation(
              "java", fullName, attributes.getValue("Implementation-Version"),
              DIALECTS, "https://sjf4j.org",
              "https://github.com/sjf4j-projects/sjf4j",
              "https://github.com/sjf4j-projects/sjf4j/issues",
              "https://github.com/sjf4j-projects/sjf4j",
              System.getProperty("os.name"), System.getProperty("os.version"),
              Runtime.version().toString(), List.of()));
      return JSONS.toJsonString(startResponse);
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
  }

  private static String stackTraceToString(Throwable t) {
    StringWriter sw = new StringWriter(512);
    t.printStackTrace(new PrintWriter(sw));
    return sw.toString();
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
