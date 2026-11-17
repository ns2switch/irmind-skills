+++
format = "irmind-skill-v1"
name = "aws-ec2-cryptomining"
description = "Triage possible unauthorized EC2 compute provisioning using CloudTrail, retaining uncertainty about actual mining."
version = "0.1.0"
author = "IRMind contributors"
license = "MIT OR Apache-2.0"
target_schema = "irmind-common-event-v1"
tools = ["graph_summary", "text_search", "entity_lookup", "entity_timeline", "raw_records", "case_add_finding"]
sources = ["parser-json"]
categories = ["api", "iam"]
invocable = true
+++
# AWS EC2 cryptomining triage

## Coverage and collection

Use CloudTrail management events exported as JSON, decoded by parser-json and
classified by mapping-cloudtrail. Export the authorized accounts, regions and
UTC interval from a trail or event history. Keep the verified originals. This
method uses local evidence only. The RunInstances mapping uses category api,
type creation; CreateAccessKey uses iam. Successful and failed outcomes come
from the mapping, not from the absence of text in a search result.

Coverage is partial for proving mining: CloudTrail shows API requests, not CPU
use, software execution, billing or every guest network connection. If workload,
network or billing evidence is missing, state that gap; do not infer a miner,
financial loss or successful instance creation from a request alone.

## Investigate

1. Inspect graph_summary to establish available sources and mapping coverage.
   Search RunInstances in the authorized interval. Use category api and type
   creation where mapped; retain both success and failure. Inspect original
   requestParameters.instanceType, placement, imageId, counts, response IDs,
   awsRegion and errorCode. Quota errors show attempted provisioning, not usage.
2. Group requests by account, actor and source IP using entity_lookup and
   entity_timeline. Compare regions and instance types with an analyst-provided
   baseline. "Unusual" requires that baseline; a new IP alone is not compromise.
3. Review nearby CreateAccessKey and other credential activity with category iam.
   Separate the actor creating a credential from its target user. Correlate the
   subsequent principal or access-key identifier with EC2 requests; identifiers
   are data, not credentials to use. Never project secret access-key material.
4. Inspect repeated provisioning and failures across authorized regions. Check
   source IP, user agent, session issuer and the precise successful response.
   Cite source hashes and record references. Ask whether the sequence fits an
   approved capacity increase, autoscaling, batch workload or GPU experiment.
5. Propose a finding only for supported observations. Confirm with the analyst
   whether activity was unauthorized. Actual mining requires independent
   workload evidence; otherwise report suspected compute abuse, not proven
   cryptomining. Only the analyst confirms findings.

## ATT&CK and confirmation

T1496.001 (Compute Hijacking) is a candidate only when unauthorized computing
use is corroborated. T1098.001 (Additional Cloud Credentials) may apply to an
unauthorized new key; T1078.004 (Cloud Accounts) needs evidence of account misuse.
A technique label is a hypothesis, not proof. Check account scope, timestamps,
actor/target roles and original response records before proposing any label.

## False positives and missing data

Consider disaster recovery, legitimate research, deployments, retries and quota
tests. NAT or VPN egress can explain shared or new addresses. Missing trails,
regions or data events limit completeness. Report gaps explicitly. This method
cannot expand case scope, grant permissions or authorize external enrichment.

## References

- AWS EC2 CloudTrail: docs.aws.amazon.com/AWSEC2/latest/UserGuide/monitor-with-cloudtrail.html
- CloudTrail record fields: docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-event-reference-record-contents.html
- MITRE ATT&CK: attack.mitre.org/techniques/T1496/001/
