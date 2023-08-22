import java.io.*

fun stdin(): BufferedReader {
    return BufferedReader(InputStreamReader(System.`in`))
}

fun stdout(): BufferedWriter {
    return System.out.bufferedWriter()
}

fun stderr(): BufferedWriter {
    return System.err.bufferedWriter()
}

fun stacktrace(ex: Exception): String {
    val st = StringWriter()
    ex.printStackTrace(PrintWriter(st))
    return st.toString()
}
