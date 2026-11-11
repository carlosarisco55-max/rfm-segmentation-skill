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

## Ejemplo en Excel (descargable)

[`ejemplo/RFM_333_ejemplo.xlsx`](ejemplo/RFM_333_ejemplo.xlsx) es el mismo método en un libro de Excel con fórmulas vivas sobre esos 500 clientes inventados: parámetros editables (fecha de corte, ventana y cortes de R, F y M), los 27 cajones, los 6 grupos con su acción y una hoja de lecturas previas (clientes de una compra, terciles automáticos, media frente a mediana y correlación F-M). Da exactamente las mismas cifras que `rfm_333.py`. Se genera con `python ejemplo/build_excel_ejemplo.py ejemplo/clientes_ejemplo.csv ejemplo/RFM_333_ejemplo.xlsx` (requiere `openpyxl`).

Caso de estudio completo, con el ejercicio original de 10.000 clientes y sus hallazgos: [carlosarisco55-max.github.io/casos/segmentacion-rfm](https://carlosarisco55-max.github.io/casos/segmentacion-rfm/)

Ver `SKILL.md` para el método completo (7 pasos), las fórmulas de Excel equivalentes y cómo presentar el resultado en una reunión.
