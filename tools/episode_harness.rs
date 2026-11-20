#![forbid(unsafe_code)]
#![allow(clippy::unwrap_used, clippy::too_many_lines)]
//! Development adapter: compile this against the immutable published `IRMind` source.
#[path = "../tests/support/current_sources.rs"]
mod current_sources;

use anyhow::{Context as _, Result, anyhow, ensure};
use ed25519_dalek::{Signer as _, SigningKey};
use irmind_app::{
    AppError, AuditLog as _, CancellationToken, CompletionRequest, CryptoPorts, Engine,
    EnginePorts, ExportVerifier as _, FindingKind, LargeCaseUseCases, LlmPort, MessageRole,
    ModelEvent, ModelResponse, ModelStream, ModelToolCall, Signer, SkillOrigin, SkillServices,
};
use irmind_domain::{Actor, AgentId, AuditEventKind, ExecutionMode, ProposedCall, Tool};
use irmind_infra::{
    FileSkillPackageStore, LocalExportVerifier, LocalVerifier, SystemClock, TomlSkillCompiler,
};
use serde_json::Value;
use std::{
    collections::{BTreeMap, BTreeSet},
    path::{Path, PathBuf},
    sync::{Arc, Mutex},
};

struct SyntheticSigner(Actor, SigningKey);
impl Signer for SyntheticSigner {
    fn actor(&self) -> Actor {
        self.0.clone()
    }
    fn public_key(&self) -> Vec<u8> {
        self.1.verifying_key().to_bytes().to_vec()
    }
    fn sign(&self, bytes: &[u8]) -> std::result::Result<Vec<u8>, AppError> {
        Ok(self.1.sign(bytes).to_bytes().to_vec())
    }
}

struct Scripted {
    steps: Vec<Value>,
    hashes: Vec<String>,
    requests: Mutex<Vec<CompletionRequest>>,
}
impl Scripted {
    fn substitute(&self, text: &str) -> String {
        self.hashes
            .iter()
            .enumerate()
            .fold(text.to_owned(), |text, (index, hash)| {
                text.replace(&format!("$source:{index}"), hash)
            })
    }
}
#[irmind_app::async_trait]
impl LlmPort for Scripted {
    fn output_profile(&self) -> irmind_app::ModelOutputProfile {
        irmind_app::ModelOutputProfile::known(2048, false).unwrap()
    }
    async fn complete(
        &self,
        request: CompletionRequest,
        _: &CancellationToken,
    ) -> std::result::Result<ModelStream, AppError> {
        request.validate()?;
        let mut requests = self.requests.lock().unwrap();
        let index = requests.len();
        let step = self
            .steps
            .get(index)
            .ok_or_else(|| AppError::Model("script exhausted".into()))?;
        let calls = step["calls"]
            .as_array()
            .unwrap()
            .iter()
            .enumerate()
            .map(|(offset, call)| {
                let tool = Tool::parse(call["tool"].as_str().unwrap())
                    .map_err(|_| AppError::Model("unknown scripted tool".into()))?;
                let args = call["args"]
                    .as_object()
                    .unwrap()
                    .iter()
                    .map(|(key, value)| (key.clone(), self.substitute(value.as_str().unwrap())))
                    .collect::<BTreeMap<_, _>>();
                ModelToolCall::from_proposal(
                    &format!("catalog_{index}_{offset}"),
                    ProposedCall { tool, args },
                )
            })
            .collect::<std::result::Result<Vec<_>, AppError>>()?;
        let text = self.substitute(step["text"].as_str().unwrap());
        requests.push(request);
        Ok(Box::pin(futures_util::stream::iter([Ok(
            ModelEvent::Completed {
                response: ModelResponse {
                    text,
                    calls,
                    raw: "scripted-catalog".into(),
                    truncated: false,
                },
                usage: None,
            },
        )])))
    }
}

fn read_json(path: &Path) -> Result<Value> {
    ensure!(!path.is_symlink(), "linked fixture is not allowed");
    let bytes = std::fs::read(path)?;
    ensure!(
        bytes.len() <= 1_000_000,
        "fixture exceeds development limit"
    );
    Ok(serde_json::from_slice(&bytes)?)
}

fn basename(text: &str) -> Result<&str> {
    ensure!(
        !text.is_empty()
            && text.len() <= 128
            && !text.contains("..")
            && text
                .bytes()
                .all(|b| b.is_ascii_alphanumeric() || b"._-".contains(&b)),
        "invalid fixture basename"
    );
    Ok(text)
}

fn script_steps(definition: &Value) -> Result<Vec<Value>> {
    let steps = definition["script"]
        .as_array()
        .context("script array required")?
        .clone();
    ensure!((2..=25).contains(&steps.len()), "bounded script required");
    let mut count = 0;
    for step in &steps {
        let object = step.as_object().context("script step required")?;
        ensure!(
            object.len() == 2 && object.contains_key("text") && object.contains_key("calls"),
            "unknown script field"
        );
        ensure!(
            step["text"].as_str().is_some_and(|s| s.len() <= 16_384),
            "bounded text required"
        );
        let calls = step["calls"].as_array().context("call array required")?;
        count += calls.len();
        for call in calls {
            let object = call.as_object().context("call object required")?;
            ensure!(
                object.len() == 2 && object.contains_key("tool") && object.contains_key("args"),
                "unknown call field"
            );
            let tool = Tool::parse(call["tool"].as_str().context("tool required")?)
                .map_err(|_| anyhow!("unknown scripted tool"))?;
            ensure!(
                matches!(
                    tool,
                    Tool::SkillRead
                        | Tool::GraphSummary
                        | Tool::TextSearch
                        | Tool::RawRecords
                        | Tool::EntityLookup
                        | Tool::EntityTimeline
                        | Tool::Neighbors
                        | Tool::GraphPath
                        | Tool::CaseAddFinding
                ),
                "episode tools must remain local"
            );
            let args = call["args"].as_object().context("arguments required")?;
            ensure!(
                args.len() <= 32
                    && args.iter().all(|(key, value)| key.len() <= 64
                        && value.as_str().is_some_and(|text| text.len() <= 16_384)),
                "bounded literal arguments required"
            );
        }
    }
    ensure!(count <= 100, "too many scripted calls");
    ensure!(
        steps.last().unwrap()["calls"]
            .as_array()
            .unwrap()
            .is_empty(),
        "final answer required"
    );
    Ok(steps)
}

fn case_store(path: &Path) -> Result<Arc<irmind_infra::LocalStore>> {
    use irmind_app::modules::{Module, ModuleConfig, ModuleRegistry};
    use irmind_mod_mapping_linux::{
        AuditMapping, AuthExtractionMapping, HttpMapping, SshdMapping, SuMapping, SudoMapping,
    };
    let mut modules: Vec<Box<dyn Module>> = vec![
        Box::new(irmind_mod_parser_json::JsonParser),
        Box::new(irmind_mod_parser_ecs::EcsParser),
        Box::new(irmind_mod_parser_ocsf::OcsfParser),
        Box::new(irmind_mod_parser_linux::LinuxParser),
        Box::new(irmind_mod_parser_syslog::SyslogParser),
        Box::new(irmind_mod_parser_zeek::ZeekParser),
        Box::new(irmind_mod_parser_suricata::SuricataParser),
        Box::new(irmind_mod_parser_entra::EntraParser),
        Box::new(irmind_mod_parser_gcp_audit::GcpAuditParser::default()),
        Box::new(irmind_mod_parser_kubernetes::KubernetesParser::default()),
        Box::new(irmind_mod_parser_falco::FalcoParser::default()),
        Box::new(irmind_mod_parser_velociraptor::VelociraptorParser),
        Box::new(irmind_mod_parser_hayabusa::HayabusaParser),
        Box::new(irmind_mod_parser_chainsaw::ChainsawParser),
        Box::new(irmind_mod_parser_plaso::PlasoParser),
        Box::new(irmind_mod_parser_eztools::EztoolsParser),
        Box::new(irmind_mod_mapping_json_compat::JsonCompatibilityMapping::generic_only()?),
        Box::new(irmind_mod_mapping_cloudtrail::CloudTrailMapping::new()?),
        Box::new(irmind_mod_mapping_ecs::EcsMapping::new()?),
        Box::new(irmind_mod_mapping_ocsf::OcsfMapping::new()?),
        Box::new(AuditMapping::new()?),
        Box::new(AuthExtractionMapping::new()?),
        Box::new(HttpMapping::new()?),
        Box::new(SshdMapping::new()?),
        Box::new(SudoMapping::new()?),
        Box::new(SuMapping::new()?),
        Box::new(irmind_mod_mapping_journald_compat::JournaldCompatibilityMapping::new()?),
        Box::new(irmind_mod_mapping_syslog::SyslogExtractionMapping::new()?),
        Box::new(irmind_mod_mapping_network::NetworkMapping::new(
            "parser-zeek",
        )?),
        Box::new(irmind_mod_mapping_network::NetworkMapping::new(
            "parser-suricata",
        )?),
        Box::new(irmind_mod_mapping_gcp_audit::CloudAuditMapping::new()?),
        Box::new(irmind_mod_mapping_gcp_audit::GkeMapping::new()?),
        Box::new(irmind_mod_mapping_falco::HostMapping::new()?),
        Box::new(irmind_mod_mapping_falco::KubernetesMapping::new()?),
        Box::new(irmind_mod_mapping_falco::AuditPluginMapping::new()?),
    ];
    for mapping in irmind_mod_mapping_kubernetes::KubernetesMapping::all()? {
        modules.push(Box::new(mapping));
    }
    for mapping in irmind_mod_mapping_entra::EntraMapping::all()? {
        modules.push(Box::new(mapping));
    }
    for parser in [
        "parser-velociraptor",
        "parser-hayabusa",
        "parser-chainsaw",
        "parser-plaso",
        "parser-eztools",
    ] {
        modules.push(Box::new(
            irmind_mod_mapping_dfir::DfirExtractionMapping::new(parser)?,
        ));
    }
    let mut registry = ModuleRegistry::new();
    for module in modules {
        registry.register(module, &ModuleConfig::new())?;
    }
    // Insert reviewed late-source registrations here.
    Ok(Arc::new(irmind_infra::LocalStore::open_mapped(
        path,
        Arc::new(registry.mapping_catalog()?),
    )?))
}

fn main() -> Result<()> {
    let mut args = std::env::args_os().skip(1);
    let repository = PathBuf::from(args.next().context("repository required")?).canonicalize()?;
    let family = args
        .next()
        .context("core or catalog required")?
        .into_string()
        .map_err(|_| anyhow!("invalid family"))?;
    ensure!(
        family == "core" || family == "catalog",
        "invalid package family"
    );
    let name = args
        .next()
        .context("skill required")?
        .into_string()
        .map_err(|_| anyhow!("invalid skill"))?;
    basename(&name)?;
    ensure!(args.next().is_none(), "unexpected argument");
    let episode = repository.join("episodes").join(&family).join(&name);
    ensure!(
        !repository.join("episodes").is_symlink()
            && !repository.join("episodes").join(&family).is_symlink()
            && !episode.is_symlink()
            && episode.canonicalize()?.starts_with(&repository),
        "linked or escaped episode directory"
    );
    let definition = read_json(&episode.join("episode.json"))?;
    ensure!(
        definition["format_version"] == 1 && definition["skill"] == name,
        "wrong episode identity"
    );
    let steps = script_steps(&definition)?;
    let scratch = tempfile::tempdir()?;
    let data = scratch.path().join("data");
    let source_root = scratch.path().join("sources");
    std::fs::create_dir_all(&source_root)?;
    let store = case_store(&data)?;
    let analyst = Arc::new(SyntheticSigner(
        Actor::Analyst,
        SigningKey::from_bytes(&[73; 32]),
    ));
    let agent = Arc::new(SyntheticSigner(
        Actor::Agent(
            AgentId::parse("catalog-scripted").map_err(|_| anyhow!("invalid synthetic agent"))?,
        ),
        SigningKey::from_bytes(&[74; 32]),
    ));
    let verifier = LocalVerifier::from_signer(analyst.as_ref())
        .with_trusted_key(&agent.actor(), &agent.public_key())?;
    let packages = irmind_infra::bundled_skill_candidates()?
        .into_iter()
        .map(|s| s.package().clone())
        .collect();
    let services = SkillServices::new(
        Arc::new(FileSkillPackageStore::new(scratch.path())),
        Arc::new(TomlSkillCompiler),
        agent,
        packages,
    )?;
    let ports = EnginePorts::new(
        store.clone(),
        store.clone(),
        store.clone(),
        store.clone(),
        CryptoPorts::new(analyst, Arc::new(verifier)),
        Arc::new(irmind_security::MandatoryGuard::new()?),
    )
    .with_source_evidence_reader(store.source_evidence_reader());
    let engine = Engine::new(ports, ExecutionMode::Attended, Arc::new(SystemClock))?
        .with_skills(services)?;
    let candidate_store = FileSkillPackageStore::new(&repository);
    let candidate = engine.preview_skill(
        &candidate_store,
        &TomlSkillCompiler,
        &repository.join(&family).join(&name),
        &CancellationToken::new(),
    )?;
    ensure!(
        candidate.metadata().name().as_str() == name,
        "wrong package identity"
    );
    if family == "catalog" {
        let services = engine.skill_services().unwrap();
        engine.install_skill(
            services.package_store(),
            services.compiler(),
            &candidate,
            SkillOrigin::Analyst,
            &BTreeSet::new(),
        )?;
    } else {
        let bundled = irmind_infra::bundled_skill_candidates()?;
        ensure!(
            bundled.iter().any(|s| s.metadata().name().as_str() == name
                && s.package().hash() == candidate.package().hash()),
            "core candidate was not embedded exactly"
        );
    }
    let case = engine.create_case(
        "Synthetic community skill evaluation",
        "local evidence only",
    )?;
    let files = definition["files"]
        .as_array()
        .context("source list required")?;
    ensure!(
        !files.is_empty() && files.len() <= 32,
        "bounded source list required"
    );
    let mut hashes = Vec::new();
    for source in files {
        let filename = basename(
            source["file"]
                .as_str()
                .context("source filename required")?,
        )?;
        let parser_name = source["parser"].as_str().context("parser required")?;
        let path = episode.join("source").join(filename);
        ensure!(
            !episode.join("source").is_symlink()
                && !path.is_symlink()
                && path.metadata()?.len() <= 1_000_000
                && path
                    .canonicalize()?
                    .starts_with(episode.canonicalize()?.join("source")),
            "source escapes public fixture directory"
        );
        std::fs::copy(&path, source_root.join(filename))?;
        let ingested = if let Some(cluster) = definition["cluster"].as_str() {
            let context = irmind_app::command_cluster_context(Some(cluster))?;
            let bytes = std::fs::read(&path)?;
            let catalog = current_sources::catalog();
            let selected = catalog.select_source(irmind_app::modules::ParserSelectionRequest {
                source: filename,
                sample: &bytes[..bytes.len().min(65_536)],
                parser_override: None,
                forced: false,
                time_context: None,
                cluster_context: context.as_ref(),
            })?;
            ensure!(
                selected.parser.parser_name() == parser_name,
                "wrong detected parser"
            );
            LargeCaseUseCases {
                engine: &engine,
                store: store.as_ref(),
                parser: selected.parser.as_ref(),
            }
            .ingest_local_batch_selected(
                &case.id,
                &source_root,
                &[filename.into()],
                false,
                &BTreeMap::from([(filename.into(), selected.selection)]),
                &CancellationToken::new(),
            )?
        } else {
            let parser = current_sources::parser(parser_name);
            LargeCaseUseCases {
                engine: &engine,
                store: store.as_ref(),
                parser: parser.as_ref(),
            }
            .ingest_local_batch(
                &case.id,
                &source_root,
                &[filename.into()],
                false,
                &CancellationToken::new(),
            )?
        };
        ensure!(ingested.len() == 1, "source was rejected");
        hashes.push(ingested[0].1.as_str().to_owned());
    }
    let selected = usize::try_from(
        definition["selected_source"]
            .as_u64()
            .context("selected source required")?,
    )?;
    ensure!(selected < hashes.len(), "selected source is out of bounds");
    let model = Scripted {
        steps,
        hashes,
        requests: Mutex::new(Vec::new()),
    };
    engine.investigate(&case.id, &format!("Use {name} to review this synthetic local episode; cite source evidence and retain uncertainty."), &model)?;
    let requests = model.requests.lock().unwrap();
    let query_ids = requests
        .iter()
        .flat_map(|request| &request.messages)
        .flat_map(|message| &message.tool_calls)
        .filter(|call| {
            matches!(
                call.proposal().tool,
                Tool::TextSearch | Tool::EntityLookup | Tool::EntityTimeline
            )
        })
        .map(|call| call.id().to_owned())
        .collect::<BTreeSet<_>>();
    ensure!(
        requests
            .iter()
            .flat_map(|request| &request.messages)
            .any(|message| {
                message.role == MessageRole::Tool
                    && message
                        .tool_call_id
                        .as_ref()
                        .is_some_and(|id| query_ids.contains(id))
                    && message.content.contains(&model.hashes[selected])
            }),
        "query did not retrieve the cited source"
    );

    // Private answers are opened only after the model has finished. The model has no filesystem port.
    let expected_name = basename(
        definition["expected_file"]
            .as_str()
            .context("expected fixture required")?,
    )?;
    ensure!(
        !repository.join("episodes/private").is_symlink(),
        "linked private answer directory"
    );
    let expected = read_json(&repository.join("episodes/private").join(expected_name))?;
    let marker = expected["private_marker"]
        .as_str()
        .context("private sentinel required")?;
    ensure!(
        !requests
            .iter()
            .flat_map(|request| &request.messages)
            .any(|message| message.content.contains(marker)),
        "private answers entered model context"
    );
    let expected = expected
        .get("episodes")
        .unwrap_or(&expected)
        .get(&name)
        .context("expected skill missing")?;
    let findings = engine.findings(&case.id)?;
    ensure!(
        findings.len() == 2,
        "expected exactly two proposed findings"
    );
    for (kind, key) in [
        (FindingKind::Hypothesis, "conclusion"),
        (FindingKind::Technique, "technique"),
    ] {
        ensure!(
            findings
                .iter()
                .any(|finding| finding.kind == kind
                    && finding.value == expected[key].as_str().unwrap()),
            "finding does not match independent evaluator"
        );
    }
    for finding in findings {
        ensure!(!finding.confirmed, "model confirmed its own finding");
        engine.confirm_finding(&case.id, &finding.id)?;
    }
    let entries = store.entries(&case.id)?;
    ensure!(
        entries
            .iter()
            .any(|entry| entry.kind == AuditEventKind::SkillLoadV1),
        "missing signed skill use"
    );
    ensure!(
        !entries.iter().any(|entry| entry.payload.contains(marker)),
        "private answers entered evidence"
    );
    engine.verify(&case.id)?;
    engine.seal(&case.id)?;
    let path = scratch.path().join("episode.irmind");
    let fingerprint = irmind_app::export_case_with_originals(
        &engine,
        store.as_ref(),
        &case.id,
        &path,
        Some(&source_root),
        true,
        &CancellationToken::new(),
    )?;
    LocalExportVerifier.verify_export_details(&path, Some(&fingerprint))?;
    println!(
        "{name}: scripted investigation, analyst confirmation, verification, seal and export passed"
    );
    Ok(())
}
