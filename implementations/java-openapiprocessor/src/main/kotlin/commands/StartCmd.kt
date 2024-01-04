package commands

import io.openapiprocessor.jsonschema.schema.SchemaVersion
import java.net.URI
import java.util.Properties

data class StartRequest(val version: Int) : Request

class StartCmd {

    fun run(request: StartRequest): Map<String, Any> {
        assert(request.version == 1)

        val properties = readProperties()
        return mapOf(
            "version" to 1,
            "implementation" to mapOf(
                "language" to "java",
                "language_version" to getRuntimeVersion(),
                "name" to "io.openapiprocessor.json-schema-validator",
                "version" to properties.getVersion(),
                "dialects" to SchemaVersion.entries.map { it.schemaUri },
                "homepage" to properties.getHomepage(),
                "issues" to properties.getIssues(),
                "source" to properties.getSource(),
            ),
        )
    }

    private fun getRuntimeVersion(): String {
        return Runtime.version().toString()
    }

    private fun readProperties(): Properties {
        val properties = Properties()
        properties.load(this::class.java.getResourceAsStream("/validator.properties"))
        return properties
    }
}

private fun Properties.getVersion(): String {
    return getProperty("validator.version")
}

private fun Properties.getHomepage(): URI {
    return URI(getProperty("validator.homepage"))
}

private fun Properties.getIssues(): URI {
    return URI(getProperty("validator.issues"))
}

private fun Properties.getSource(): URI {
    return URI(getProperty("validator.source"))
}
