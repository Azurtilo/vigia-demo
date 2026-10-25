# Validar con evidencia

Puedes pedir a la IA que lea este archivo en el proyecto. Si copias el mensaje, reemplaza los campos entre <...>. Los nombres/IDs de ejemplo no son trabajo autorizado.

```text
Valida <carpeta de spec> contra spec, plan, tareas y código.
Esta fase autoriza comprobaciones en entorno aislado y actualización documental; no correcciones funcionales automáticas.

Revisa RF uno por uno; ejecuta pruebas pertinentes y registra resultados reales, incluyendo casos denegados y límites. Distingue fallos previos de nuevos.
Si hay interfaz interactiva, verifica navegador; si se modifican reportes/exportaciones, verifica el contenido y representación que corresponda.
No declares tests pasados si no se ejecutaron ni cobertura por encontrar cero tests.
Los no funcionales de CLAUDE.md (alerta de caída ≤ 10 s, inferencia < 100 ms por cuadro, disponibilidad ≥ 99,5 %, detección de caídas ≥ 90 % con falsos positivos ≤ 5 %, sin video a la nube) son objetivos del informe: decláralos cumplidos solo con medición registrada en validation.md (método, entorno/dispositivo, muestra y resultado). Sin medición, márcalos como no verificados. La disponibilidad es un objetivo de diseño no medido en el prototipo (D-060). Compara el resultado con la matriz HU/RT/RNF de docs/TRAZABILIDAD.md y actualízala.
Ejecuta las verificaciones de los componentes tocados con los comandos de AGENTS.md (web, edge, mobile); lo que dependa del dispositivo se comprueba en un Android físico o se declara no comprobado.
Crea/actualiza validation.md usando su plantilla, tareas, trazabilidad y estado. Señala qué no se pudo comprobar y por qué.
No marques mi aceptación funcional ni despliegues. Propón tareas documentadas para hallazgos que necesiten corrección.
```
