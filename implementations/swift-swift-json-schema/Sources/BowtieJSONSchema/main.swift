import Foundation
import JSONSchema

setLineBufferedOutput()

func main() throws {
  log("Starting BowtieJSONSchema")

  let encoder = JSONEncoder()
  encoder.keyEncodingStrategy = .convertToSnakeCase
  let decoder = JSONDecoder()

  var bowtieProcess = BowtieProcessor(encoder: encoder, decoder: decoder)

  while let line = readLine(strippingNewline: true) {
    guard !line.isEmpty else { continue }
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
