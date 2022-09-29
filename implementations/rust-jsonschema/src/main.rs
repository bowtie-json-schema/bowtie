use std::{collections::HashMap, io, process, sync::Arc};

use jsonschema::{Draft, JSONSchema, SchemaResolver, SchemaResolverError};
use serde_json::{json, Result};
use url::Url;

struct InMemoryResolver {
    registry: serde_json::Value,
}

impl SchemaResolver for InMemoryResolver {
    fn resolve(
        &self,
        _root_schema: &serde_json::Value,
        url: &Url,
        _original_reference: &str,
    ) -> core::result::Result<Arc<serde_json::Value>, SchemaResolverError> {
        return Ok(Arc::new(self.registry[url.to_string()].to_owned()));
    }
}

fn main() -> Result<()> {
    let dialects = HashMap::from([
        (
            String::from("https://json-schema.org/draft/2020-12/schema"),
            Draft::Draft202012,
        ),
        (
            String::from("https://json-schema.org/draft/2019-09/schema"),
            Draft::Draft201909,
        ),
        (
            String::from("http://json-schema.org/draft-07/schema#"),
            Draft::Draft7,
        ),
        (
            String::from("http://json-schema.org/draft-06/schema#"),
            Draft::Draft6,
        ),
        (
            String::from("http://json-schema.org/draft-04/schema#"),
            Draft::Draft4,
        ),
    ]);

    let mut started = false;
    let mut options = JSONSchema::options();
    let mut compiler = options.with_draft(Draft::Draft202012);

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
                        "homepage": "https://docs.rs/jsonschema/latest/jsonschema/",
                        "issues": "https://github.com/Stranger6667/jsonschema-rs/issues",

                        "dialects": [
                            "https://json-schema.org/draft/2020-12/schema",
                            "https://json-schema.org/draft/2019-09/schema",
                            "http://json-schema.org/draft-07/schema#",
                            "http://json-schema.org/draft-06/schema#",
                            "http://json-schema.org/draft-04/schema#",
                        ],
                    },
                });
                println!("{}", response.to_string());
            }
            "dialect" => {
                if !started {
                    panic!("Not started!")
                };
                let dialect = request["dialect"].as_str().expect("Bad dialect!");
                options = JSONSchema::options();
                compiler = options.with_draft(*dialects.get(dialect).expect("No such draft!"));
                let response = json!({"ok": true});
                println!("{}", response.to_string());
            }
            "run" => {
                if !started {
                    panic!("Not started!")
                };
                let case = &request["case"];

                let registry = &case["registry"];
                let resolver = InMemoryResolver {
                    registry: registry.to_owned(),
                };
                compiler = compiler.with_resolver(resolver);

                let compiled = compiler.compile(&case["schema"]).expect("Invalid schema!");
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
