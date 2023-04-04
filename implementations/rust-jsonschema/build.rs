use cargo_lock::Lockfile;

/// sets jsonschema library version from Cargo.lock as environment variable
fn main() {
    let lockfile = Lockfile::load("Cargo.lock").unwrap();
    let jsonschema = lockfile
        .packages
        .iter()
        .find(|p| p.name.as_str() == "jsonschema");
    if let Some(jsonschema) = jsonschema {
        println!("cargo:rustc-env=JSONSCHEMA_VERSION={}", jsonschema.version);
    }
}
