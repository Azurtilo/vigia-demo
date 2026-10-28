# Diseño visual (aprobado 2026-10-25)

Propuesta visual y pantallas de referencia: lienzo de diseño "VIGIA — propuesta visual app móvil" (fila "Propuesta 2", APROBADA).

## Logo

- Archivo original: `mobile/assets/branding/07_icono_app.svg` (no se modifica).
- Para el ícono de la app se derivarán dos versiones: cuadrada sin esquinas redondeadas (iOS) y con las figuras reducidas al área segura del 66 % central (Android adaptativo).

## Paleta (Propuesta 2: tonos claros del logo)

Regla: los tonos claros son fondos y superficies **siempre con texto oscuro**; botones y textos destacados usan el tono oscuro del mismo color. Todas las combinaciones de texto superan 4,5:1 (WCAG AA), medidas.

| Token | Color | Uso | Contraste |
|---|---|---|---|
| `background` | `#F4F0FC` | Fondo de pantallas | tinta 13,0:1 |
| `surface` | `#FFFFFF` | Tarjetas, hojas | — |
| `primary` | `#5E4BA3` | Botones, enlaces, navegación activa | blanco 7,0:1 |
| `primaryPressed` | `#4A3A86` | Botón presionado | — |
| `primarySoft` | `#E9E2F8` | Chips "pendiente", selección, encabezados | primary 5,6:1 |
| `lavender` | `#C6B2EC` | Destacados, IA, Premium | tinta 7,6:1 |
| `mint` | `#A9E6CC` | Completado | `mintInk` 4,5:1 |
| `mintInk` | `#1E6B52` | Texto sobre menta | — |
| `sky` | `#DCEEF8` | Ficha del paciente, consejos | tinta |
| `rose` | `#F7E1EC` / texto `#7A2E50` | Personas, recordatorios | — |
| `ink` | `#2B2541` | Texto principal | 13,0:1 |
| `inkMuted` | `#5A5370` | Texto secundario | 6,4:1 |
| `outline` | `#8F86AE` | Borde de campos (no texto) | 3,4:1 |
| `risk` / `riskSoft` | `#B3261E` / `#FBE4E2` | Posibles eventos de riesgo | 5,4:1 |
| `attention` / `attentionSoft` | `#7A4F00` / `#FCEBC8` | Retrasado, pendiente vencido | 6,1:1 |

El azul `#4054A8` y los demás colores de la paleta original dejan de usarse como color principal (decisión del usuario, ADR 027).

## Tipografía

Nunito (400, 600, 700, 800). Cuerpo 16, mínimo 14. Se respeta el tamaño de letra del sistema.

## Reglas de interfaz

- Barra inferior de 4 secciones: Hoy, Pacientes, Alertas, Cuenta. El paciente activo se elige arriba.
- Áreas táctiles de al menos 48 px.
- Los estados nunca se indican solo con color: texto + ícono.
- Lo que la persona no puede hacer (permisos) se oculta; lo que su plan no incluye se muestra con la explicación.
