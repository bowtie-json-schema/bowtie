import Foundation

func setLineBufferedOutput() {
  FileHandle.standardOutput.synchronizeFile()
  FileHandle.standardError.synchronizeFile()
}

/// Writes to standard error for logging in Bowtie.
func log(_ message: String) {
  FileHandle.standardError.write(Data("\(message)\n".utf8))
}

// MARK: JSON
extension JSONEncoder {
  func encodeToString<E: Encodable>(_ encodable: E) throws -> String {
    let data = try encode(encodable)
    return String(data: data, encoding: .utf8)!
  }
}
