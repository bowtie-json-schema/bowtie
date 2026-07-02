import io.circe.generic.auto._
import io.circe.parser.parse
import io.circe.syntax.EncoderOps
import io.circe.{Json, Decoder}
import java.io.InputStream
import java.nio.charset.StandardCharsets
import java.util.Scanner
import java.util.jar.Manifest
import io.github.jam01.json_schema.{Config, Dialect, MutableRegistry, Registry, Schema, Uri}
import io.github.jam01.json_schema as js

// The library resolves `$ref` purely against the supplied Registry - it doesn't bundle
// the official meta-schema documents itself, so a schema that `$ref`s its own dialect's
// meta-schema (e.g. the test suite's "remote ref, containing refs itself" case) needs
// them supplied. Falls back to the officially bundled 2020-12 meta-schemas whenever a
// URI isn't found in the per-case registry.
final class FallbackRegistry(primary: Registry, fallback: Registry) extends Registry {
  override def contains(schemaUri: Uri): Boolean = primary.contains(schemaUri) || fallback.contains(schemaUri)
  override def get(schemaUri: Uri): Option[Schema] = primary.get(schemaUri).orElse(fallback.get(schemaUri))
}

class Harness {
  def operate(line: String) = {
    val node: Json = parse(line) match {
      case Right(json)          => json
      case Left(parsingFailure) => throw parsingFailure
    }

    val cmd: String = (node \\ "cmd").headOption match {
      case Some(value) => value.asString.getOrElse("")
      case None        => throw new RuntimeException("Failed to get cmd")
    }
    cmd match {
      case "start"   => println(start(node))
      case "dialect" => println(dialect(node))
      case "run"     => println(run(node))
      case "stop"    => System.exit(0)
      case default   => throw new IllegalArgumentException(s"Unknown command: $default")
    }
  }

  def start(node: Json): String = {
    Harness.started = true
    val startRequest: StartRequest = decodeTo[StartRequest](node)
    if (startRequest.version != 1) {
      throw new IllegalArgumentException(s"Unsupported IHOP version: ${startRequest.version}")
    }

    val is: InputStream = getClass.getResourceAsStream("META-INF/MANIFEST.MF")
    val attributes = new Manifest(is).getMainAttributes

    val implementation: Implementation = Implementation(
      "scala",
      attributes.getValue("Implementation-Name"),
      attributes.getValue("Implementation-Version"),
      List("https://json-schema.org/draft/2020-12/schema"),
      "https://github.com/jam01/json-schema",
      "https://github.com/jam01/json-schema/issues",
      "https://github.com/jam01/json-schema",
      System.getProperty("os.name"),
      System.getProperty("os.version"),
      Runtime.version().toString,
      List()
    )
    StartResponse(startRequest.version, implementation).asJson.noSpaces
  }

  def dialect(node: Json): String = {
    if (!Harness.started) {
      throw new IllegalArgumentException("Not started!")
    }
    DialectResponse(true).asJson.noSpaces
  }

  def run(node: Json): String = {
    if (!Harness.started) {
      throw new IllegalArgumentException("Not started!")
    }

    val runRequest: RunRequest = decodeTo[RunRequest](node)
    val testCase = runRequest.testCase
    try {
      val registry = new MutableRegistry
      testCase.registry.getOrElse(Map.empty).foreach { case (uri, schemaJson) =>
        js.from(ujson.Readable, ujson.Readable.fromString(schemaJson.noSpaces),
          docbase = Uri(uri), registry = registry)
      }

      val schema: Schema = js.from(ujson.Readable, ujson.Readable.fromString(testCase.schema.noSpaces),
        registry = registry)
      val effectiveRegistry = new FallbackRegistry(registry, Harness.metaschemas)
      val validator = js.validator(schema, Config(dialect = Dialect.FullSpec, ffast = false), effectiveRegistry)

      val resultArray = testCase.tests.map { test =>
        val outcome = ujson.read(test.instance.noSpaces).transform(validator)
        Json.obj("valid" -> outcome.vvalid.asJson)
      }
      RunResponse(runRequest.seq, resultArray.toVector).asJson.noSpaces
    } catch {
      case e: Exception =>
        val error: ErrorContext = ErrorContext(e.getMessage, e.getStackTrace.mkString("\n"))
        RunErroredResponse(runRequest.seq, context = error).asJson.noSpaces
    }
  }

  def decodeTo[Request: Decoder](json: Json): Request = {
    json.as[Request] match {
      case Right(value)          => value
      case Left(decodingFailure) => throw decodingFailure
    }
  }
}

case class Implementation(language: String, name: String, version: String,
                          dialects: List[String], homepage: String, issues: String,
                          source: String, os: String, os_version: String,
                          language_version: String, links: List[Link])

case class Link(url: String, description: String)

case class StartRequest(version: Int)

case class StartResponse(version: Int, implementation: Implementation)

case class DialectRequest(dialect: String)

case class DialectResponse(ok: Boolean)

case class RunRequest(seq: Json, testCase: TestCase)
implicit val decodeRunRequest: Decoder[RunRequest] = Decoder.forProduct2("seq", "case")(RunRequest.apply)

case class RunResponse(seq: Json, results: Vector[Json])

case class RunSkippedResponse(seq: Json, skipped: Boolean = true, message: Option[String] = None)

case class RunErroredResponse(seq: Json, errored: Boolean = true, context: ErrorContext)

case class ErrorContext(message: String, traceback: String)

case class TestCase(description: String, comment: Option[String], schema: Json, registry: Option[Map[String, Json]], tests: List[Test])

case class Test(description: String, comment: Option[String], instance: Json, valid: Option[Boolean])

object Harness {
  var started: Boolean = false

  // The official JSON Schema 2020-12 meta-schemas, bundled as resources and pre-registered
  // once so `$ref`s to them (e.g. a schema validating against its own dialect) resolve.
  val metaschemas: MutableRegistry = {
    val reg = new MutableRegistry
    Seq(
      "schema.json" -> "https://json-schema.org/draft/2020-12/schema",
      "meta_core.json" -> "https://json-schema.org/draft/2020-12/meta/core",
      "meta_applicator.json" -> "https://json-schema.org/draft/2020-12/meta/applicator",
      "meta_unevaluated.json" -> "https://json-schema.org/draft/2020-12/meta/unevaluated",
      "meta_validation.json" -> "https://json-schema.org/draft/2020-12/meta/validation",
      "meta_meta-data.json" -> "https://json-schema.org/draft/2020-12/meta/meta-data",
      "meta_format-annotation.json" -> "https://json-schema.org/draft/2020-12/meta/format-annotation",
      "meta_content.json" -> "https://json-schema.org/draft/2020-12/meta/content",
    ).foreach { case (resource, uri) =>
      val is = getClass.getResourceAsStream(s"/metaschemas/$resource")
      val text = new String(is.readAllBytes(), StandardCharsets.UTF_8)
      js.from(ujson.Readable, ujson.Readable.fromString(text), docbase = Uri(uri), registry = reg)
    }
    reg
  }

  def main(args: Array[String]): Unit = {
    val input = new Scanner(System.in)
    while (true) {
      new Harness().operate(input.nextLine())
    }
  }
}
