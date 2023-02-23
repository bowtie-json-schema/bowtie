use std::{collections::HashMap, error::Error, io, process};

use boon::{Compiler, Draft, Schemas, UrlLoader};
use serde_json::{json, Map, Value};
use url::Url;

fn main() -> Result<(), Box<dyn Error>> {
    let drafts = {
        let mut m = HashMap::new();
        m.insert(
            "https://json-schema.org/draft/2020-12/schema",
            Draft::V2020_12,
        );
        m.insert(
            "https://json-schema.org/draft/2019-09/schema",
            Draft::V2019_09,
        );
        m.insert("http://json-schema.org/draft-07/schema#", Draft::V7);
        m.insert("http://json-schema.org/draft-06/schema#", Draft::V6);
        m.insert("http://json-schema.org/draft-04/schema#", Draft::V4);
        m
    };

    let mut started = false;
    let mut draft = None;
    for line in io::stdin().lines() {
        let request: Value = serde_json::from_str(&line?)?;
        let cmd = request["cmd"].as_str().ok_or("no command")?;
        match cmd {
            "start" => {
                started = true;
                if request["version"] != 1 {
                    Err("not version 1")?;
                }
                let response = json!({
                    "ready": true,
                    "version": 1,
                    "implementation": {
                        "language": "rust",
                        "name": "boon",
                        "homepage": "https://docs.rs/boon/latest/boon/",
                        "issues": "htps://github.com/santhosh-tekuri/boon/issues",
                        "dialects": [
                            "https://json-schema.org/draft/2020-12/schema",
                            "https://json-schema.org/draft/2019-09/schema",
                            "http://json-schema.org/draft-07/schema#",
                            "http://json-schema.org/draft-06/schema#",
                            "http://json-schema.org/draft-04/schema#",
                        ],
                    }
                });
                println!("{response}");
            }
            "dialect" => {
                let dialect = request["dialect"].as_str().ok_or("no dialect")?;
                draft = Some(
                    drafts
                        .get(dialect)
                        .ok_or(format!("no such dialect {dialect}"))?,
                );
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
                    compiler.set_default_draft(*draft);
                }
                if let Value::Object(obj) = &case["registry"] {
                    compiler.register_url_loader("http", Box::new(MapUrlLoader(obj.clone())));
                    compiler.register_url_loader("https", Box::new(MapUrlLoader(obj.clone())));
                }
                let fake_url = "http://fake.com/schema.json";
                if let Err(e) = compiler.add_resource(fake_url, case["schema"].clone()) {
                    print_error(seq, e);
                    continue;
                }
                let schema = match compiler.compile(&mut schemas, fake_url.to_owned()) {
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
    fn load(&self, url: &Url) -> Result<Value, Box<dyn Error>> {
        let value = self.0.get(url.as_str());
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
