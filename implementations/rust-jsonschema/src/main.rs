use std::{collections::HashMap, io, process};

use backtrace::Backtrace;
use serde_json::{json, Result};

use jsonschema::{Draft, Retrieve, Uri};

struct InMemoryRetriever {
    registry: serde_json::Value,
}

impl Retrieve for InMemoryRetriever {
    fn retrieve(
        &self,
        uri: &Uri<String>,
    ) -> std::result::Result<serde_json::Value, Box<dyn std::error::Error + Send + Sync>> {
        Ok(self.registry[uri.as_str()].to_owned())
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
    let mut options = jsonschema::options().with_draft(Draft::Draft202012);

    for line in io::stdin().lines() {
        let request: serde_json::Value = serde_json::from_str(&line.expect("No input!"))?;
        match request["cmd"].as_str().expect("Bad command!") {
            "start" => {
                let osinfo = os_info::get();
                started = true;
                if request["version"] != 1 {
                    panic!("Not version 1!")
                };
                let response = json!({
                    "version": 1,
                    "implementation": {
                        "language": "rust",
                        "name": "jsonschema",
                        "version": env!("JSONSCHEMA_VERSION"),
                        "homepage": "https://docs.rs/jsonschema",
                        "documentation": "https://docs.rs/jsonschema",
                        "issues": "https://github.com/Stranger6667/jsonschema-rs/issues",
                        "source": "https://github.com/Stranger6667/jsonschema-rs",

                        "dialects": [
                            "https://json-schema.org/draft/2020-12/schema",
                            "https://json-schema.org/draft/2019-09/schema",
                            "http://json-schema.org/draft-07/schema#",
                            "http://json-schema.org/draft-06/schema#",
                            "http://json-schema.org/draft-04/schema#",
                        ],
                        "os": osinfo.os_type(),
                        "os_version": osinfo.version().to_string(),
                        "language_version": rustc_version_runtime::version().to_string(),
                    },
                });
                println!("{}", response);
            }
            "dialect" => {
                if !started {
                    panic!("Not started!")
                };
                let dialect = request["dialect"].as_str().expect("Bad dialect!");
                options = jsonschema::options()
                    .with_draft(*dialects.get(dialect).expect("No such draft!"));
                let response = json!({"ok": true});
                println!("{}", response);
            }
            "run" => {
                if !started {
                    panic!("Not started!")
                };
                let case = &request["case"];

                let registry = &case["registry"];
                let retriever = InMemoryRetriever {
                    registry: registry.to_owned(),
                };
                options = options.with_retriever(retriever);

                let response = match options.build(&case["schema"]) {
                    Ok(compiled) => {
                        let results: Vec<_> = case["tests"]
                            .as_array()
                            .expect("Invalid tests!")
                            .iter()
                            .map(|test| json!({"valid": compiled.is_valid(&test["instance"])}))
                            .collect();
                        json!({"seq": &request["seq"], "results": &results})
                    }
                    Err(error) => json!({
                        "errored": true,
                        "seq": &request["seq"],
                        "context": {
                            "message": format!("{:?}", error),
                            "traceback": format!("{:?}", Backtrace::new()),
                        },
                    }),
                };
                println!("{}", response);
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
