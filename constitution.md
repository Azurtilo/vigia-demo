# Constitución general de desarrollo

Versión 1.0 · 2026-09-20. Reutilizable en proyectos derivados de esta base.
Estos principios no contienen reglas de ningún negocio particular.

1. **Resolver una necesidad definida.** Implementar lo solicitado, con alcance y resultado verificable. Las ideas futuras se registran como propuestas; no se convierten automáticamente en trabajo.
2. **Especificar antes de programar.** Todo módulo o cambio funcional comienza por requisitos, plan y tareas. La primera entrega es documental; la implementación necesita una instrucción posterior explícita. Un documento propuesto no equivale a un acuerdo aprobado.
3. **Separar reglas generales y reglas del producto.** Esta constitución contiene principios; AGENTS y arquitectura contienen convenciones técnicas; cada spec contiene las reglas de su módulo. No trasladar datos, roles exclusivos o decisiones comerciales de otro proyecto.
4. **Conservar lo que ya funciona.** Inspeccionar código, instrucciones y cambios locales antes de editar. Reutilizar los componentes de la base; justificar cambios de arquitectura o dependencias dentro del alcance solicitado.
5. **Validar donde corresponde.** La interfaz ayuda al usuario, pero integridad y permisos se verifican en servidor. Definir tipos, precisión, relaciones, límites, duplicados y transacciones según los datos de cada módulo.
6. **Acceso explícito y mínimo necesario.** Definir quién puede ver y modificar cada dato. Respetar la política real de la base y documentar excepciones aprobadas. Una URL oculta o un botón ausente no constituyen control de acceso.
7. **Trazabilidad proporcional.** Determinar qué operaciones requieren autor, fecha, motivo e historial según el módulo. Si se exige auditoría, no reemplazarla por mensajes de pantalla ni afirmar garantías que no existen.
8. **Interfaz para personas.** Español claro por defecto, etiquetas comprensibles, acciones coherentes, errores útiles, navegación por teclado y adaptación a móvil. Ajustar la interfaz al usuario real sin imponer vocabulario de otro dominio.
9. **Datos protegidos.** No incluir secretos ni bases reales en prompts, pruebas, commits o entregas de código. No migrar, desplegar ni modificar producción por el solo hecho de poder acceder a ella.
10. **Pruebas y evidencia.** Un cambio terminado identifica requisitos, archivos y comprobaciones. No declarar aprobada una prueba no ejecutada. Una suite verde no prueba por sí sola capacidad, privacidad ni aceptación del usuario; cero tests no equivale a cobertura.
11. **Preguntar solo lo necesario.** No hacer entrevistas automáticas. Reutilizar decisiones documentadas; preguntar por vacíos que cambien permisos, datos, dinero, reglas de negocio o alcance. Registrar supuestos técnicos reversibles de bajo riesgo.
12. **Cambios reversibles y acotados.** Evitar modificaciones ajenas a la tarea. Una migración debe explicar compatibilidad, respaldo y recuperación. Documentar límites conocidos, mantener decisiones y dejar un punto de reanudación.

## Cambios de estos principios

Un requisito de un cliente se escribe normalmente en su spec, no aquí. Para modificar un principio, proponer motivo e impacto, obtener una decisión explícita y registrarla en [docs/DECISIONES.md](docs/DECISIONES.md), incrementando esta versión. No cambiar reglas para eludir una restricción ni sustituir instrucciones superiores del entorno.
