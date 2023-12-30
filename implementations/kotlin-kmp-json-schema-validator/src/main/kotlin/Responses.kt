import kotlinx.serialization.DeserializationStrategy
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonContentPolymorphicSerializer
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject

@Serializable
class StartResponse(
    val ready: Boolean,
    val version: Int,
    val implementation: Implementation,
)

@Suppress("LongParameterList")
@Serializable
class Implementation(
    val language: String = "kotlin",
    val name: String = "kmp-json-schema-validator",
    val version: String,
    val dialects: Set<String>,
    val homepage: String,
    val issues: String,
    val source: String,
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

@Serializable(with = TestResultSerializer::class)
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

private class TestResultSerializer : JsonContentPolymorphicSerializer<TestResult>(TestResult::class) {
    override fun selectDeserializer(element: JsonElement): DeserializationStrategy<TestResult> {
        require(element is JsonObject) { "command must be an object" }
        return when {
            "valid" in element -> TestResult.Executed.serializer()
            "skipped" in element -> TestResult.Skipped.serializer()
            "errored" in element -> TestResult.ExecutionError.serializer()
            else -> error("unknown object type")
        }
    }
}
