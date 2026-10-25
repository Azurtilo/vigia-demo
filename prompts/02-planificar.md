# Proponer integración técnica

Puedes pedir a la IA que lea este archivo en el proyecto. Si copias el mensaje, reemplaza los campos entre <...>. Los nombres/IDs de ejemplo no son trabajo autorizado.

```text
Spec a trabajar: <ruta>/spec.md.
Fase DOCUMENTAR, no implementación.

Lee spec, reglas de la base y archivos existentes afectados.
Crea/actualiza plan.md con la plantilla: arquitectura propuesta, app nueva o ampliación, archivos, modelos/relaciones, validación, permisos, rutas, plantillas, transacciones/migraciones si aplican y pruebas por RF.
Separa el impacto por componente: web/ (Django), mobile/ (Flutter, lib/features/*, plugin vigia_pose) y edge/ (nodo Python MediaPipe). Si cambia la comunicación entre ellos, describe el cambio de contrato API (endpoints, payloads, autenticación, compatibilidad con versiones instaladas) y actualiza o propone la referencia de contrato correspondiente.
Distingue rutas existentes de archivos propuestos. No inventes una configuración de pruebas que la base no trae; usa las suites existentes de cada componente. Reutiliza autenticación, usuarios, tema y navegación.
Registra riesgos, alternativas relevantes y decisiones pendientes. Actualiza docs solo si la información lo exige, marcando propuestas como tales.
No escribas código ni ejecutes startapp, migraciones o compilaciones. Entrega el plan y continúa solo con tareas documentales si se solicitaron.
```
