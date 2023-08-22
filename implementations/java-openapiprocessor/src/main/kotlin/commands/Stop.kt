package commands

class StopRequest: Request

class Stop(private val cfg: Configuration) {

    fun run(): Map<String, Any> {
        return emptyMap()
    }
}
