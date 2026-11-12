---
name: rfm-segmentation
description: "Calcula segmentacion RFM (Recencia, Frecuencia, Monetario) a partir de cualquier tabla de clientes o transacciones que el usuario proporcione (CSV/Excel), y explica el resultado en lenguaje llano. Tambien puede anadir la segmentacion como pagina/medida nueva dentro de un proyecto Power BI (.pbip) ya existente. Usa este skill cuando el usuario pida 'segmentacion RFM', 'calcula el RFM de esta tabla', 'clasifica estos clientes', 'quien son mis mejores/peores clientes', o pase una tabla con fecha de compra / numero de pedidos / importe gastado."
---

# RFM Segmentation

Segmenta clientes por Recencia (dias desde la ultima compra), Frecuencia (nº de compras/pedidos) y Monetario (gasto total), usando puntuaciones por quintiles (1-5) y una regla de 6 segmentos. Metodo desarrollado y validado en `carlosarisco55-max/marketing-campaign-customer-personality-analysis/rfm/`.

## Paso 1 — identifica las columnas en la tabla del usuario

Necesitas mapear las columnas reales del usuario a uno de estos dos modos:

- **`aggregated`** — la tabla ya tiene una fila por cliente, con columnas de recencia (dias), frecuencia (nº compras) y monetario (importe total). Es el caso mas comun cuando el usuario ya tiene un dataset limpio tipo el de `marketing_campaign`.
- **`transactions`** — la tabla tiene una fila por pedido/transaccion (id de cliente, fecha, importe). El script agrega automaticamente por cliente antes de puntuar.

Si no esta claro cual es el caso o como se llaman las columnas relevantes, pregunta al usuario antes de ejecutar nada — no adivines nombres de columna.

## Paso 2 — ejecuta el script

```bash
# Modo aggregated
python scripts/rfm_generic.py --input <tabla.csv> --mode aggregated \
  --id-col <col_id> --recency-col <col_recencia> \
  --frequency-col <col_frecuencia> --monetary-col <col_monetario> \
  --output rfm_segments.csv

# Modo transactions
python scripts/rfm_generic.py --input <tabla.csv> --mode transactions \
  --id-col <col_id> --date-col <col_fecha> --amount-col <col_importe> \
  --date-format "%Y-%m-%d" \
  --output rfm_segments.csv
```

Solo depende de la libreria estandar de Python (`csv`, `statistics`, `datetime`) — no requiere pandas ni instalar nada.

Si el input es `.xlsx` en vez de `.csv`, convierte primero a CSV (o adapta el script con `openpyxl` si el usuario ya lo tiene instalado) antes de ejecutar.

## Paso 3 — explica el resultado, no solo lo entregues

El usuario ya ha dejado claro en conversaciones anteriores que quiere entender el porque, no solo el output. Al presentar resultados:

1. Explica que las puntuaciones 1-5 son **relativas a esa tabla de clientes** (quintiles: el 20% que mas gasta/compra/compro mas reciente saca un 5), no umbrales fijos universales.
2. Recuerda que en Recencia la puntuacion se **invierte** (menos dias = mejor = puntuacion mas alta).
3. Explica las 6 reglas de segmentacion en el orden en que se evaluan (la primera que se cumple gana):

| # | Condicion | Segmento | Significado |
|---|---|---|---|
| 1 | R>=4 y FM>=4 | Champions | Compro muy reciente y es de los que mas compran/gastan |
| 2 | R>=3 y FM>=3 | Clientes fieles | Ni extremo ni bajo en ninguna de las dos — solido y constante |
| 3 | R>=4 y FM<3 | Nuevos / prometedores | Reciente pero aun con poco historial de valor |
| 4 | R<3 y FM>=4 | En riesgo (antes valiosos) | Valia mucho, hace tiempo que no vuelve |
| 5 | R<=2 y FM<=2 | Perdidos | Bajo en ambas — casi seguro se ha ido |
| 6 | (ninguna anterior) | Necesitan atencion | Combinaciones intermedias sin encajar claramente |

Deja claro que esta tabla de reglas es un **diseño simplificado**, no un estandar oficial unico — hay versiones mas complejas (rejilla 5x5, hasta 11 segmentos) usadas por herramientas de CRM, pero esta version de 6 segmentos es deliberadamente mas facil de explicar y defender.

4. Cierra siempre con un apartado tipo "so what": a que segmento priorizar (Champions), a cual reactivar con campana (En riesgo), y en cual no gastar presupuesto (Perdidos) — el usuario viene de un perfil de marketing/growth y valora la recomendacion accionable, no solo la tabla de numeros.

## Paso 4 (opcional) — anadirlo a un proyecto Power BI (.pbip)

Se honesto sobre el alcance real de esto: **no existe un comando que "genere un .pbip desde cero" de forma fiable** — un proyecto Power BI Project es una carpeta con TMDL (modelo semantico) + JSON (paginas/visuales), y anadir una pagina nueva a un `.pbip` ya existente se hace editando esos archivos de texto directamente, igual que se hizo en `marketing-campaign-customer-personality-analysis/powerbi/PersonalityAnalysis.pbip` (4 paginas construidas por codigo, no a golpe de raton).

Si el usuario pide esto:

1. Confirma que existe ya un proyecto `.pbip` al que anadir la pagina (o si quiere uno nuevo desde cero, avisa que eso normalmente se hace mejor abriendo Power BI Desktop una vez para el scaffold inicial, y luego editando el `.pbip` resultante como texto).
2. Genera el CSV de segmentos con este skill primero.
3. Anade la tabla de segmentos al modelo semantico (TMDL) como nueva tabla o medida calculada.
4. Crea una pagina nueva (JSON) con: distribucion de clientes por segmento (barras), valor medio por segmento, y una tabla con los top N "Champions" y "En riesgo".
5. Recuerda al usuario cerrar Power BI Desktop del todo antes de editar los archivos por fuera y volver a abrirlo — si no, Desktop sobrescribe los cambios externos con su version en memoria (leccion ya aprendida en ese mismo proyecto).

No prometas generar visuales complejos con un solo comando — es un trabajo de edicion de varios archivos, comunicalo asi.

## Siguiente paso

- `ficha-cliente`: junta esta segmentación con las demás (ciclo de vida, RFM, patrón de cesta, propensión y control) en una fila por cliente con qué, cuándo, palanca de comportamiento y prioridad. Lee el CSV de salida tal cual.
- `medicion-incremental`: aparta el grupo de control ANTES de activar ningún segmento y mide la venta incremental real.
