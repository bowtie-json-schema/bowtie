import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
    alias(libs.plugins.kotlin.jvm)
    alias(libs.plugins.kotlin.serialization)
    application
}

tasks.withType<KotlinCompile> {
    kotlinOptions {
        jvmTarget = "11"
    }
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
                put("Implementation-Name", "${lib.group}:${lib.module}")
                put("Implementation-Version", lib.version)
                put("Implementation-Homepage", "https://github.com/OptimumCode/json-schema-validator")
                put("Implementation-Issues", "https://github.com/OptimumCode/json-schema-validator/issues")
            },
        )
    }
}

application {
    mainClass.set("BowtieSampsonSchemaValidatorLauncherKt")
}
