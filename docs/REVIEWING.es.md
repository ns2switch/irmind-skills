# Revisar y publicar skills

[English](REVIEWING.md)

## Automatización y revisión humana

La CI usa el compilador de la última release de IRMind, valida límites, hashes,
fuentes y mapeos del build por defecto, nombres reservados y aumentos SemVer.
Ejecuta los episodios scripted con admisión firmada, consultas, hallazgos propuestos
y confirmados por el analista, verificación, sello y exportación. Las respuestas
esperadas quedan fuera del paquete y del contexto. Los avisos de herramientas
inusuales o texto parecido a instrucciones no demuestran seguridad ni corrección.

Una persona revisa la metodología, las herramientas mínimas, los falsos positivos,
la cobertura honesta, las instrucciones de recogida, la autoría y la calidad del
episodio. Busca intentos directos o indirectos de ignorar política, pedir aprobaciones
o ampliar alcance. No ejecutes contenido del paquete. No se admiten datos reales
ni secretos, ni se confirma una técnica por una simple coincidencia de consulta.

Las PR no acceden a secretos ni al environment release y tienen permisos de lectura.
El workflow de comentarios usa código de main, valida el origen y lee JSON acotado
como datos; nunca ejecuta código de la PR. Configura la aprobación de workflows de forks.

## Publicación

1. Tras la CI y la revisión, aumenta `release_sequence` en `catalog-release.json`
   mediante PR. Elige una etiqueta nueva y no sustituyas índices ni tags publicados.
   Cualquier cambio de una metodología requiere aumentar su versión.
2. Crea el tag sobre main en verde y lanza **Publish signed skill catalog**
   (`release.yml`) sobre ese tag. Se fija el commit del compilador publicado de
   IRMind y `core/` nunca entra en el índice.
3. Revisa tag, secuencia, paquetes y validación antes de aprobar el environment
   protegido **release**. Solo el proceso firmante lee `CATALOG_ED25519_SEED_HEX`:
   nunca se pasa por argumentos, ficheros ni artefactos. El ensayo sintético está
   separado. No actives trazas ni imprimas el entorno. Una clave pública distinta
   produce un error cerrado.
4. Comprueba la firma Ed25519, los bundles Sigstore, la procedencia y el SBOM.
   Descarga y verifica de forma independiente con `tools/verify_release.py`
   (README). Contrasta el key_id con las claves compiladas en IRMind y la identidad
   OIDC exacta del tag.
5. Prueba `/skills install catalog:<nombre>` con el binario publicado: vista previa,
   cobertura, herramientas, admisión firmada, uso sintético, verificación, sello y
   exportación. Conserva las pruebas de índice alterado, otra clave y secuencia anterior.

## Corrección y retirada

Publica otra versión con sus notas; nunca sobrescribas assets. Para retirar una
skill, elimínala de un índice de secuencia mayor y explica el motivo en las notas.
Las instalaciones existentes no cambian automáticamente: indica cómo inspeccionar,
actualizar o desactivar. Retirar una clave compilada exige una release de IRMind.

Los problemas se corrigen con texto técnico neutro y se publican según la política
pre-1.0 de IRMind. Mantén privados los informes sensibles; nunca publiques secretos
ni datos de incidentes. El mantenedor decide si retirar, corregir o rotar la clave.

## Registrar las comprobaciones de la release

Tras publicar, lanza el workflow nativo con tags exactos:

```sh
gh workflow run verify-published.yml -R ns2switch/irmind-skills --ref main -f irmind_tag=v0.5.4 -f catalog_tag=v0.1.0
```

Instala la release firmada de IRMind, verifica el catálogo de forma independiente
y prueba el ejecutable publicado en Linux, macOS y Windows. Un índice alterado o
una firma de otra clave no deben dejar una admisión firmada. El contrato con
historial sintético firmado comprueba que un descenso requiere la confirmación
separada del analista; la primera release de producción no tiene un índice anterior
que reproducir.

Una corrección aumenta la versión del paquete y explica el cambio en la descripción
de cobertura de `metadata/<nombre>.json`, dentro del límite de 512 bytes existente.
Esa descripción queda firmada en el índice. La retirada completa elimina la entrada
del siguiente índice de secuencia mayor y se explica en las notas. No añadas
instrucciones sin firma ni campos que el formato del índice no soporte.
