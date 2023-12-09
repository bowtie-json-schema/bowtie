name := "mjs-validator"

ThisBuild / version := "1.0"
ThisBuild / scalaVersion := "2.13.10"

javacOptions ++= Seq("-source", "17", "-target", "17")

resolvers += Resolver.mavenCentral

libraryDependencies ++= Seq(
  "org.scala-lang" % "scala-library" % "2.13.10"
)

val circeVersion = "0.14.1"
libraryDependencies ++= Seq(
  "io.circe" %% "circe-core",
  "io.circe" %% "circe-generic",
  "io.circe" %% "circe-generic-extras",
  "io.circe" %% "circe-parser"
).map(_ % circeVersion)

val mjsVersion = "v0.1.0"
lazy val mjs = RootProject(
  uri(s"https://gitlab.lip6.fr/jsonschema/modernjsonschemavalidator.git#$mjsVersion")
)
lazy val bowtieMjs = (project in file(".")).dependsOn(mjs)
assembly / assemblyJarName := "bowtieMjs.jar"
assembly / packageOptions := Seq(
  Package.ManifestAttributes(
    "Main-Class" -> "Harness",
    "Implementation-Group" -> "org.up.mjs",
    "Implementation-Name" -> "mjs",
    "Implementation-Version" -> mjsVersion
  )
)

scalacOptions += "-Ymacro-annotations"
