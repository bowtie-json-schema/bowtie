import Foundation
import JSONSchema

setLineBufferedStdout()

func main() throws {
  log("Starting BowtieJSONSchema")

  let encoder = JSONEncoder()
  encoder.keyEncodingStrategy = .convertToSnakeCase
  let decoder = JSONDecoder()

  var bowtieProcess = BowtieProcessor(encoder: encoder, decoder: decoder)

  let input = FileHandle.standardInput
  let inputData = input.readDataToEndOfFile()
  guard let inputString = String(data: inputData, encoding: .utf8) else {
    throw NSError(domain: "BowtieJSONSchema", code: 1, userInfo: [NSLocalizedDescriptionKey: "Failed to read input"])
  }

  for line in inputString.components(separatedBy: .newlines) where !line.isEmpty {
    let command = try decoder.decode(Command.self, from: line.data(using: .utf8)!)
    try bowtieProcess.handle(command: command)
  }
}

do {
  try main()
} catch {
  log("An error occurred: \(error)")
  exit(1)
}
