use std::{error::Error, io, process};

use boon::{Compiler, Draft, Schemas, UrlLoader};
use serde_json::{json, Map, Value};

fn main() -> Result<(), Box<dyn Error>> {
    let mut started = false;
    let mut draft = None;
    for line in io::stdin().lines() {
        let request: Value = serde_json::from_str(&line?)?;
        let cmd = request["cmd"].as_str().ok_or("no command")?;
        match cmd {
            "start" => {
                let osinfo = os_info::get();
                started = true;
                if request["version"] != 1 {
                    Err("not version 1")?;
                }
                let response = json!({
                    "version": 1,
                    "implementation": {
                        "language": "rust",
                        "name": "boon",
                        "version": env!("BOON_VERSION"),
                        "documentation": "https://docs.rs/boon",
                        "homepage": "https://github.com/santhosh-tekuri/boon",
                        "issues": "https://github.com/santhosh-tekuri/boon/issues",
                        "source": "https://github.com/santhosh-tekuri/boon",
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
                    }
                });
                println!("{response}");
            }
            "dialect" => {
                let dialect = request["dialect"].as_str().ok_or("no dialect")?;
                draft = Draft::from_url(dialect);
                let response = json!({"ok": true});
                println!("{response}");
            }
            "run" => {
                if !started {
                    Err("not started")?;
                }
                let seq = &request["seq"];
                let case = &request["case"];
                let mut schemas = Schemas::default();
                let mut compiler = Compiler::default();
                if let Some(draft) = draft {
                    compiler.set_default_draft(draft);
                }
                if let Value::Object(obj) = &case["registry"] {
                    compiler.use_loader(Box::new(MapUrlLoader(obj.clone())));
                }
                let fake_url = "http://fake.com/schema.json";
                if let Err(e) = compiler.add_resource(fake_url, case["schema"].clone()) {
                    print_error(seq, e);
                    continue;
                }
                let schema = match compiler.compile(fake_url, &mut schemas) {
                    Ok(sch) => sch,
                    Err(e) => {
                        print_error(seq, e);
                        continue;
                    }
                };
                let tests = case["tests"].as_array().ok_or("invalid tests")?;
                let results = tests
                    .iter()
                    .map(|test| {
                        let valid = schemas.validate(&test["instance"], schema).is_ok();
                        json!({ "valid": valid })
                    })
                    .collect::<Vec<_>>();
                let response = json!({"seq": seq, "results": results});
                println!("{response}");
            }
            "stop" => {
                if !started {
                    Err("not started")?;
                }
                process::exit(0);
            }
            _ => Err(format!("unknown command: {cmd}"))?,
        }
    }
    Ok(())
}

struct MapUrlLoader(Map<String, Value>);

impl UrlLoader for MapUrlLoader {
    fn load(&self, url: &str) -> Result<Value, Box<dyn Error>> {
        let value = self.0.get(url);
        if let Some(v) = value {
            return Ok(v.clone());
        }
        Err(format!("Can't load {url}"))?
    }
}

fn print_error(seq: &Value, err: impl Error) {
    let response = json!({
        "seq": seq,
        "errored": true,
        "context": {
            "message": format!("{err:#}"),
        }
    });
    println!("{response}");
}
