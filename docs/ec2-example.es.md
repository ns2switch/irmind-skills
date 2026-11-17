# Ejemplo EC2: referencias y cobertura

[English](ec2-example.md) · [Método](../catalog/aws-ec2-cryptomining/SKILL.md)

El ejemplo usa metodología propia y eventos sintéticos de administración de CloudTrail.
La [guía de EC2 y CloudTrail](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/monitor-with-cloudtrail.html)
y la [referencia de campos](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-event-reference-record-contents.html)
explican la evidencia de API. [ATT&CK T1496.001](https://attack.mitre.org/techniques/T1496/001/)
describe Compute Hijacking: requiere corroboración, no se deduce de una petición
de instancia. Las credenciales nuevas pueden apoyar una hipótesis
[T1098.001](https://attack.mitre.org/techniques/T1098/001/) si no estaban autorizadas.

El episodio registra una clave nueva, aprovisionamiento entre regiones y un error
de cuota. No demuestra ejecución de un minero, consumo real ni impacto económico.
Las respuestas esperadas quedan fuera del paquete y del contexto del modelo.

Los enlaces completos se conservan en documentación del repositorio, fuera del
paquete instalable. ContentGuard revisa cada recurso: las URL y las instrucciones
de rol o de ejecutar herramientas pueden activar sus controles de admisión
existentes. Cita las referencias por su nombre en el método, escribe pasos de
investigación y valida el paquete exacto con el compilador publicado y el episodio.
Las heurísticas de revisión nunca sustituyen a ContentGuard ni a la política.
