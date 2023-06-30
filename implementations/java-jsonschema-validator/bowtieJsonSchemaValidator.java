// import com.fasterxml.jackson.annotation.JsonProperty;
// import com.fasterxml.jackson.core.JsonProcessingException;
// import com.fasterxml.jackson.core.type.TypeReference;
// import com.fasterxml.jackson.databind.DeserializationFeature;
// import com.fasterxml.jackson.databind.JsonNode;
// import com.fasterxml.jackson.databind.ObjectMapper;
import com.networknt.schema.JsonSchemaFactory;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.jar.Attributes;
import java.util.jar.Manifest;

// public class BowtieJsonSchemaValidator {

//   private static final List<String> DIALECTS = List.of(
//       "https://json-schema.org/draft/2020-12/schema",
//       "https://json-schema.org/draft/2019-09/schema",
//       "http://json-schema.org/draft-07/schema#",
//       "http://json-schema.org/draft-06/schema#",
//       "http://json-schema.org/draft-04/schema#");

//   private static final String RECOGNIZING_IDENTIFIERS = "Determining if a specific location is a schema or not is not supported.";
//   private static final Map<String, String> UNSUPPORTED = Map.of(
//       "$id inside an enum is not a real identifier", RECOGNIZING_IDENTIFIERS,
//       "$id inside an unknown keyword is not a real identifier",
//       RECOGNIZING_IDENTIFIERS,
//       "$anchor inside an enum is not a real identifier",
//       RECOGNIZING_IDENTIFIERS,
//       "schema that uses custom metaschema with with no validation vocabulary",
//       "Vocabularies are not yet supported.",
//       "ignore unrecognized optional vocabulary",
//       "Vocabularies are not yet supported.");

//   private final ObjectMapper objectMapper = new ObjectMapper()
//       .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
//   private final JsonSchemaFactory factory = JsonSchemaFactory.getInstance();
//   private final PrintStream output;

//   public static void main(String[] args) {
//     BufferedReader reader = new BufferedReader(
//         new InputStreamReader(System.in));
//     new BowtieJsonSchemaValidator(System.out).run(reader);
//   }

//   public BowtieJsonSchemaValidator(PrintStream output) {
//     this.output = output;
//   }

//   private void run(BufferedReader reader) {
//     reader.lines().forEach(this::handle);
//   }

//   private void handle(String data) {
//     try {
//       JsonNode node = objectMapper.readTree(data);
//       String cmd = node.get("cmd").asText();
//       switch (cmd) {
//         case "start" -> start(node);
//         // case "dialect" -> dialect(node);
//         // case "run" -> run(node);
//         case "stop" -> System.exit(0);
//         default -> throw new IllegalArgumentException(
//             "Unknown cmd [%s]".formatted(cmd));
//       }
//     } catch (IOException e) {
//       throw new UncheckedIOException(e);
//     }
//   }

//   private void start(JsonNode node) throws IOException {
//     StartRequest startRequest = objectMapper.treeToValue(
//       node,
//       StartRequest.class
//     );
//     if (startRequest.version() != 1) {
//       throw new IllegalArgumentException(
//         "Unsupported IHOP version [%d]".formatted(startRequest.version())
//       );
//     }

//     InputStream is = getClass().getResourceAsStream("META-INF/MANIFEST.MF");
//     var attributes = new Manifest(is).getMainAttributes();

//     List<String> dialectList = DIALECTS;
//     StartResponse startResponse = new StartResponse(
//       1,
//       true,
//       new Implementation(
//         "java",
//         attributes.getValue("Implementation-Name"),
//         attributes.getValue("Implementation-Version"),
//         DIALECTS,
//         "https://github.com/networknt/json-schema-validator/",
//         "https://github.com/networknt/json-schema-validator/issues",
//         System.getProperty("os.name"),
//         System.getProperty("os.version"),
//         System.getProperty("java.vendor.version")
//       )
//     );
//     output.println(objectMapper.writeValueAsString(startResponse));
//   }
// }

//   // private void dialect(JsonNode node) throws JsonProcessingException {
//   //   DialectRequest dialectRequest = objectMapper.treeToValue(node, DialectRequest.class);

//   //   String requestedDialect = dialectRequest.dialect();
//   //   boolean isSupportedDialect = DIALECTS.contains(requestedDialect);

//   //   if (isSupportedDialect) {
//   //     JsonSchema schema = schemaFactory.getSchema(requestedDialect);
//   //     Set<ValidationMessage> validationMessages = schema.validate(jsonInstance);

//   //     if (validationMessages.isEmpty()) {
//   //       System.out.println("Validation succeeded. JSON is valid.");
//   //       output.println(objectMapper.writeValueAsString(new DialectResponse(true)));
//   //     } else {
//   //       System.out.println("Validation failed. JSON is invalid.");
//   //       for (ValidationMessage message : validationMessages) {
//   //         System.out.println(message.getMessage());
//   //       }
//   //       output.println(objectMapper.writeValueAsString(new DialectResponse(false)));
//   //     }
//   //   } else {
//   //     output.println(objectMapper.writeValueAsString(new DialectResponse(false)));
//   //   }
//   // }

//   // private void run(JsonNode node) throws JsonProcessingException {
//   //   RunRequest runRequest = objectMapper.treeToValue(node, RunRequest.class);
//   //   try {
//   //     if (UNSUPPORTED.containsKey(runRequest.testCase().description())) {
//   //       RunSkippedResponse response = new RunSkippedResponse(runRequest.seq(), true,
//   //           UNSUPPORTED.get(runRequest.testCase().description()), null);
//   //       output.println(objectMapper.writeValueAsString(response));
//   //       return;
//   //     }

//   //     // if (runRequest.testCase().registry() != null) {
//   //     //   validatorFactory.withSchemaResolver(new RegistrySchemaResolver(runRequest.testCase().registry()));
//   //     // }
//   //     JsonSchemaFactory schemaFactory = JsonSchemaFactory.getInstance();
//   //     JsonSchema schema = schemaFactory.getSchema(new RegistrySchemaResolver(runRequest.testCase().registry()));
//   //     List<TestResult> results = runRequest.testCase().tests().stream().map(test -> {
//   //       Set<ValidationMessage> validationMessages = schema.validate(test.instance());
//   //       // Validator.Result result = validatorFactory.validate(runRequest.testCase().schema(), test.instance());
//   //       // return new TestResult(result.isValid());
//   //       if (validationMessages.isEmpty()) {
//   //           System.out.println("Validation succeeded. JSON is valid.");
//   //           return new TestResult(true);
//   //       } else {
//   //           System.out.println("Validation failed. JSON is invalid.");
//   //           for (ValidationMessage message : validationMessages) {
//   //               System.out.println(message.getMessage());
//   //           }
//   //           return new TestResult(false);
//   //       }
//   //     }).toList();
//   //     output.println(objectMapper.writeValueAsString(new RunResponse(runRequest.seq(), results)));
//   //   } catch (Exception e) {
//   //     StringWriter stringWriter = new StringWriter();
//   //     PrintWriter printWriter = new PrintWriter(stringWriter);
//   //     e.printStackTrace(printWriter);
//   //     RunErroredResponse response = new RunErroredResponse(runRequest.seq(), true,
//   //         new ErrorContext(e.getMessage(), stackTraceToString(e)));
//   //     output.println(objectMapper.writeValueAsString(response));
//   //   }
//   // }

//   // private String stackTraceToString(Exception e) {
//   //   StringWriter stringWriter = new StringWriter();
//   //   e.printStackTrace(new PrintWriter(stringWriter));
//   //   return stringWriter.toString();
//   // }

// //   class RegistrySchemaResolver implements SchemaResolver {
// //     private final Map<String, JsonNode> registry;

// //     public RegistrySchemaResolver(JsonNode registryNode) {
// //       this.registry = objectMapper.convertValue(registryNode, new TypeReference<>() {
// //       });
// //     }

// //     @Override
// //     public SchemaResolver.Result resolve(String uri) {
// //       return Optional.ofNullable(registry.get(uri))
// //           .map(Result::fromProviderNode)
// //           .orElse(SchemaResolver.Result.empty());
// //     }
// //   }
// // }

// record StartRequest(int version) {
// }

// record StartResponse(int version, boolean ready, Implementation implementation) {
// }

// // record DialectRequest(String dialect) {
// // }

// // record DialectResponse(boolean ok) {
// // }

// // record RunRequest(JsonNode seq, @JsonProperty("case") TestCase testCase) {
// // }

// // record RunResponse(JsonNode seq, List<TestResult> results) {
// // }

// // record RunSkippedResponse(JsonNode seq, boolean skipped, String message, String issue_url) {
// // }

// // record RunErroredResponse(JsonNode seq, boolean errored, ErrorContext context) {
// // }

// // record ErrorContext(String message, String traceback) {
// // }

// // record TestCase(String description, String comment, JsonNode schema, JsonNode registry, List<Test> tests) {
// // }

// // record Test(String description, String comment, JsonNode instance, boolean valid) {
// // }

// // record TestResult(boolean valid) {
// // }

// record Implementation(String language,
//                       String name,
//                       String version,
//                       List<String> dialects,
//                       String homepage,
//                       String issues,
//                       String os,
//                       String os_version,
//                       String language_version) {}

public class BowtieJsonSchemaValidator {

    private static final JsonSchemaFactory schemaFactory = JsonSchemaFactory.getInstance();
    private static boolean STARTED = false;

    private static final List<String> DIALECTS = List.of(
            "https://json-schema.org/draft/2020-12/schema",
            "https://json-schema.org/draft/2019-09/schema",
            "http://json-schema.org/draft-07/schema#",
            "http://json-schema.org/draft-06/schema#",
            "http://json-schema.org/draft-04/schema#"
    );

    public static void main(String[] args) throws IOException {
        BufferedReader reader = new BufferedReader(
                new InputStreamReader(System.in)
        );

        Map<String, Command> commands = new HashMap<>();
        commands.put(
                "start",
                request -> {
                    assert request.getInt("version") == 1 : "Wrong version!";
                    STARTED = true;

                    Manifest manifest = getManifest();
                    Attributes attributes = manifest.getMainAttributes();

                    JSONObject implementation = new JSONObject();
                    implementation.put("language", "java");
                    implementation.put("name", attributes.getValue("Implementation-Name"));
                    implementation.put("version", attributes.getValue("Implementation-Version"));
                    implementation.put("homepage", "https://github.com/networknt/json-schema-validator/");
                    implementation.put("issues", "https://github.com/networknt/json-schema-validator/issues");
                    implementation.put("os_name", System.getProperty("os.name"));
                    implementation.put("os_version", System.getProperty("os.version"));
                    implementation.put("language_version", System.getProperty("java.vendor.version"));
                    implementation.put("dialects", DIALECTS);

                    JSONObject response = new JSONObject();
                    response.put("ready", true);
                    response.put("version", 1);
                    response.put("implementation", implementation);
                    return response;
                }
        );
        commands.put(
                "stop",
                request -> {
                    assert STARTED : "Not started!";
                    System.exit(0);
                    return null;
                }
        );

        String line;
        while ((line = reader.readLine()) != null) {
            JSONObject json = new JSONObject(line);
            String cmd = json.getString("cmd");

            if (commands.containsKey(cmd)) {
                Command command = commands.get(cmd);
                JSONObject response = command.execute(json);
                System.out.println(response.toString());
            }
        }
    }

    private static Manifest getManifest() {
        try {
            ClassLoader classLoader = BowtieJsonSchemaValidator.class.getClassLoader();
            return new Manifest(classLoader.getResourceAsStream("META-INF/MANIFEST.MF"));
        } catch (IOException e) {
            e.printStackTrace();
            throw new RuntimeException("Failed to load manifest");
        }
    }

    interface Command {
        JSONObject execute(JSONObject request);
    }
}
