import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
    kotlin("jvm") version "1.8.22"
    kotlin("plugin.serialization") version "1.8.22"
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

val implementationName: String = "io.github.optimumcode:json-schema-validator"
val implementationVersion: String = "0.0.2"

dependencies {
    implementation("$implementationName:$implementationVersion")
}

tasks.withType<Jar> {
    manifest {
        attributes(buildMap {
            put("Implementation-Name", implementationName)
            put("Implementation-Version", implementationVersion)
            put("Implementation-Homepage", "https://github.com/OptimumCode/json-schema-validator")
            put("Implementation-Issues", "https://github.com/OptimumCode/json-schema-validator/issues")
        })
    }
}

application {
    mainClass.set("BowtieSampsonSchemaValidatorLauncherKt")
}
