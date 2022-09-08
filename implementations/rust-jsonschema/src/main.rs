use std::{io, process};

use jsonschema::JSONSchema;
use serde_json::{json, Result};

fn main() -> Result<()> {
    let mut started = false;

    for line in io::stdin().lines() {
        let request: serde_json::Value = serde_json::from_str(&line.expect("No input!"))?;
        match request["cmd"].as_str().expect("Bad command!") {
            "start" => {
                started = true;
                if request["version"] != 1 {
                    panic!("Not version 1!")
                };
                let response = json!({
                    "ready": true,
                    "version": 1,
                    "implementation": {
                        "language": "rust",
                        "name": "jsonschema",
                    }
                });
                println!("{}", response.to_string());
            }
            "run" => {
                if !started {
                    panic!("Not started!")
                };
                let case = &request["case"];
                let compiled = JSONSchema::compile(&case["schema"]).expect("Invalid schema!");
                let results: Vec<_> = case["tests"]
                    .as_array()
                    .expect("Invalid tests!")
                    .iter()
                    .map(|test| json!({"valid": compiled.is_valid(&test["instance"])}))
                    .collect();
                let response = json!({"seq": &request["seq"], "results": &results});
                println!("{}", response.to_string());
            }
            "stop" => {
                if !started {
                    panic!("Not started!")
                };
                process::exit(0);
            }
            _ => panic!("Unknown command"),
        }
    }
    Ok(())
}
