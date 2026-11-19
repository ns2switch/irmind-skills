// Use the production implementations of the additional offline sources.
fn register_added_sources(registry: &mut irmind_app::modules::ModuleRegistry) -> Result<()> {
    use irmind_app::modules::{Module, ModuleConfig};
    use irmind_mod_mapping_cloud_flow::CloudFlowMapping;
    use irmind_mod_mapping_identity::IdentityMapping;

    let mut modules: Vec<Box<dyn Module>> = vec![
        Box::new(irmind_mod_parser_s3_access::S3AccessParser),
        Box::new(irmind_mod_mapping_s3_access::S3AccessMapping::new()?),
        Box::new(irmind_mod_parser_elb::ElbParser),
        Box::new(irmind_mod_mapping_elb::ElbMapping::new()?),
        Box::new(irmind_mod_parser_iis_w3c::IisW3cParser),
        Box::new(irmind_mod_mapping_iis_w3c::IisW3cMapping::new()?),
        Box::new(irmind_mod_parser_windows_dns::WindowsDnsParser),
        Box::new(irmind_mod_mapping_windows_dns::WindowsDnsMapping::new()?),
        Box::new(irmind_mod_parser_route53::Route53Parser),
        Box::new(irmind_mod_mapping_route53::Route53Mapping::new()?),
        Box::new(irmind_mod_parser_github_audit::GitHubAuditParser),
        Box::new(irmind_mod_mapping_github_audit::GitHubAuditMapping::new()?),
        Box::new(irmind_mod_parser_google_workspace::GoogleWorkspaceParser),
        Box::new(irmind_mod_mapping_google_workspace::GoogleWorkspaceMapping::new()?),
        Box::new(irmind_mod_parser_macos::MacosParser),
        Box::new(irmind_mod_mapping_macos::MacosMapping::new()?),
        Box::new(irmind_mod_parser_fdr::FdrParser),
        Box::new(irmind_mod_mapping_fdr::FdrMapping::new()?),
        Box::new(irmind_mod_parser_defender::DefenderParser),
        Box::new(irmind_mod_mapping_defender::DefenderMapping::new()?),
        Box::new(irmind_mod_parser_email::EmailParser),
        Box::new(irmind_mod_mapping_email::EmailMapping::new()?),
        Box::new(irmind_mod_parser_vpc_flow::VpcFlowParser),
        Box::new(CloudFlowMapping::aws()?),
        Box::new(irmind_mod_parser_azure_flow::AzureFlowParser),
        Box::new(irmind_mod_parser_gcp_flow::GcpFlowParser),
        Box::new(CloudFlowMapping::gcp()?),
        Box::new(irmind_mod_parser_guardduty::GuardDutyParser),
        Box::new(irmind_mod_mapping_guardduty::GuardDutyMapping::new()?),
        Box::new(irmind_mod_parser_m365::M365Parser),
        Box::new(IdentityMapping::m365()?),
        Box::new(irmind_mod_parser_okta::OktaParser),
        Box::new(IdentityMapping::okta()?),
    ];
    for mapper in CloudFlowMapping::azure()? {
        modules.push(Box::new(mapper));
    }
    for module in modules {
        registry.register(module, &ModuleConfig::new())?;
    }
    Ok(())
}
