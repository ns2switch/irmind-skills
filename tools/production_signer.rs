#![forbid(unsafe_code)]
//! Production signer: the protected release job supplies the seed only in memory.
use anyhow::{Context as _, Result, ensure};
use ed25519_dalek::{Signer as _, SigningKey};
use std::path::PathBuf;
use secrecy::{ExposeSecret as _, SecretString};

struct CatalogSigner(SigningKey);
impl irmind_app::Signer for CatalogSigner {
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

fn sign_index() -> Result<()> {
    let encoded = SecretString::from(std::env::var("CATALOG_ED25519_SEED_HEX").map_err(|_| anyhow::anyhow!("signing secret unavailable"))?);
    let text = encoded.expose_secret();
    ensure!(text.len() == 64 && text.bytes().all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b)), "invalid signing secret");
    let mut seed = [0_u8; 32];
    for (slot, pair) in seed.iter_mut().zip(text.as_bytes().chunks_exact(2)) {
        fn nibble(byte: u8) -> u8 { if byte <= b'9' { byte - b'0' } else { byte - b'a' + 10 } }
        *slot = (nibble(pair[0]) << 4) | nibble(pair[1]);
    }
    let signing = SigningKey::from_bytes(&seed);
    seed.fill(0);
    drop(encoded);
    let public = signing.verifying_key();
    let key_id = irmind_app::hex(&irmind_app::sha256(public.as_bytes()));
    let args = std::env::args_os().skip(1).collect::<Vec<_>>();
    ensure!(irmind_app::hex(public.as_bytes()) == "fb2015c83d13fe018e270a7fe73bf7bccfdb622565e30f7ade436637c3b2c25b" && key_id == "f04daae3f8243ed76452d5f787ea527c8fbec895ca0c91a35f453f6677575e4f", "unexpected signing key");
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
        "unexpected index key ID"
    );
    let mut preimage = b"irmind-skill-catalog-index-v1\0".to_vec();
    preimage.extend_from_slice(&u64::try_from(bytes.len())?.to_be_bytes());
    preimage.extend_from_slice(&bytes);
    let signature = signing.sign(&preimage);
    public.verify_strict(&preimage, &signature)?;
    // The verifier receives only the checked public key, never private material.
    let keys = Box::leak(Box::new([public.to_bytes()]));
    let raw = irmind_app::catalog::CatalogIndexBytes::new(bytes, &signature.to_bytes())?;
    let expected = irmind_app::catalog::FrozenCatalogRelease::new(
        index["release_tag"].as_str().context("tag required")?,
    )?;
    let signature_checker =
        irmind_infra::LocalVerifier::from_signer(&CatalogSigner(signing));
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
    println!("Catalog index signature and package hashes verified.");
    Ok(())
}

fn main() {
    // Never format an error chain or environment value in the protected job.
    if sign_index().is_err() {
        eprintln!("Catalog signing failed; no release should be published.");
        std::process::exit(1);
    }
}
