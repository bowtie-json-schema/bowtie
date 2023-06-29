import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
// import dev.harrel.jsonschema.SchemaResolver;
// import dev.harrel.jsonschema.Validator;
// import dev.harrel.jsonschema.ValidatorFactory;
// import java.io.*;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.jar.Attributes;
import java.util.jar.Manifest;

public class BowtieJsonSchemaValidator {

  private static final String[] DIALECTS = {
    "https://json-schema.org/draft/2020-12/schema",
    "https://json-schema.org/draft/2019-09/schema",
    "http://json-schema.org/draft-07/schema#",
    "http://json-schema.org/draft-06/schema#",
    "http://json-schema.org/draft-04/schema#",
  };
  private final ObjectMapper objectMapper = new ObjectMapper()
    .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
  private final ValidatorFactory validatorFactory = new ValidatorFactory();
  private final PrintStream output;

  public static void main(String[] args) {
    BufferedReader reader = new BufferedReader(
      new InputStreamReader(System.in)
    );
    new BowtieJsonSchemaValidator(System.out).run(reader);
  }

  public BowtieJsonSchemaValidator(PrintStream output) {
    this.output = output;
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
        default -> throw new IllegalArgumentException(
          "Unknown cmd [%s]".formatted(cmd)
        );
      }
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    }
  }

  private void start(JsonNode node) throws IOException {
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

    List<String> dialectList = Arrays.asList(DIALECTS);
    StartResponse startResponse = new StartResponse(
      1,
      true,
      new Implementation(
        "java",
        attributes.getValue("Implementation-Name"),
        attributes.getValue("Implementation-Version"),
        List.of(DRAFT_2020),
        "https://github.com/harrel56/json-schema",
        "https://github.com/harrel56/json-schema/issues",
        System.getProperty("os.name"),
        System.getProperty("os.version"),
        System.getProperty("java.vendor.version"),
        List.of(
          new Link("https://harrel.dev", "Group homepage"),
          new Link(
            createMavenUrl("Implementation", attributes),
            "Maven Central - implementation"
          ),
          new Link(
            createMavenUrl("Provider", attributes),
            "Maven Central - used JSON provider"
          )
        )
      )
    );
    output.println(objectMapper.writeValueAsString(startResponse));
  }
}
