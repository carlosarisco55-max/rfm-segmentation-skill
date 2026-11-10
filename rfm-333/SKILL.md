---
name: rfm-333
description: "Construye una segmentación RFM (Recencia, Frecuencia, Monto) de clientes a partir de un CSV o Excel, en versión 333 (puntuación 1-3 por eje, 27 cajones agrupados en 6 grupos con acción) y la explica en lenguaje de negocio. Evita los errores típicos: bandear con terciles automáticos sin mirar la curva, usar HOY() como fecha de corte, leer la media en vez de la mediana, ordenar segmentos por número de clientes en vez de por gasto total, y lanzar acciones sin grupo de control. Úsalo cuando alguien pida 'segmentación RFM', 'RFM 333', 'clasifica a mis clientes', 'quiénes son mis mejores clientes' o tenga una tabla con fecha de última compra, número de compras e importe gastado."
---

# RFM 333 — segmentación de clientes que se pueda defender en una reunión

RFM ordena a los clientes con tres preguntas que cualquier sistema de ventas ya tiene contestadas:

- **R · Recencia**: ¿cuánto hace que compró? (días desde la última compra hasta la fecha de corte)
- **F · Frecuencia**: ¿cuántas veces compró en el periodo? (nº de tickets/pedidos)
- **M · Monto**: ¿cuánto gastó en el periodo? (suma de importes, no el ticket medio)

En la versión **333** cada eje recibe 1, 2 o 3 (3 = mejor), y el código resultante va de `111` a `333`: 27 combinaciones ("cajones"). Nadie gestiona 27 campañas, así que se agrupan en 6 grupos con una acción cada uno.

El RFM es **descriptivo**: dice quién ha sido valioso y quién se está yendo. No predice qué comprará, no explica por qué compra así y no detecta afinidad de producto. Para eso hacen falta otros modelos (propensión, ciclo de recompra).

## Paso 0 — Antes de calcular nada, deja por escrito dos decisiones

1. **Periodo**: normalmente 12 meses cerrados. Los clientes con la última compra fuera del periodo quedan fuera del modelo (se tratan aparte como inactivos).
2. **Fecha de corte fija**: usa la fecha de la última compra registrada en la base (o un cierre de mes), **no `HOY()`**. Con `HOY()` el resultado cambia cada día y, si los datos tienen unos meses, puede que nadie cumpla el umbral de "reciente".

## Paso 1 — Identifica las columnas

Hacen falta, por cliente: identificador, fecha de última compra, nº de compras, gasto total. Si la tabla es de pedidos (una fila por ticket), agrega por cliente: fecha máxima, recuento de tickets, suma de importes. Si no está claro qué columna es cuál, pregunta antes de calcular.

## Paso 2 — Mira las tres curvas antes de poner cortes

Haz un histograma de cada variable (o pide media, mediana, mínimo, máximo y la distribución de compras). Casi siempre verás:

- **Frecuencia**: la mayoría compra una sola vez. Si el 60-70% tiene 1 compra, **los terciles automáticos no funcionan**: los dos cortes caen en 1, la banda F=2 queda vacía y un tercio de los cajones se queda sin clientes. Corta por negocio: 1 compra / 2 compras / 3 o más.
- **Monto**: asimetría a la derecha (muchos gastan poco, pocos gastan mucho). La media miente: compara siempre media y mediana. Si la media supera mucho a la mediana, avísalo.
- **Recencia**: corta por calendario de negocio (por ejemplo, cuatrimestres: ≤120 días / 121-243 / 244-365), no por percentiles.

Regla práctica para M: usa múltiplos del ticket medio (por ejemplo, <1 ticket / 1-2 tickets / ≥2 tickets). Así el corte significa algo para el negocio.

## Paso 3 — Comprueba que las variables no miden lo mismo

Calcula la correlación entre F y M. Si pasa de 0,7, las dos aportan casi la misma información (típico cuando el ticket es casi constante). No es un error, pero hay que decirlo: en esa base el valor depende sobre todo de cuántas veces compra el cliente. Lo habitual es que la recencia tenga correlación casi nula con F y M; es el eje que más información nueva aporta.

## Paso 4 — Puntúa y concatena

Con el script (sin dependencias, solo Python estándar):

```bash
python scripts/rfm_333.py --input clientes.csv \
  --id-col Id_Cliente --date-col Fecha_Ultima_Compra --date-format "%m/%d/%Y" \
  --frequency-col Compras --monetary-col Gasto \
  --r-cuts 120 243 --f-cuts 3 2 --m-cuts 70 35 \
  --window 365 --output rfm_resultado.csv
```

- `--r-cuts A B`: R=3 si días ≤ A; R=2 si ≤ B; si no, R=1.
- `--f-cuts A B` y `--m-cuts A B`: score 3 si valor ≥ A; 2 si ≥ B; si no, 1.
- `--cutoff AAAA-MM-DD` opcional; por defecto, la última fecha de la base.
- `--auto-terciles` calcula los cortes por terciles e imprime un aviso si alguna banda queda vacía (sirve para enseñar por qué no conviene).

El script imprime: media y mediana, la correlación F-M, el reparto de cada banda (clientes y gasto), la tabla de los 27 cajones ordenada por gasto total y los 6 grupos.

En Excel (columnas: A id, B fecha, C compras, D gasto; fecha de corte en `$Z$1`):

```
E2  =$Z$1-B2                                   días desde la última compra
F2  =SI(E2<=120;3;SI(E2<=243;2;1))             R
G2  =SI(C2>=3;3;SI(C2>=2;2;1))                 F
H2  =SI(D2>=70;3;SI(D2>=35;2;1))               M
I2  =F2&G2&H2                                  código RFM
```

(En Excel en inglés: `IF` y `,` en lugar de `SI` y `;`. Pon los umbrales en celdas aparte para poder cambiarlos sin tocar fórmulas.)

## Paso 5 — Agrupa los 27 cajones en 6 grupos (la recencia manda primero)

| Grupo | Cajones | Quiénes son | Acción |
|---|---|---|---|
| 1. Campeones | 333, 332, 323, 322 | Recientes, repiten, gasto medio/alto | Trato VIP, acceso anticipado. Sin descuento: comprarían igual |
| 2. Recientes de una compra | 313, 312, 311, 331, 321 | Compra reciente pero poca historia | Onboarding: conseguir la segunda compra |
| 3. Valiosos enfriándose | 233, 232, 223, 222 | Buenos clientes, 4-8 meses sin comprar | Recordatorio personalizado antes de que se vayan |
| 4. Ocasionales en pausa | 213, 212, 211, 231, 221 | Una compra hace 4-8 meses | Recordatorios baratos, campañas de temporada, up selling |
| 5. Valiosos en riesgo | 133, 132, 123, 122 | Buenos clientes, 8-12 meses sin comprar | Recuperación urgente con incentivo |
| 6. A punto de perderse | 113, 112, 111, 131, 121 | Una compra hace 8-12 meses | Solo la gran oferta del año. No gastes cupones personalizados |

Ajusta la asignación a tu negocio, pero mantén la lógica: un gasto alto con recencia baja es un cliente que **fue** bueno, no uno que lo sea.

## Paso 6 — Lee la tabla por gasto total, no por número de clientes

El valor de un cajón es clientes × frecuencia × ticket. Ordena la tabla de los 27 por **gasto total**: es habitual que el cajón que más factura no sea el `333`, sino uno de buenos clientes que se están enfriando (por ejemplo, `133`). Esa es la lectura que cambia el presupuesto.

## Paso 7 — Antes de actuar sobre un grupo, aparta un control

Cualquier acción (reactivación, cupón, onboarding) se mide contra un grupo de control del mismo segmento que no recibe nada (~10%, elegido al azar y guardado con fecha antes del envío). Sin control no se puede separar lo que compraron por la campaña de lo que habrían comprado igual. La venta incremental se calcula con dos escenarios sobre la misma audiencia:

```
orgánico   = audiencia × conversión_control × gasto_medio_control
con acción = audiencia × conversión_test    × gasto_medio_test
incremental = con acción − orgánico
```

Nunca restes directamente las ventas del grupo test menos las del control: los grupos tienen tamaños distintos y una parte de esas ventas iba a ocurrir de todos modos.

## Cómo presentar el resultado

1. Decisiones tomadas: periodo, fecha de corte, cortes de cada eje y por qué.
2. Media vs mediana del gasto y % de clientes por debajo de la media.
3. Reparto de bandas (clientes y % del gasto) y correlación F-M.
4. Tabla de los 27 cajones ordenada por gasto total.
5. Los 6 grupos con tamaño, gasto y acción.
6. Limitaciones: qué no puede decir el RFM (por qué compra, qué producto ofrecer, si volverá) y qué datos faltan (por ejemplo, fecha de alta para distinguir clientes nuevos de clientes que se apagan).

Recalcula cada trimestre con los mismos cortes y guarda el código de cada cliente: lo valioso es ver quién se mueve de cajón (un `333` que pasa a `233` es una alerta temprana).
