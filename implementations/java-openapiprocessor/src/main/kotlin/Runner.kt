import com.fasterxml.jackson.databind.json.JsonMapper
import com.fasterxml.jackson.module.kotlin.jsonMapper
import com.fasterxml.jackson.module.kotlin.kotlinModule
import com.fasterxml.jackson.module.kotlin.readValue
import commands.Configuration
import commands.Dialect
import commands.DialectRequest
import commands.Request
import commands.Run
import commands.RunRequest
import commands.Start
import commands.StartRequest
import commands.Stop
import commands.StopRequest
import java.io.BufferedReader
import java.io.BufferedWriter
import java.util.stream.Stream

class Runner(
    private val input: BufferedReader,
    private val output: BufferedWriter,
    private val error: BufferedWriter
) {
    private val mapper = createMapper()
    private val config = Configuration()

    fun run() {
        commands().forEach {
            try {
                val request = readRequest(it)
                handleRequest(request)
            } catch (ex: Exception) {
                writeError(ex)
            }
        }
    }

    private fun handleRequest(request: Request) {
        when (request) {
            is StartRequest -> {
                writeResponse(Start().run(request))
            }
            is DialectRequest -> {
                writeResponse(Dialect(config).run(request))
            }
            is RunRequest -> {
                writeResponse(Run(config).run(request))
            }
            is StopRequest -> {
                writeResponse(Stop(config).run())
            }
            else -> {
                writeError("unknown request!")
            }
        }
    }

    private fun commands(): Stream<String> {
        return input.lines()
    }

    private fun readRequest(input: String): Request {
        return mapper.readValue<Request>(input)
    }

    private fun writeResponse(response: Map<String, Any>) {
        writeOutput(toJson(response))
    }

    private fun writeOutput(message: String) {
        output.write(message)
        output.newLine()
        flush()
    }

    private fun writeError(exception: Exception) {
        error.write(exception.message!!)
        error.newLine()
        flush()
    }

    private fun writeError(message: String) {
        error.write(message)
        error.newLine()
        flush()
    }

    private fun flush() {
        output.flush()
        error.flush()
    }

    private fun toJson(response: Map<String, Any>): String {
        return mapper.writeValueAsString(response)
    }

    private fun createMapper(): JsonMapper {
        return jsonMapper {
            addModule(kotlinModule())
        }
    }
}
