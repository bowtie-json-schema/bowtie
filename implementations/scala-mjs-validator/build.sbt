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

unmanagedBase := baseDirectory.value / "lib"

assembly / assemblyJarName := "validator.jar"

assembly / assemblyMergeStrategy := {
  case PathList("META-INF", xs @ _*) => MergeStrategy.discard
  case x                             => MergeStrategy.first
}

val setValidatorVersion = taskKey[Seq[PackageOption]]("Set validator version")

setValidatorVersion := {
  import java.util.jar.JarFile
  import scala.util.Try

  val validatorJarPath = (baseDirectory.value / "lib" / "mjs.jar").toString

  val validatorVersion = Try {
    val jar = new JarFile(validatorJarPath)
    val manifest = jar.getManifest
    manifest.getMainAttributes.getValue("Implementation-Version")
  }.getOrElse("unknown")

  Seq(
    Package.ManifestAttributes(
      "Main-Class" -> "Harness",
      "Implementation-Group" -> "org.up.mjs",
      "Implementation-Name" -> "mjs",
      "Implementation-Version" -> s"Harness 1.0 | Validator $validatorVersion"
    )
  )
}

Compile / packageBin / packageOptions := setValidatorVersion.value

scalacOptions += "-Ymacro-annotations"
