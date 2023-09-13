package commands

import io.openapiprocessor.jsonschema.schema.SchemaVersion

class Configuration {
    var version: SchemaVersion = SchemaVersion.getLatest()
}
