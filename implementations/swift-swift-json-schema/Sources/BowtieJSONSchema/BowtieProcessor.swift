import Foundation
import JSONSchema

struct BowtieProcessor {
  enum Constants {
    static let supportedDialects: Set<String> = [
      JSONSchema.Dialect.draft2020_12.rawValue
    ]
  }

  private var didStart = false
  private var currentDialect: JSONSchema.Dialect?

  private let encoder: JSONEncoder
  private let decoder: JSONDecoder

  init(encoder: JSONEncoder, decoder: JSONDecoder) {
    self.encoder = encoder
    self.decoder = decoder
  }

  mutating func handle(command: Command) throws {
    switch command {
    case .start(let start):
      try handleStart(start)
    case .dialect(let dialect):
      try handleDialect(dialect)
    case .run(let run):
      try handleRun(run)
    case .stop:
      try handleStop()
    }
  }

  mutating func handleStart(_ start: Start) throws {
    log("STARTING")
    didStart = true
    let response = StartResponse(
      version: start.version,
      implementation: .init(dialects: Constants.supportedDialects)
    )
    try write(response)
  }

  mutating func handleDialect(_ dialect: Dialect) throws {
    assert(didStart)
    log("Dialect: \(dialect.dialect)")
    guard let dialect = JSONSchema.Dialect(rawValue: dialect.dialect) else {
      try write(DialectResponse(ok: false))
      return
    }
    currentDialect = dialect
    try write(DialectResponse(ok: true))
  }

  mutating func handleRun(_ run: Run) throws {
    assert(didStart)
    let identifier = run.seq
    log("Schema: \(run.testCase.schema)")

    let rawTestSchema = run.testCase.schema
    let schema: Schema
    do {
      schema = try Schema(
        rawSchema: rawTestSchema,
        context: .init(
          dialect: currentDialect ?? .draft2020_12,
          remoteSchema: run.testCase.registry ?? [:]
        )
      )
    } catch {
      log("Error: \(error)")
      try write(
        RunResponse.executionError(
          .init(
            seq: identifier,
            errored: true,
            context: .init(message: error.localizedDescription, traceback: nil)
          )
        )
      )
      return
    }

    let testResults = run.testCase.tests
      .map { test in
        let instance = test.instance
        let result = schema.validate(instance)
        return TestResult.executed(.init(valid: result.isValid))
      }

    let runResult = RunResponse.result(.init(seq: identifier, results: testResults))
    try write(runResult)
  }

  mutating func handleStop() throws {
    assert(didStart)
    log("STOPPING")
  }
}

extension BowtieProcessor {
  private func write<E: Encodable>(_ value: E) throws {
    let output = try encoder.encodeToString(value) + "\n"
    FileHandle.standardOutput.write(Data(output.utf8))
  }
}
