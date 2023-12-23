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
    private val libraryVersion: String
    private val libraryHomepage: String
    private val libraryIssues: String
    private val librarySource: String

    init {
        val attributes: Attributes = javaClass.getResourceAsStream("META-INF/MANIFEST.MF").use {
            requireNotNull(it) { "cannot find manifest file" }
            Manifest(it).mainAttributes
        }
        with(attributes) {
            libraryVersion = getValue("Implementation-Version")
            libraryHomepage = getValue("Implementation-Homepage")
            libraryIssues = getValue("Implementation-Issues")
            librarySource = getValue("Implementation-Source")
        }
    }

    fun handle(command: Command): Result {
        return when (command) {
            is Command.Start -> handleStart()
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
            caseDescription.endsWith(" format") -> "the format keyword is not yet supported"
            caseDescription in IGNORED_CASES || caseDescription.contains("remote ref") ->
                "remote schema loading is not yet supported"
            else -> null
        }
    }

    @Suppress("detekt:UnusedPrivateMember", "detekt:FunctionOnlyReturningConstant")
    private fun shouldSkipTest(caseDescription: String, testDescription: String): String? {
        return null
    }

    private fun handleRun(command: Command.Run) {
        requireStarted()
        shouldSkipCase(command.case.description)?.also { reason ->
            writer.writeLine(
                json.encodeToString(
                    RunResponse.Skipped(
                        seq = command.seq,
                        message = reason,
                    ),
                ),
            )
            return
        }
        val schemaDefinition = command.case.schema

        @Suppress("detekt:TooGenericExceptionCaught")
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
        runCase(command, schema)
    }

    private fun runCase(command: Command.Run, schema: JsonSchema) {
        val results: List<TestResult> = command.case.tests.map { test ->
            runCatching {
                shouldSkipTest(command.case.description, test.description)?.let { reason ->
                    TestResult.Skipped(message = reason)
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

    private fun handleStart(): Result {
        started = true
        writer.writeLine(
            json.encodeToString(
                StartResponse(
                    ready = true,
                    version = 1,
                    implementation = Implementation(
                        name = "kmp-json-schema-validator",
                        version = libraryVersion,
                        homepage = libraryHomepage,
                        dialects = SUPPORTED_DIALECTS,
                        issues = libraryIssues,
                        source = librarySource,
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
