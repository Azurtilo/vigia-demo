# Revisión QA independiente

Puedes pedir a la IA que lea este archivo en el proyecto. Si copias el mensaje, reemplaza los campos entre <...>. Los nombres/IDs de ejemplo no son trabajo autorizado.

```text
Revisión QA de VIGIA. Alcance: <proyecto completo, spec NNN o rama>.
Fase de solo lectura: no modifiques código, tests, migraciones, dependencias, specs ni configuración. El único archivo nuevo permitido es docs/QA_<AAAA-MM-DD>.md (si existe, agrega _2; no sobrescribas informes anteriores).

Lee CLAUDE.md, AGENTS.md, constitution.md, docs/ESTADO_PROYECTO.md, docs/TRAZABILIDAD.md, specs/README.md y las specs del alcance. Registra rama, commit y git status al inicio.
Ejecuta las suites con los comandos de AGENTS.md (web, edge, mobile) y registra comando, salida y conteos reales; lo que no se pueda ejecutar, con motivo.
Contrasta cada HU-01..07, RT-01..03 y no funcional con la matriz de docs/TRAZABILIDAD.md: implementación, pruebas, evidencia en validation.md y estado (Cubierto / Parcial / Sin implementar / Sin evidencia). Los objetivos numéricos no se declaran cumplidos sin medición registrada.
Revisa seguridad y privacidad: datos de salud (Ley 21.719 y 20.584), ningún cuadro ni imagen fuera del nodo, secretos versionados, permisos por endpoint con pruebas de acceso denegado, CSRF, validación de entrada y configuración de producción. Clasifica con OWASP Top 10 cuando aplique.
Revisa calidad: duplicación relevante, funciones muy largas en lógica crítica y rutas críticas sin pruebas.
Informe: resumen, suites, matriz, hallazgos ordenados Crítico → Alto → Medio → Bajo con ID QA-<fecha>-NN, archivo y línea, evidencia, certeza, impacto y corrección sugerida; limitaciones y siguientes pasos.
No repitas como nuevos los hallazgos ya corregidos o registrados en DECISIONES.md; indica su estado. No presentes el informe como certificación ni aceptación funcional.
```

En Claude Code, el agente `qa-vigia` (`.claude/agents/qa-vigia.md`) aplica esta misma guía con más detalle.
