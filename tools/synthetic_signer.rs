#![forbid(unsafe_code)]
//! Known fixture key only. This program cannot accept a production key.
use anyhow::{Context as _, Result, ensure};
use ed25519_dalek::{Signer as _, SigningKey};
use std::path::PathBuf;

struct FixtureSigner(SigningKey);
impl irmind_app::Signer for FixtureSigner {
    fn actor(&self) -> irmind_domain::Actor {
        irmind_domain::Actor::Analyst
    }
    fn public_key(&self) -> Vec<u8> {
        self.0.verifying_key().to_bytes().to_vec()
    }
    fn sign(&self, bytes: &[u8]) -> Result<Vec<u8>, irmind_app::AppError> {
        Ok(self.0.sign(bytes).to_bytes().to_vec())
    }
}

fn main() -> Result<()> {
    let signing = SigningKey::from_bytes(&[90; 32]);
    let public = signing.verifying_key();
    let key_id = irmind_app::hex(&irmind_app::sha256(public.as_bytes()));
    let args = std::env::args_os().skip(1).collect::<Vec<_>>();
    if args.is_empty() {
        println!(
            "{}",
            serde_json::json!({"synthetic":true,"public_key":irmind_app::hex(public.as_bytes()),"key_id":key_id})
        );
        return Ok(());
    }
    ensure!(
        args.len() == 2,
        "usage: catalog_sign INDEX OUTPUT_SIGNATURE"
    );
    let path = PathBuf::from(&args[0]);
    let bytes = std::fs::read(path)?;
    ensure!(bytes.len() <= 1024 * 1024, "index exceeds limit");
    let index: serde_json::Value = serde_json::from_slice(&bytes)?;
    ensure!(
        index["key_id"].as_str().context("key ID required")? == key_id,
        "not a synthetic index"
    );
    let mut preimage = b"irmind-skill-catalog-index-v1\0".to_vec();
    preimage.extend_from_slice(&u64::try_from(bytes.len())?.to_be_bytes());
    preimage.extend_from_slice(&bytes);
    let signature = signing.sign(&preimage);
    public.verify_strict(&preimage, &signature)?;
    // This fixed fixture key exists only in this development process, never in
    // the release's production catalog verifier or compiled trust roots.
    let keys = Box::leak(Box::new([public.to_bytes()]));
    let raw = irmind_app::catalog::CatalogIndexBytes::new(bytes, &signature.to_bytes())?;
    let expected = irmind_app::catalog::FrozenCatalogRelease::new(
        index["release_tag"].as_str().context("tag required")?,
    )?;
    let signature_checker =
        irmind_infra::LocalVerifier::from_signer(&FixtureSigner(signing.clone()));
    let verified = irmind_app::catalog::VerifiedCatalogIndex::authenticate(
        &raw,
        &expected,
        keys,
        &signature_checker,
    )?;
    let directory = PathBuf::from(&args[0])
        .parent()
        .context("index directory required")?
        .to_path_buf();
    for entry in verified.index().entries() {
        let transport = irmind_app::catalog::BoundedPackageBytes::new(std::fs::read(
            directory.join(entry.asset()),
        )?)?;
        verified.asset(entry.name())?.compile(
            &transport,
            env!("CARGO_PKG_VERSION"),
            &irmind_infra::TomlSkillCompiler,
        )?;
    }
    std::fs::write(PathBuf::from(&args[1]), signature.to_bytes())?;
    if let Some(last) = preimage.last_mut() {
        *last ^= 1;
    }
    ensure!(
        public.verify_strict(&preimage, &signature).is_err(),
        "tamper test failed"
    );
    println!("Synthetic index signature verified; a changed byte is rejected.");
    Ok(())
}
