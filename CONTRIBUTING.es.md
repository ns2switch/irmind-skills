# Contribuir una skill forense

[English](CONTRIBUTING.md) · [Guía de revisión](docs/REVIEWING.es.md)

Puedes mejorar una metodología sin escribir Rust. Para una skill nueva se
recomienda abrir antes una propuesta **Skill proposal**, especialmente si hay
dudas de cobertura; los cambios pequeños pueden ir directamente a una PR.

1. Haz un fork y crea `catalog/<nombre>/` a partir de `template/package/`.
   [aws-ec2-cryptomining](catalog/aws-ec2-cryptomining/SKILL.md) es el ejemplo
   completo. Usa minúsculas y guiones; los nombres de `core/` están reservados.
2. Completa el frontmatter: format, name, description, versión SemVer, author,
   license, target_schema, tools, sources, categories e invocable. Describe los
   pasos con consultas por categoría, tipo, resultado y rol del esquema común.
   Incluye fuentes y mapeos, cómo recogerlos, cobertura, técnicas ATT&CK,
   criterios de confirmación y falsos positivos. Declara las herramientas mínimas.
3. Añade `metadata/<nombre>.json` con los mismos campos del ejemplo. Las fuentes
   principales y los mapeos deben existir en la compilación por defecto de la
   última release publicada de IRMind. La cobertura parcial debe explicarse;
   una fuente principal no soportada bloquea la contribución.
4. Añade un episodio pequeño en `episodes/catalog/<nombre>/` con `episode.json`
   y `source/`. Guarda las respuestas esperadas en `episodes/private/`, fuera
   del paquete instalable. El modelo scripted consulta evidencia y propone;
   la confirmación sigue siendo del analista.
5. Prepara un clon limpio de la última release publicada de IRMind fuera de este
   repo: el validador superpone allí los fixtures. Con su toolchain de Rust,
   Python 3.11+ y cargo-nextest, ejecuta:

   ```sh
   git fetch origin main
   git worktree add --detach ../skills-baseline origin/main
   python3 -B -m unittest discover -s tests -v
   python3 -B tools/review.py --root . --baseline ../skills-baseline --irmind ../irmind-release --output review-results.json
   python3 -B tools/validate.py --irmind ../irmind-release
   git worktree remove ../skills-baseline
   ```

   El compilador publicado y el motor real son la referencia. Los episodios usan
   respuestas scripted, sin proveedores ni respuestas esperadas en el contexto.
6. Abre la PR con su lista de comprobación. Explica cambios, cobertura y herramientas.
   Todo cambio del paquete aumenta SemVer: patch para correcciones, minor para
   metodología adicional y major para cambios incompatibles. Los metadatos de
   build no cuentan como aumento de versión.

## Texto y licencia

Texto propio con licencia **MIT OR Apache-2.0**. Puedes citar documentación pública
sin copiar material protegido. Solo datos sintéticos: nada de incidentes reales,
secretos, datos personales, ejecutables o scripts. No se permiten instrucciones
para ignorar política, pedir aprobaciones, ampliar alcance o atribuir autoridad
a la skill. Los recursos son datos y pasan por ContentGuard y los controles normales.

## Núcleo y catálogo

Las mejoras de `core/` llegan con una PR de sincronización y una release de IRMind.
Actualiza sus inventarios con `tools/inventory.py --write`. Sus nombres no se
publican en el índice del catálogo y no pueden sustituirse desde él.

Las skills de `catalog/` se instalan de forma independiente. Estar en main **no
significa estar publicada**: el mantenedor prepara lotes revisados sin un calendario
fijo y aprueba una release firmada. Después, el analista ejecuta explícitamente
`/skills install catalog:<nombre>`, revisa el contenido y firma la admisión.
No hay descargas ni actualizaciones automáticas.

La [guía del ejemplo EC2](docs/ec2-example.es.md) muestra cómo organizar referencias y cobertura. Conserva los enlaces web completos fuera del paquete: ContentGuard sigue siendo obligatorio aunque una heurística de revisión solo produzca un aviso.
