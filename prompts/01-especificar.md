# Especificar el resultado

Puedes pedir a la IA que lea este archivo en el proyecto. Si copias el mensaje, reemplaza los campos entre <...>. Los nombres/IDs de ejemplo no son trabajo autorizado.

```text
Nombre del módulo: <NombreAPP>.
Requerimiento: <texto y ejemplos>.

Fase DOCUMENTAR. Lee reglas, estado, decisiones y código relacionado.
Usa specs/_templates/spec.md para redactar qué debe hacer: actores, alcance/exclusiones, datos, RF identificados, permisos por acción, casos límite, criterios observables y regresiones a preservar.
Incluye la política de superusuario real de esta base y cualquier excepción explícitamente solicitada; no copies la de otro proyecto.
Para módulo nuevo usa siguiente número libre; un ajuste pequeño actualiza su spec.
Conserva lo que esté claro. Si falta una decisión crítica, identifica la parte afectada y pregunta solo eso. No inventes aprobación, requisitos comerciales ni funcionalidades futuras.
Actualiza el índice y estado pertinente. No generes código. Entrega la spec para revisión o para continuar con el plan si esa fase documental también está pedida.
```
