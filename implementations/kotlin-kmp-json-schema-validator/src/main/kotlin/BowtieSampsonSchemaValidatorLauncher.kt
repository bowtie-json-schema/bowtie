import io.github.optimumcode.json.schema.ErrorCollector
import io.github.optimumcode.json.schema.JsonSchema
import io.github.optimumcode.json.schema.JsonSchemaLoader
import io.github.optimumcode.json.schema.SchemaType
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.ClassDiscriminatorMode
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonPrimitive
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
            classDiscriminatorMode = ClassDiscriminatorMode.NONE
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
    "https://json-schema.org/draft/2019-09/schema",
    "https://json-schema.org/draft/2020-12/schema",
)

enum class Result { CONTINUE, STOP }

class BowtieSampsonSchemaValidatorLauncher(
    private val writer: BufferedWriter,
    private val json: Json,
) {
    private var started: Boolean = false
    private var currentDialect: SchemaType? = null
    private val libraryVersion: String
    private val libraryHomepage: String
    private val libraryIssues: String
    private val librarySource: String
    private var testFilter: TestFilter = TestFilterDraft7

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

    private fun handleRun(command: Command.Run) {
        requireStarted()
        testFilter.shouldSkipCase(command.case.description)?.also { reason ->
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
            loadSchema(command, schemaDefinition)
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

    private fun loadSchema(
        command: Command.Run,
        schemaDefinition: JsonElement,
    ): JsonSchema = JsonSchemaLoader.create()
        .apply {
            currentDialect?.also(this::registerWellKnown)
            for ((uri, schema) in command.case.registry) {
                if (skipSchema(uri, schema)) {
                    continue
                }
                @Suppress("detekt:TooGenericExceptionCaught")
                try {
                    register(schema, uri)
                } catch (ex: Exception) {
                    throw IllegalStateException("cannot register schema for URI '$uri'", ex)
                }
            }
        }.fromJsonElement(schemaDefinition, currentDialect)

    private fun skipSchema(uri: String, schema: JsonElement): Boolean {
        if (uri.contains("draft4", ignoreCase = true)) {
            // skip draft4 schemas
            return true
        }
        // ignore schemas for unsupported drafts
        return schema is JsonObject &&
            schema["\$schema"]
                ?.jsonPrimitive
                ?.content
                .let { it != null && SchemaType.find(it) == null }
    }

    private fun runCase(command: Command.Run, schema: JsonSchema) {
        val results: List<TestResult> = command.case.tests.map { test ->
            runCatching {
                testFilter.shouldSkipTest(command.case.description, test.description)?.let { reason ->
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
        currentDialect = null
        val supported = command.dialect in SUPPORTED_DIALECTS
        writer.writeLine(
            json.encodeToString(
                DialectResponse(
                    ok = supported,
                ),
            ),
        )
        if (supported) {
            currentDialect = SchemaType.find(command.dialect)
            testFilter = getFilter(currentDialect)
        }
        return Result.CONTINUE
    }

    private fun handleStart(): Result {
        started = true
        writer.writeLine(
            json.encodeToString(
                StartResponse(
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
