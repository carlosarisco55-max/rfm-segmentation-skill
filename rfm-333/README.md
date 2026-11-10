# rfm-333 — variante de 27 cajones (puntuación 1-3)

Segunda variante del mismo método RFM del repositorio raíz, pensada para cuando se quiere trabajar con un modelo más simple de explicar en comité: 3 niveles por eje (27 combinaciones) en vez de 5 (125 celdas), agrupados en 6 segmentos con una acción cada uno.

Incluye avisos activos sobre dos errores frecuentes al hacer RFM a mano: bandear con terciles automáticos sin mirar la forma de la curva (puede dejar una banda vacía) y confundir una variable que mide lo mismo que otra (correlación F-M alta).

## Instalar como skill de Claude

**Claude Code:** copia esta carpeta (`rfm-333/`) dentro de `~/.claude/skills/` (Windows: `C:\Users\<tu usuario>\.claude\skills\`). Reinicia la sesión.

**Claude.ai (web/escritorio):** comprime la carpeta `rfm-333` en un `.zip` y súbela en Ajustes → Capacidades → Skills.

## Usar como script de línea de comandos

Solo necesita Python 3.10+, sin librerías externas:

```bash
python scripts/rfm_333.py --input ejemplo/clientes_ejemplo.csv \
  --id-col Id_Cliente --date-col Fecha_Ultima_Compra \
  --frequency-col Compras --monetary-col Gasto
```

Prueba también `--auto-terciles` para ver por qué cortar por terciles automáticos suele romper la banda de frecuencia cuando la mayoría de clientes solo ha comprado una vez.

`ejemplo/clientes_ejemplo.csv` son 500 clientes inventados para probar.

Ver `SKILL.md` para el método completo (7 pasos), las fórmulas de Excel equivalentes y cómo presentar el resultado en una reunión.
