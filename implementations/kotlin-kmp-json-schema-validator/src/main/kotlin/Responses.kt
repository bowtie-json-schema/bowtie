import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement

@Serializable
class StartResponse(
    val version: Int,
    val implementation: Implementation,
)

@Suppress("LongParameterList", "ConstructorParameterNaming")
@Serializable
class Implementation(
    val language: String = "kotlin",
    val name: String = "kmp-json-schema-validator",
    val version: String,
    val dialects: Set<String>,
    val homepage: String,
    val issues: String,
    val source: String,
    val os: String,
    val os_version: String,
    val language_version: String,
)

@Serializable
class DialectResponse(
    /**
     * Whether this dialect is supported or not
     */
    val ok: Boolean,
)

@Serializable
sealed class RunResponse {
    abstract val seq: JsonElement

    @Serializable
    class Result(
        override val seq: JsonElement,
        val results: List<TestResult>,
    ) : RunResponse()

    @Serializable
    class Skipped(
        override val seq: JsonElement,
        val skipped: Boolean = true,
        val message: String,
    ) : RunResponse()

    @Serializable
    class ExecutionError(
        override val seq: JsonElement,
        val errored: Boolean = true,
        val context: ErrorContext,
    ) : RunResponse()
}

@Serializable
sealed class TestResult {

    @Serializable
    class Executed(
        val valid: Boolean,
    ) : TestResult()

    @Serializable
    class Skipped(
        val skipped: Boolean = true,
        val message: String? = null,
    ) : TestResult()

    @Serializable
    class ExecutionError(
        val errored: Boolean = true,
        val context: ErrorContext? = null,
    ) : TestResult()
}

@Serializable
class ErrorContext(
    val message: String? = null,
    val traceback: String? = null,
    val stderr: String? = null,
)
