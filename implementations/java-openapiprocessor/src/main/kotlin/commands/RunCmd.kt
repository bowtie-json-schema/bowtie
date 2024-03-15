package commands

import io.openapiprocessor.jackson.JacksonConverter
import io.openapiprocessor.jsonschema.reader.UriReader
import io.openapiprocessor.jsonschema.schema.DocumentLoader
import io.openapiprocessor.jsonschema.schema.JsonInstance
import io.openapiprocessor.jsonschema.schema.SchemaStore
import io.openapiprocessor.jsonschema.schema.SchemaVersion
import io.openapiprocessor.jsonschema.validator.Validator
import io.openapiprocessor.jsonschema.validator.ValidatorSettings
import stacktrace
import java.net.URI

class Case(
    val description: String,
    val comment: String?,
    val schema: Any,
    val registry: Map<URI, Any>?,
    val tests: List<Test>,
)

data class Test(
    val description: String,
    val comment: String? = null,
    val instance: Any?,
    val valid: Boolean?,
)

data class RunRequest(val seq: Any, val case: Case) : Request

class RunCmd(private val cfg: Configuration) : Request {

    @Suppress("TooGenericExceptionCaught")
    fun run(request: RunRequest): Map<String, Any> {
        return try {
            validate(request)
        } catch (ex: Exception) {
            mapOf(
                "seq" to request.seq,
                "errored" to true,
                "context" to mapOf(
                    "message" to ex.message,
                    "traceback" to stacktrace(ex),
                ),
            )
        }
    }

    private fun validate(request: RunRequest): Map<String, Any> {
        val reader = UriReader()
        val converter = JacksonConverter()
        val loader = DocumentLoader(reader, converter)

        val store = SchemaStore(loader)
        when (cfg.version) {
            SchemaVersion.Draft202012 -> store.registerDraft202012()
            SchemaVersion.Draft201909 -> store.registerDraft201909()
            SchemaVersion.Draft7 -> store.registerDraft7()
            SchemaVersion.Draft6 -> store.registerDraft6()
            SchemaVersion.Draft4 -> store.registerDraft4()
        }

        request.case.registry?.forEach {
            store.register(it.key, it.value)
        }

        val schemaUri = store.register(request.case.schema)
        val schema = store.getSchema(schemaUri, cfg.version)

        val settings = ValidatorSettings()
        settings.version = cfg.version

        val validator = Validator(settings)

        val results = mutableListOf<Any>()
        request.case.tests.forEach {
            val instance = JsonInstance(it.instance)
            val step = validator.validate(schema, instance)

            results.add(
                mutableMapOf<String, Any>(
                    "valid" to step.isValid,
                ),
            )
        }

        return mapOf(
            "seq" to request.seq,
            "results" to results,
        )
    }
}
