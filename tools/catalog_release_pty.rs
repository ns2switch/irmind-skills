#![forbid(unsafe_code)]
#![allow(clippy::unwrap_used, clippy::too_many_lines)]
//! Development test: uses an installed, signed IRMind executable, never a model provider.
#[path = "support/current_sources.rs"] mod current_sources;
#[path = "support/demo_session.rs"] mod demo_session;
#[path = "support/terminal_screen.rs"] mod terminal_screen;
use irmind_app::{AuditLog as _, ConfigChange, CryptoPorts, Engine, EnginePorts, FindingKind, SignerBackend as _};
use irmind_domain::{Actor, ExecutionMode};
use irmind_infra::{LocalVerifier, SystemClock, TomlConfigurationStore};
use irmind_mod_keystore_file::FileKeystore;
use secrecy::SecretString;
use std::{io::{Read,Write},net::TcpListener,path::{Path,PathBuf},process::{Command,Stdio},sync::{Arc,Mutex,atomic::{AtomicBool,Ordering}},time::Duration};
const PHRASE:&str="Synthetic catalog release PTY passphrase";
const NAME:&str="aws-ec2-cryptomining";
fn binary()->PathBuf {std::env::var_os("IRMIND_CATALOG_PTY_BINARY").expect("published binary required").into()}
fn seed(root:&Path){
 let backend=FileKeystore::open(root,&SecretString::from(PHRASE.to_owned()),true).unwrap();
 let signer=backend.create(Actor::Analyst).unwrap();
 let store=Arc::new(current_sources::open(root));
 let engine=Engine::new(EnginePorts::new(store.clone(),store.clone(),store.clone(),store.clone(),CryptoPorts::new(signer.clone(),Arc::new(LocalVerifier::from_signer(signer.as_ref()))),Arc::new(irmind_security::MandatoryGuard::new().unwrap())),ExecutionMode::Attended,Arc::new(SystemClock)).unwrap();
 engine.create_case("Synthetic catalog bootstrap", "local evidence only").unwrap();
 let config=root.join("keystore.toml");
 std::fs::write(&config,format!("[keystore]\nsigner = \"file\"\nsecrets = \"file\"\nanalyst_key_fingerprint = \"{}\"\n",irmind_app::hex(&irmind_app::sha256(&signer.public_key())))).unwrap();
 irmind_fs::private_file(&config).unwrap();
}
fn command(root:&Path)->Command {
 #[cfg(unix)] let mut c={let mut c=Command::new("sh");c.args(["-c","stty cols 120 rows 40; exec \"$0\" --home \"$1\""]).arg(binary()).arg(root);c};
 #[cfg(windows)] let mut c={let mut c=Command::new("cmd.exe");c.args(["/d","/c","chcp","65001",">nul","&&"]).arg(binary()).arg("--home").arg(root).args(["<CONIN$",">CONOUT$","2>&1"]);c};
 c.env("TERM","xterm-256color").env("NO_COLOR","1");c
}
fn cli(root:&Path,args:&[&str])->String {
 let mut child=Command::new(binary()).arg("--home").arg(root).args(["--passphrase-fd","0"]).args(args).stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::piped()).spawn().unwrap();
 child.stdin.take().unwrap().write_all(PHRASE.as_bytes()).unwrap();
 let out=child.wait_with_output().unwrap();assert!(out.status.success(),"command failed: {}",String::from_utf8_lossy(&out.stderr));String::from_utf8(out.stdout).unwrap()
}
fn configure(root:&Path,url:&str){
 let backend=FileKeystore::open(root,&SecretString::from(PHRASE.to_owned()),false).unwrap();let signer=backend.load(Actor::Analyst).unwrap();
 let store=Arc::new(current_sources::open(root));
 let engine=Engine::new(EnginePorts::new(store.clone(),store.clone(),store.clone(),store.clone(),CryptoPorts::new(signer.clone(),Arc::new(LocalVerifier::from_signer(signer.as_ref()))),Arc::new(irmind_security::MandatoryGuard::new().unwrap())),ExecutionMode::Attended,Arc::new(SystemClock)).unwrap();
 engine.apply_configuration_change(&TomlConfigurationStore::new(root),&[&irmind_mod_llm_openai_compatible::MANIFEST],ConfigChange::ConfigureModel(irmind_app::ModelConfiguration{module:"llm-openai-compatible".into(),base_url:url.into(),model:"synthetic-local-catalog".into(),maximum_output_tokens:Some(4096),output_required:false}),true).unwrap();
}
#[test]
fn published_binary_installs_catalog_and_completes_signed_synthetic_case(){
 let repo=PathBuf::from(std::env::var_os("IRMIND_SKILLS_REPOSITORY").expect("skills repository required"));
 let tag=std::env::var("IRMIND_CATALOG_TAG").expect("frozen catalog tag required");
 let home=tempfile::tempdir().unwrap();seed(home.path());
 // Install from the real GitHub release with the published binary's compiled trust roots.
 let mut session=demo_session::DemoSession::spawn_sized(&command(home.path()),120,40).unwrap();
 session.expect("Unlock").unwrap();session.send(format!("{PHRASE}\r")).unwrap();session.expect("Fingerprint").unwrap();session.send("\r").unwrap();session.expect("Find cases or type").unwrap();
 session.send(format!("/skills install catalog:{NAME}@{tag}\r")).unwrap();session.expect("Release tag").unwrap();session.send("\r").unwrap();
 session.expect("2. Sign and apply").unwrap();session.expect("SHA-256:").unwrap();session.send("2\r").unwrap();session.expect("Skill state applied").unwrap();
 session.send("\x1b").unwrap();session.expect("Find cases or type").unwrap();session.send("/quit\r").unwrap();session.expect("Exit IRMind?").unwrap();session.send("\r").unwrap();session.expect_exit().unwrap();drop(session);
 let episode=repo.join("episodes/catalog").join(NAME);
 let definition:serde_json::Value=serde_json::from_slice(&std::fs::read(episode.join("episode.json")).unwrap()).unwrap();
 let source=episode.join("source/ec2.json");let hash=irmind_app::hex(&irmind_app::sha256(&std::fs::read(&source).unwrap()));
 let script=definition["script"].as_array().unwrap().clone();
 let listener=TcpListener::bind("127.0.0.1:0").unwrap();listener.set_nonblocking(true).unwrap();let address=listener.local_addr().unwrap();
 let stop=Arc::new(AtomicBool::new(false));let stop_server=stop.clone();let captured=Arc::new(Mutex::new(Vec::<serde_json::Value>::new()));let capture=captured.clone();
 let server=std::thread::spawn(move||{
  let mut index=0;
  while !stop_server.load(Ordering::Relaxed){
   let (mut stream,_)=match listener.accept(){Ok(s)=>s,Err(e) if e.kind()==std::io::ErrorKind::WouldBlock=>{std::thread::sleep(Duration::from_millis(5));continue},Err(e)=>panic!("{e}")};
   stream.set_read_timeout(Some(Duration::from_secs(10))).unwrap();let mut buffer=Vec::new();let mut part=[0u8;8192];
   let header=loop{let n=stream.read(&mut part).unwrap();assert!(n>0);buffer.extend_from_slice(&part[..n]);assert!(buffer.len()<=2_000_000);if let Some(pos)=buffer.windows(4).position(|p|p==b"\r\n\r\n"){break pos+4}};
   let headers=String::from_utf8_lossy(&buffer[..header]);let length=headers.lines().find_map(|line|line.to_ascii_lowercase().strip_prefix("content-length:").map(|v|v.trim().parse::<usize>().unwrap())).unwrap();assert!(length<=1_000_000);
   while buffer.len()<header+length{let n=stream.read(&mut part).unwrap();assert!(n>0);buffer.extend_from_slice(&part[..n]);}
   let request:serde_json::Value=serde_json::from_slice(&buffer[header..header+length]).unwrap();capture.lock().unwrap().push(request);
   let step=&script[index];let text=step["text"].as_str().unwrap().replace("$source:0",&hash);
   let calls=step["calls"].as_array().unwrap().iter().enumerate().map(|(offset,call)|{
    let args=call["args"].as_object().unwrap().iter().map(|(k,v)|(k.clone(),serde_json::Value::String(v.as_str().unwrap().replace("$source:0",&hash)))).collect::<serde_json::Map<_,_>>();
    serde_json::json!({"index":offset,"id":format!("published_{index}_{offset}"),"type":"function","function":{"name":call["tool"],"arguments":serde_json::to_string(&args).unwrap()}})
   }).collect::<Vec<_>>();
   let delta=if calls.is_empty(){serde_json::json!({"content":text})}else{serde_json::json!({"tool_calls":calls})};
   let first=serde_json::json!({"id":"synthetic-catalog","choices":[{"index":0,"delta":delta,"finish_reason":null}]});
   let last=serde_json::json!({"id":"synthetic-catalog","choices":[{"index":0,"delta":{},"finish_reason":if calls.is_empty(){"stop"}else{"tool_calls"}}],"usage":{"prompt_tokens":100,"completion_tokens":25,"total_tokens":125}});
   let body=format!("data: {first}\n\ndata: {last}\n\ndata: [DONE]\n\n");
   write!(stream,"HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",body.len(),body).unwrap();index+=1;if index==script.len(){break}
  }
  index
 });
 configure(home.path(),&format!("http://{address}/v1/"));
 let id=cli(home.path(),&["case","new","Published catalog synthetic test","--scope","local evidence only"]).trim().to_owned();
 cli(home.path(),&["ingest",&id,source.to_str().unwrap()]);
 let answer=cli(home.path(),&["ask",&id,"Use aws-ec2-cryptomining on this synthetic local case; cite the evidence and keep uncertainty."]);
 assert!(answer.contains("actual mining remains unproven"));stop.store(true,Ordering::Relaxed);assert_eq!(server.join().unwrap(),definition["script"].as_array().unwrap().len());
 // Only now open evaluator answers. They were neither evidence nor model context.
 let expected:serde_json::Value=serde_json::from_slice(&std::fs::read(repo.join("episodes/private/ec2-cryptomining.json")).unwrap()).unwrap();
 assert!(captured.lock().unwrap().iter().all(|r|!r.to_string().contains(expected["private_marker"].as_str().unwrap())));
 let parsed=irmind_domain::CaseId::parse(&id).unwrap();
 let findings={let store=current_sources::open(home.path());let entries=store.entries(&parsed).unwrap();assert!(entries.iter().any(|e|e.kind==irmind_domain::AuditEventKind::SkillLoadV1));drop(store);cli(home.path(),&["findings",&id])};
 assert!(findings.contains("T1098.001"));
 // Inspect typed findings through the real repository, then confirm with the published CLI.
 let ids={let backend=FileKeystore::open(home.path(),&SecretString::from(PHRASE.to_owned()),false).unwrap();let signer=backend.load(Actor::Analyst).unwrap();let store=Arc::new(current_sources::open(home.path()));let engine=Engine::new(EnginePorts::new(store.clone(),store.clone(),store.clone(),store.clone(),CryptoPorts::new(signer.clone(),Arc::new(LocalVerifier::from_signer(signer.as_ref()))),Arc::new(irmind_security::MandatoryGuard::new().unwrap())),ExecutionMode::Attended,Arc::new(SystemClock)).unwrap();let fs=engine.findings(&parsed).unwrap();assert_eq!(fs.len(),2);assert!(fs.iter().all(|f|!f.confirmed));assert!(fs.iter().any(|f|f.kind==FindingKind::Hypothesis && f.value==expected["episodes"][NAME]["conclusion"].as_str().unwrap()));fs.into_iter().map(|f|f.id).collect::<Vec<_>>()};
 for id_finding in ids{cli(home.path(),&["confirm-finding",&id,&id_finding]);}
 cli(home.path(),&["verify",&id,"--source-root",source.parent().unwrap().to_str().unwrap()]);cli(home.path(),&["seal",&id]);
 let exported=home.path().join("published-catalog.irmind");cli(home.path(),&["export",&id,exported.to_str().unwrap(),"--include-originals","--source-root",source.parent().unwrap().to_str().unwrap()]);
 let expected_key={let backend=FileKeystore::open(home.path(),&SecretString::from(PHRASE.to_owned()),false).unwrap();irmind_app::hex(&irmind_app::sha256(&backend.load(Actor::Analyst).unwrap().public_key()))};
 cli(home.path(),&["verify-export",exported.to_str().unwrap(),"--expected-key",&expected_key]);
 eprintln!("Published binary: catalog preview, signed admission, scripted local investigation, analyst confirmation, verification, seal and export passed.");
}
