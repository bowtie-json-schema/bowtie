import java.io.BufferedReader
import java.io.BufferedWriter
import java.io.InputStreamReader
import java.io.PrintWriter
import java.io.StringWriter

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
