# Skills de IRMind

Repositorio fuente de las skills forenses de datos de [IRMind](https://github.com/ns2switch/irmind).

- `core/` contiene los paquetes incluidos en cada release de IRMind. IRMind compila una copia local fijada y nunca descarga skills al compilar.
- `catalog/` contiene paquetes opcionales de la comunidad para `/skills install catalog:<nombre>`. Los nombres del núcleo nunca son entradas instalables del catálogo.
- Los episodios sintéticos y las respuestas exclusivas del evaluador quedan fuera de los paquetes instalables.

Una skill no concede permisos. Siguen mandando la política, el alcance del caso, el techo de la organización, ContentGuard y las aprobaciones del analista. Los paquetes no contienen código ejecutable.

No se publican releases de producción del catálogo hasta disponer de su clave de firma. Los ensayos usan solo claves sintéticas.

[English](README.md)

Licencia MIT OR Apache-2.0.
