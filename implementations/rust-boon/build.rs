use cargo_lock::Lockfile;

/// sets boon library version from Cargo.lock as environment variable
fn main() {
    let lockfile = Lockfile::load("Cargo.lock").unwrap();
    let boon = lockfile.packages.iter().find(|p| p.name.as_str() == "boon");
    if let Some(boon) = boon {
        println!("cargo:rustc-env=BOON_VERSION={}", boon.version);
    }
}
