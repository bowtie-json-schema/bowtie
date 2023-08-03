import kotlinx.serialization.DeserializationStrategy
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonContentPolymorphicSerializer
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive

@Serializable(with = CommandSerializer::class)
sealed class Command {
    @Serializable
    class Start(
        val version: Int,
    ) : Command()

    @Serializable
    class Dialect(
        val dialect: String,
    ) : Command()

    @Serializable
    class Run(
        val seq: JsonElement,
        val case: TestCase,
    ) : Command()

    @Serializable
    object Stop : Command()
}

@Serializable
class TestCase(
    val description: String,
    val comment: String? = null,
    /**
     * JSON schema to be used
     */
    val schema: JsonElement,
    val registry: Map<String, JsonElement> = emptyMap(),
    /**
     * List of tests
     */
    val tests: List<Test>,
)

@Serializable
class Test(
    val description: String,
    val comment: String? = null,
    /**
     * Instance to be validated against the schema
     */
    val instance: JsonElement,
    /**
     * Expected result of validation
     */
    val valid: Boolean? = null,
)

private class CommandSerializer : JsonContentPolymorphicSerializer<Command>(Command::class) {
    override fun selectDeserializer(element: JsonElement): DeserializationStrategy<Command> {
        require(element is JsonObject) { "command must be an object" }
        val cmd = requireNotNull(element["cmd"]) { "'cmd' is a required field" }
        require(cmd is JsonPrimitive && cmd.isString) { "'cmd' must be a string" }
        return when (val command = cmd.content) {
            "start" -> Command.Start.serializer()
            "dialect" -> Command.Dialect.serializer()
            "run" -> Command.Run.serializer()
            "stop" -> Command.Stop.serializer()
            else -> error("unsupported command '$command'")
        }
    }

}