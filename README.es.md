# Skills de IRMind

Repositorio fuente de las skills forenses de datos de [IRMind](https://github.com/ns2switch/irmind).

- `core/` contiene los paquetes incluidos en cada release de IRMind. IRMind compila una copia local fijada y nunca descarga skills al compilar.
- `catalog/` contiene paquetes opcionales de la comunidad para `/skills install catalog:<nombre>`. Los nombres del núcleo nunca son entradas instalables del catálogo.
- Los episodios sintéticos y las respuestas exclusivas del evaluador quedan fuera de los paquetes instalables.

Una skill no concede permisos. Siguen mandando la política, el alcance del caso, el techo de la organización, ContentGuard y las aprobaciones del analista. Los paquetes no contienen código ejecutable.

No se publican releases de producción del catálogo hasta disponer de su clave de firma. Los ensayos usan solo claves sintéticas.

[English](README.md)

Licencia MIT OR Apache-2.0.

## Paquetes y validación

Hay **15 paquetes del núcleo** y **0 entradas instalables del catálogo**. Los compromisos originales de v0.5.0 están en [el inventario](core/package-identities.json) y [la referencia inicial](core/baseline.json).

| Skill | Fuentes declaradas |
| --- | --- |
| [aws-credential-compromise](core/aws-credential-compromise/SKILL.md) | parser-json |
| [aws-s3-data-exfiltration](core/aws-s3-data-exfiltration/SKILL.md) | parser-json |
| [azure-entra-identity-compromise](core/azure-entra-identity-compromise/SKILL.md) | parser-entra, parser-ecs, parser-json |
| [gcp-service-account-abuse](core/gcp-service-account-abuse/SKILL.md) | parser-gcp-audit, parser-ecs |
| [k8s-cluster-compromise](core/k8s-cluster-compromise/SKILL.md) | parser-kubernetes, parser-gcp-audit, parser-falco |
| [k8s-workload-compromise](core/k8s-workload-compromise/SKILL.md) | parser-kubernetes, parser-falco, parser-gcp-audit |
| [linux-persistence](core/linux-persistence/SKILL.md) | parser-linux, parser-ecs, parser-velociraptor, parser-plaso |
| [linux-triage](core/linux-triage/SKILL.md) | parser-linux, parser-syslog |
| [linux-webshell](core/linux-webshell/SKILL.md) | parser-linux, parser-ecs |
| [malware-execution-triage](core/malware-execution-triage/SKILL.md) | parser-evtx, parser-ecs, parser-eztools, parser-velociraptor, parser-plaso |
| [network-c2-beaconing](core/network-c2-beaconing/SKILL.md) | parser-zeek, parser-suricata, parser-ecs |
| [windows-lateral-movement](core/windows-lateral-movement/SKILL.md) | parser-evtx, parser-ecs, parser-hayabusa, parser-velociraptor |
| [windows-persistence](core/windows-persistence/SKILL.md) | parser-evtx, parser-ecs, parser-eztools, parser-velociraptor, parser-plaso |
| [windows-ransomware](core/windows-ransomware/SKILL.md) | parser-evtx, parser-ecs, parser-eztools, parser-velociraptor, parser-plaso |
| [windows-triage](core/windows-triage/SKILL.md) | parser-evtx, parser-hayabusa, parser-eztools, parser-velociraptor, parser-plaso |

[Contribuir](CONTRIBUTING.es.md) · [Plantilla del paquete](template/package/SKILL.md) · [Ejemplo de episodio](template/episode/episode.json)

La CI fija una etiqueta y un commit de la última release publicada de IRMind, incluido su estado preliminar. Usa su compilador real, límites, política, guard y motor; ejecuta los 15 episodios y las pruebas existentes de contenido malicioso, verifica, sella y exporta. No necesita claves de proveedores. Las respuestas privadas están en `episodes/private/` y solo se abren después del modelo.

El índice firmado contiene solo `catalog/`. Los paquetes de `core/` llegan con cada release de IRMind y no se instalan con `/skills install catalog:`. Para proponer mejoras al núcleo abre una PR aquí; un script de desarrollo crea una copia local fijada mediante una PR normal de IRMind. El build de IRMind nunca descarga paquetes.

El ensayo manual produce índices con una clave Ed25519 sintética conocida, bundles de Sigstore, procedencia de GitHub y un SBOM. Solo guarda artefactos de CI: no crea releases ni accede a claves de producción. Para verificar externamente un artefacto usa `cosign verify-blob` con la identidad exacta del workflow y `gh attestation verify`; la identidad del ensayo corresponde a su rama, no a una release de producción.

## Proponer una skill

[Contribuye una metodología](CONTRIBUTING.es.md) sin Rust: fuentes, falsos positivos, consultas y episodios sintéticos. `core/` llega con IRMind; `catalog/` solo se instala tras una release firmada aprobada por el mantenedor. Empieza por [el ejemplo EC2](catalog/aws-ec2-cryptomining/SKILL.md).

## Verificar una release del catálogo

Necesitas OpenSSL 3, cosign 3.1.3+ y una versión actual de GitHub CLI. Descarga
los assets del tag exacto y verifica de forma independiente Ed25519, hashes,
SHA256SUMS, identidad Sigstore y procedencia:

```sh
gh release download v0.1.0 -R ns2switch/irmind-skills -D verified-catalog
python3 -B tools/verify_release.py --directory verified-catalog
```

El key_id de producción es
`f04daae3f8243ed76452d5f787ea527c8fbec895ca0c91a35f453f6677575e4f`.
La identidad Sigstore exacta es
`https://github.com/ns2switch/irmind-skills/.github/workflows/release.yml@refs/tags/v0.1.0`,
con emisor `https://token.actions.githubusercontent.com`. IRMind v0.5.4 lleva la
clave pública Ed25519 compilada y no necesita cosign en ejecución. Instala de forma
explícita con `/skills install catalog:aws-ec2-cryptomining`, revisa cobertura y
herramientas y firma la admisión. Los nombres del núcleo no se sustituyen.
La [guía de revisión](docs/REVIEWING.es.md) explica publicación y retirada.
Los ensayos sintéticos nunca usan la semilla de producción.
