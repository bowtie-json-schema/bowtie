name := "scala-json-schema"

ThisBuild / version := "1.0"
ThisBuild / scalaVersion := "3.3.3"

javacOptions ++= Seq("-source", "17", "-target", "17")

resolvers += Resolver.mavenCentral

val circeVersion = "0.14.6"
libraryDependencies ++= Seq(
  "io.circe" %% "circe-core",
  "io.circe" %% "circe-generic",
  "io.circe" %% "circe-parser"
).map(_ % circeVersion)

val jsonSchemaVersion = "0.2.0"
libraryDependencies += "io.github.jam01" %% "json-schema" % jsonSchemaVersion

// Not a transitive dependency of json-schema (see its README) - pinned to the exact
// upickle-core version that json-schema_3:0.2.0's POM depends on.
libraryDependencies += "com.lihaoyi" %% "ujson" % "3.3.1"

assembly / assemblyJarName := "bowtieJsonSchema.jar"
assembly / packageOptions := Seq(
  Package.ManifestAttributes(
    "Main-Class" -> "Harness",
    "Implementation-Group" -> "io.github.jam01",
    "Implementation-Name" -> "json-schema",
    "Implementation-Version" -> jsonSchemaVersion,
  )
)
