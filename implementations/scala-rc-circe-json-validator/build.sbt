name := "bowtie-rc-circe-json-validator"


ThisBuild / version := "1.0"
ThisBuild / scalaVersion := "3.3.1"

javacOptions ++= Seq("-source", "17", "-target", "17")

resolvers += Resolver.mavenCentral

val circeVersion = "0.14.6"
libraryDependencies ++= Seq(
  "io.circe" %% "circe-core",
  "io.circe" %% "circe-generic",
  "io.circe" %% "circe-parser"
).map(_ % circeVersion)

val rcCirceJsonVersion = "0.4.1"
libraryDependencies += "net.reactivecore" % "circe-json-schema_3" % rcCirceJsonVersion

assembly / assemblyJarName := "bowtieRcCirce.jar"
assembly / packageOptions := Seq(
  Package.ManifestAttributes(
    "Main-Class" -> "BowtieRcCirceJsonValidator",
    "Implementation-Group" -> "reactive-core",
    "Implementation-Name" -> "rc-circe-json-validator",
    "Implementation-Version" -> rcCirceJsonVersion,
  )
)
