# EC2 example: references and coverage

[Español](ec2-example.es.md) · [Method](../catalog/aws-ec2-cryptomining/SKILL.md)

The example uses original methodology and synthetic CloudTrail management events.
The [AWS EC2 CloudTrail guide](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/monitor-with-cloudtrail.html)
and [record-field reference](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-event-reference-record-contents.html)
explain the API evidence. [ATT&CK T1496.001](https://attack.mitre.org/techniques/T1496/001/)
describes Compute Hijacking; it is a candidate requiring corroboration, not an
inference from an instance request alone. New credentials can support a
[T1098.001](https://attack.mitre.org/techniques/T1098/001/) hypothesis when unauthorized.

The episode records key creation, cross-region provisioning and a quota failure.
It does not prove a miner executed, resource consumption or financial impact.
Expected answers are evaluator data outside the package and model context.

Clickable references stay in repository documentation, outside the installable
package. ContentGuard screens every package resource; URLs and role/tool-execution
directives can trigger its existing admission checks. Name references in the method,
write investigative steps and verify the exact package with the released compiler
and episode. Reviewer heuristics never override ContentGuard or policy.
