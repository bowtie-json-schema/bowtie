import java.io._
import io.circe.generic.auto._
import io.circe.parser.parse
import io.circe.syntax.EncoderOps
import io.circe.{Json, Decoder, ParsingFailure}
import io.circe.generic.extras.{Configuration, ConfiguredJsonCodec, JsonKey}
import java.util.jar.Manifest
import main.MainClass
import java.util.Scanner

class Harness {
  val NOT_IMPLEMENTED: String = "This case is not yet implemented."

  val UNSUPPORTED_CASES: Map[String, String] = Map(
    "escaped pointer ref" -> NOT_IMPLEMENTED,
    "empty tokens in $ref json-pointer" -> NOT_IMPLEMENTED,
    "schema that uses custom metaschema with with no validation vocabulary" -> NOT_IMPLEMENTED,
    "small multiple of large integer" -> NOT_IMPLEMENTED
  )

  // List of specific tests of a case that are not supported
  val UNSUPPORTED_TESTS: Map[String, TestSkip] = Map(
    "minLength validation" -> TestSkip("one supplementary Unicode code point is not long enough", NOT_IMPLEMENTED),
    "maxLength validation" -> TestSkip("two supplementary Unicode code points is long enough", NOT_IMPLEMENTED),
    // The above two tests were renamed to the following two tests. We keep the old names for backward compatibility.
    "minLength validation" -> TestSkip("one grapheme is not long enough", NOT_IMPLEMENTED),
    "maxLength validation" -> TestSkip("two graphemes is long enough", NOT_IMPLEMENTED)
  )

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
      "https://gitlab.lip6.fr/jsonschema/modernjsonschemavalidator",
      "https://gitlab.lip6.fr/jsonschema/modernjsonschemavalidator/issues",
      "https://gitlab.lip6.fr/jsonschema/modernjsonschemavalidator",
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
    try {
      val caseDescription = runRequest.testCase.description
      if (UNSUPPORTED_CASES.contains(caseDescription)) {
        return RunSkippedResponse(runRequest.seq, true, Some(NOT_IMPLEMENTED)).asJson.noSpaces
      }

      val registryMap: Map[String, String] = runRequest.testCase.registry
        .flatMap { node =>
          node.as[Map[String, Json]].toOption.map { jsonMap => jsonMap.mapValues(_.noSpaces).toMap }
          node.as[Map[String, Json]].toOption.map { jsonMap => jsonMap.mapValues(_.noSpaces).toMap }
        }
        .getOrElse(null)

      var resultArray = Vector.empty[Json]
      runRequest.testCase.tests.foreach { test =>
        val testDescription: String = test.description
        val instance: String = test.instance.noSpaces

        if (UNSUPPORTED_TESTS.contains(caseDescription) && UNSUPPORTED_TESTS(caseDescription).description == testDescription) {
          resultArray :+= SkippedTest(message = Some(UNSUPPORTED_TESTS(caseDescription).message)).asJson
        } else {
          val schema: String = runRequest.testCase.schema.noSpaces

          val result: Json = Json.obj("valid" -> MainClass.validateInstance(schema, instance, registryMap).asJson)
          resultArray :+= result
        }
      }
      RunResponse(runRequest.seq, resultArray).asJson.noSpaces
    } catch {
      case e: Exception =>
        val error: ErrorContext = ErrorContext(e.getMessage(), e.getStackTrace().mkString("\n"))
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

@ConfiguredJsonCodec
case class RunRequest(seq: Json, @JsonKey("case") testCase: TestCase)

object RunRequest {
  implicit val config: Configuration = Configuration.default.withSnakeCaseMemberNames.withDefaults
}

case class RunResponse(seq: Json, results: Vector[Json])

case class RunSkippedResponse(seq: Json, skipped: Boolean = true, message: Option[String] = None)

case class RunErroredResponse(seq: Json, errored: Boolean = true, context: ErrorContext)

case class ErrorContext(message: String, traceback: String)

case class TestCase(description: String, comment: Option[String], schema: Json, registry: Option[Json], tests: List[Test])

case class Test(description: String, comment: Option[String], instance: Json, valid: Option[Boolean])

case class SkippedTest(skipped: Boolean = true, message: Option[String] = None)

case class TestSkip(description: String, message: String)

object Harness {
  var started: Boolean = false

  def main(args: Array[String]): Unit = {
    val input = new Scanner(System.in)
    while (true) {
      new Harness().operate(input.nextLine())
    }
  }
}
