# Especificar el resultado

Puedes pedir a la IA que lea este archivo en el proyecto. Si copias el mensaje, reemplaza los campos entre <...>. Los nombres/IDs de ejemplo no son trabajo autorizado.

```text
Nombre del módulo: <NombreAPP>.
Requerimiento: <texto y ejemplos>.

Fase DOCUMENTAR. Lee reglas, estado, decisiones y código relacionado.
Usa specs/_templates/spec.md para redactar qué debe hacer: actores, alcance/exclusiones, datos, RF identificados, permisos por acción, casos límite, criterios observables y regresiones a preservar.
Vincula cada RF a las historias HU-01..HU-07, requerimientos técnicos RT-01..RT-03 y no funcionales de CLAUDE.md que cubre; si un RF no corresponde a ninguno, decláralo como alcance adicional.
Indica qué componentes toca (web/, mobile/, edge/) y los permisos por rol real de VIGIA (cargos del portal y dueño del paciente; familiar y cuidador según los vínculos de D-050 una vez implementados), con cualquier excepción explícitamente solicitada; no copies la política de otro proyecto.
Respeta las restricciones vigentes: sin video a la nube (solo metadatos), Android primero, español es-CL.
Para módulo nuevo usa siguiente número libre; un ajuste pequeño actualiza su spec.
Conserva lo que esté claro. Si falta una decisión crítica, identifica la parte afectada y pregunta solo eso. No inventes aprobación, requisitos comerciales ni funcionalidades futuras.
Actualiza el índice y estado pertinente. No generes código. Entrega la spec para revisión o para continuar con el plan si esa fase documental también está pedida.
```
