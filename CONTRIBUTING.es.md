# Contribuir skills

Las skills de IRMind son metodologías de datos con licencia MIT OR Apache-2.0.
Escribe texto propio, cita fuentes públicas y usa evidencia sintética. No incluyas
datos de incidentes, credenciales, ejecutables, scripts ni instrucciones que
debiliten la política, custodia, ContentGuard, alcance, aprobaciones o TLS.

## Elegir el directorio

| Directorio | Distribución | Cambios |
| --- | --- | --- |
| `core/<nombre>/` | Incluido en cada release de IRMind | Mejora aquí una skill del núcleo; una PR normal de sincronización fija el commit en IRMind. |
| `catalog/<nombre>/` | Instalación opcional admitida por el analista | Añade métodos especializados con nombre distinto. Su distribución independiente llegará tras configurar la clave del publicador. |

No dupliques ni renombres paquetes del núcleo en `catalog/`. El constructor del
índice e IRMind rechazan los nombres que sustituyan al núcleo. Las skills de
`core/` no son entradas instalables del catálogo. Una firma nunca concede permisos
ni convierte una metodología en código ejecutable.

## Paquete y episodio

Parte de [la plantilla](template/package/SKILL.md). Incluye `SKILL.md` y recursos de texto
opcionales en `queries/`, `rules/` o `references/`. Respeta el compilador de la
última release publicada: actualmente 32 KiB por fichero, dieciséis recursos
adicionales y 128 KiB en total. Declara solo las herramientas necesarias, la
cobertura real de fuentes y mapeos, falsos positivos y criterios de confirmación.

Pon el guion en `episodes/<core|catalog>/<nombre>/episode.json` y las fuentes
sintéticas públicas en su directorio `source/`. Las respuestas esperadas van en
`episodes/private/`, nunca en el paquete ni en las fuentes. El guion contiene
llamadas locales literales y referencias a índices de fuente; no contiene código.
El evaluador abre las respuestas privadas después de terminar el modelo.
Cada episodio recupera evidencia real de sus fuentes, carga la skill, propone
hallazgos sin confirmar, los confirma como analista sintético, verifica, sella y
verifica de manera independiente la exportación.

Cada entrada del catálogo lleva `metadata/<nombre>.json` con
`minimum_irmind_version`, `mappings` y `coverage` (`status` y `description`
acotada). Esta información queda fuera del paquete instalable. La versión,
esquema y fuentes coinciden con el paquete; un mapeo ausente no es cobertura total.

Actualiza los compromisos con `python3 tools/inventory.py --write`; compruébalos
con `python3 tools/inventory.py` y `python3 -m unittest discover -s tests -v`.
Los cambios de fixtures del núcleo actualizan también el espejo explícito. El
espejo nunca acepta código del compilador o del motor. La CI fija la etiqueta y
el commit de la última release publicada, usa su compilador y motor sin cambios
y ejecuta episodios locales guionizados sin credenciales de proveedores. Estas
pruebas validan integración y controles, no precisión forense en incidentes reales.

## Confianza y publicación

No hay descargas ni actualizaciones automáticas. Instalar o actualizar exige
verificar el índice del publicador, revisar el contenido y firmar la admisión por
separado. La skill sigue siendo contenido no confiable y nunca entra en system.
La firma del catálogo y la admisión del analista son garantías diferentes.

La publicación de producción está desactivada. El ensayo manual usa una clave
Ed25519 sintética conocida, Sigstore y attestations de GitHub; solo sube artefactos
de CI. Nunca compiles esa clave en IRMind ni la uses en producción. El mantenedor
genera y configura la clave real por separado.

Antes de 1.0, una versión menor puede cambiar formatos sin migración. Adapta las
pruebas al último compilador publicado; no añadas intérpretes históricos ni
reescribas silenciosamente un paquete admitido.

[English](CONTRIBUTING.md)
