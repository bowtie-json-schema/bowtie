// swift-tools-version: 6.0

import PackageDescription

let package = Package(
  name: "BowtieJSONSchema",
  platforms: [
    .macOS(.v14)
  ],
  products: [
    .executable(
      name: "BowtieJSONSchema",
      targets: ["BowtieJSONSchema"]
    )
  ],
  dependencies: [
    .package(url: "https://github.com/ajevans99/swift-json-schema.git", from: "0.7.0")
  ],
  targets: [
    .executableTarget(
      name: "BowtieJSONSchema",
      dependencies: [
        .product(name: "JSONSchema", package: "swift-json-schema")
      ]
    )
  ]
)
