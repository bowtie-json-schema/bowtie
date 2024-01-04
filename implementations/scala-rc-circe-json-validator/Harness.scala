import io.circe.generic.auto._
import io.circe.parser.parse
import io.circe.syntax.EncoderOps
import io.circe.{Json, Decoder, ParsingFailure}
import java.io.InputStream
import java.util.Scanner
import java.util.jar.Manifest
import net.reactivecore.cjs.{Loader, ResolveFailure, Result}
import net.reactivecore.cjs.resolver.Downloader

class BowtieRcCirceJsonValidator {
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
    BowtieRcCirceJsonValidator.started = true
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
      "https://github.com/reactivecore/rc-circe-json-schema",
      "https://github.com/reactivecore/rc-circe-json-schema/issues",
      "https://github.com/reactivecore/rc-circe-json-schema",
      System.getProperty("os.name"),
      System.getProperty("os.version"),
      Runtime.version().toString,
      List()
    )
    StartResponse(startRequest.version, implementation).asJson.noSpaces
  }

  def dialect(node: Json): String = {
    if (!BowtieRcCirceJsonValidator.started) {
      throw new IllegalArgumentException("Not started!")
    }
    DialectResponse(true).asJson.noSpaces
  }

  def run(node: Json): String = {
    if (!BowtieRcCirceJsonValidator.started) {
      throw new IllegalArgumentException("Not started!")
    }

    val runRequest: RunRequest = decodeTo[RunRequest](node)
    val testCase = runRequest.testCase
    try {
      val registry: Map[String, Json] = testCase.registry.getOrElse(Map.empty)
      val downloader = new InMemoryDownloader(registry)
      val validator = Loader(downloader).fromJson(testCase.schema).right.get

      var resultArray = Vector.empty[Json]
      runRequest.testCase.tests.foreach { test =>
        val instance: String = test.instance.noSpaces
        val result = Json.obj("valid" -> validator.validate(test.instance).isSuccess.asJson)
        resultArray :+= result
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


class InMemoryDownloader(registry: Map[String, Json]) extends Downloader[Result] {
  override def loadJson(url: String): Result[Json] = {
    registry.get(url) match {
      case Some(json) => Right(json)
      case None => Left(ResolveFailure(s"Failed to resolve URL: $url"))
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

object RunRequest {}

case class RunResponse(seq: Json, results: Vector[Json])

case class RunSkippedResponse(seq: Json, skipped: Boolean = true, message: Option[String] = None)

case class RunErroredResponse(seq: Json, errored: Boolean = true, context: ErrorContext)

case class ErrorContext(message: String, traceback: String)

case class TestCase(description: String, comment: Option[String], schema: Json, registry: Option[Map[String, Json]], tests: List[Test])

case class Test(description: String, comment: Option[String], instance: Json, valid: Option[Boolean])

case class SkippedTest(skipped: Boolean = true, message: Option[String] = None)

case class TestSkip(description: String, message: String)

object BowtieRcCirceJsonValidator {
  var started: Boolean = false

  def main(args: Array[String]): Unit = {
    val input = new Scanner(System.in)
    while (true) {
      new BowtieRcCirceJsonValidator().operate(input.nextLine())
    }
  }
}
