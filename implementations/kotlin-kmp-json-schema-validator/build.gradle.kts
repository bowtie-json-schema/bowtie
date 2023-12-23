plugins {
    alias(libs.plugins.kotlin.jvm)
    alias(libs.plugins.kotlin.serialization)
    application
}

repositories {
    mavenCentral()
}

dependencies {
    implementation(libs.json.schema.validator)
}

tasks.withType<Jar> {
    val lib = libs.json.schema.validator.get()
    manifest {
        attributes(
            buildMap {
                put("Implementation-Version", lib.version)
                put("Implementation-Homepage", "https://github.com/OptimumCode/json-schema-validator")
                put("Implementation-Issues", "https://github.com/OptimumCode/json-schema-validator/issues")
                put("Implementation-Source", "https://github.com/OptimumCode/json-schema-validator")
            },
        )
    }
}

application {
    mainClass.set("BowtieSampsonSchemaValidatorLauncherKt")
}
