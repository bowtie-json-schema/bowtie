import io.github.optimumcode.json.schema.ErrorCollector
import io.github.optimumcode.json.schema.JsonSchema
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.io.BufferedReader
import java.io.BufferedWriter
import java.io.InputStreamReader
import java.util.jar.Attributes
import java.util.jar.Manifest

fun main() {
    val input = BufferedReader(InputStreamReader(System.`in`))
    val outputWriter = System.out.bufferedWriter()
    try {
        val json = Json {
            ignoreUnknownKeys = true
            prettyPrint = false
            encodeDefaults = true
        }
        val processor = BowtieSampsonSchemaValidatorLauncher(outputWriter, json)
        input.lines().forEach {
            val command = json.decodeFromString(Command.serializer(), it)
            processor.handle(command)
        }
    } finally {
        outputWriter.flush()
    }
}

private val SUPPORTED_DIALECTS: Set<String> = hashSetOf(
    "http://json-schema.org/draft-07/schema#",
)

// TODO: remove when remote ref support is added
/**
 * All these cases are ignored because they contain remote refs
 * Library does not support them yet.
 */
private val IGNORED_CASES: Set<String> = hashSetOf(
    "validate definition against metaschema",
    "base URI change - change folder",
    "base URI change - change folder in subschema",
    "base URI change",
    "retrieved nested refs resolve relative to their URI not \$id",
    "\$ref to \$ref finds location-independent \$id",
)

enum class Result { CONTINUE, STOP }

class BowtieSampsonSchemaValidatorLauncher(
    private val writer: BufferedWriter,
    private val json: Json,
) {
    private var started: Boolean = false
    private var currentDialect: String = ""
    private val libraryName: String
    private val libraryVersion: String
    private val libraryHomepage: String
    private val libraryIssues: String

    init {
        val attributes: Attributes = javaClass.getResourceAsStream("META-INF/MANIFEST.MF").use {
            requireNotNull(it) { "cannot find manifest file" }
            Manifest(it).mainAttributes
        }
        with(attributes) {
            libraryName = getValue("Implementation-Name")
            libraryVersion = getValue("Implementation-Version")
            libraryHomepage = getValue("Implementation-Homepage")
            libraryIssues = getValue("Implementation-Issues")
        }
    }

    fun handle(command: Command): Result {
        return when (command) {
            is Command.Start -> handleStart(command)
            is Command.Dialect -> handleDialect(command)
            is Command.Run -> {
                handleRun(command)
                Result.CONTINUE
            }

            Command.Stop -> Result.STOP
        }
    }

    private fun shouldSkipCase(caseDescription: String): String? {
        return when {
            caseDescription.endsWith(" format") -> "impl does not support format assertion"
            caseDescription in IGNORED_CASES || caseDescription.contains("remote ref") ->
                "impl does not support remote schema loading yet"
            else -> null
        }
    }

    private fun shouldSkipTest(caseDescription: String, testDescription: String): String? {
        return null
    }

    private fun handleRun(command: Command.Run) {
        requireStarted()
        requireDialect()
        shouldSkipCase(command.case.description)?.also { reason ->
            writer.writeLine(
                json.encodeToString(
                    RunResponse.Skipped(
                        seq = command.seq,
                        message = "case '${command.case.description}' in the list of ignored cases: $reason",
                    ),
                ),
            )
            return
        }
        val schemaDefinition = command.case.schema
        // TODO: ability to specify certain dialect
        val schema = try {
            JsonSchema.fromJsonElement(schemaDefinition)
        } catch (ex: Exception) {
            writer.writeLine(
                json.encodeToString(
                    RunResponse.ExecutionError(
                        seq = command.seq,
                        context = ErrorContext(
                            message = "cannot create JSON schema",
                            traceback = ex.stackTraceToString(),
                        ),
                    ),
                ),
            )
            return
        }
        val results: List<TestResult> = command.case.tests.map { test ->
            runCatching {
                shouldSkipTest(command.case.description, test.description)?.let { reason ->
                    TestResult.Skipped(
                        message = "test '${test.description}' in the list of ignored tests: $reason",
                    )
                } ?: run {
                    val valid = schema.validate(test.instance, ErrorCollector.EMPTY)
                    TestResult.Executed(
                        valid = test.valid?.let { it == valid } ?: valid,
                    )
                }
            }.getOrElse {
                TestResult.ExecutionError(
                    context = ErrorContext(
                        message = "cannot execute test ${test.description}",
                        traceback = it.stackTraceToString(),
                    ),
                )
            }
        }
        writer.writeLine(
            json.encodeToString(
                RunResponse.Result(
                    seq = command.seq,
                    results = results,
                ),
            ),
        )
    }

    private fun requireDialect() {
        require(currentDialect.isNotEmpty()) { "dialect is not set" }
    }

    private fun handleDialect(command: Command.Dialect): Result {
        requireStarted()
        val supported = command.dialect in SUPPORTED_DIALECTS
        writer.writeLine(
            json.encodeToString(
                DialectResponse(
                    ok = supported,
                ),
            ),
        )
        if (supported) {
            currentDialect = command.dialect
        }
        return Result.CONTINUE
    }

    private fun handleStart(command: Command.Start): Result {
        started = true
        writer.writeLine(
            json.encodeToString(
                StartResponse(
                    ready = true,
                    version = 1,
                    implementation = Implementation(
                        name = libraryName,
                        version = libraryVersion,
                        homepage = libraryHomepage,
                        dialects = SUPPORTED_DIALECTS,
                        issues = libraryIssues,
                    ),
                ),
            ),
        )
        return Result.CONTINUE
    }

    private fun requireStarted() {
        require(started) { "start command was not received" }
    }
}

private fun BufferedWriter.writeLine(string: String) {
    write(string)
    newLine()
    flush()
}
