package commands

import io.openapiprocessor.jsonschema.schema.SchemaVersion
import java.net.URI

data class DialectRequest(val dialect: URI) : Request

class Dialect(private val cfg: Configuration) : Request {

    fun run(request: DialectRequest): Map<String, Any> {
        cfg.version = SchemaVersion.getVersion(request.dialect)!!

        return mapOf("ok" to true)
    }
}
