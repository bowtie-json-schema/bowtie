plugins {
    alias(libs.plugins.kotlin)
    application
}

group = "com.github.bowtie-json-schema"

repositories {
    mavenCentral()
    maven {
        url = uri("https://oss.sonatype.org/content/repositories/snapshots")
    }
}

kotlin {
    jvmToolchain(libs.versions.build.jdk.get().toInt())
}

application {
    mainClass.set("MainKt")
}

distributions {
    main {
        distributionBaseName.set("bowtie")
    }
}

dependencies {
    implementation(platform(libs.jsv.bom))
    implementation(libs.jsv.validator)
    implementation(libs.io.interfaces)
    implementation(libs.io.jackson)
    implementation(platform(libs.jackson.bom))
    implementation(libs.jackson.databind)
    implementation(libs.jackson.kotlin)
    runtimeOnly(libs.logback)
}

tasks {
    val validatorProperties by registering(WriteProperties::class) {
        description = "Write project properties in a file."
        comment = "properties for start command"

        destinationFile.set(file("$buildDir/validator.properties"))
        encoding = "UTF-8"

        properties(
            mapOf(
                "validator.version" to libs.versions.validator.get(),
                "validator.homepage" to "https://github.com/openapi-processor/openapi-parser",
                "validator.issues" to "https://github.com/openapi-processor/openapi-parser/issues",
                "java.build.version" to libs.versions.build.jdk.get()
            )
        )
    }

    processResources {
        from(validatorProperties)
    }
}
