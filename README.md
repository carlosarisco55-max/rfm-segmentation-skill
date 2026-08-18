# RFM Customer Segmentation

Herramienta en Python que clasifica a los clientes de cualquier negocio en 6 segmentos accionables (Champions, Clientes fieles, En riesgo, Perdidos...) usando el método **RFM** (Recencia, Frecuencia, Monetario) — una de las técnicas de segmentación más usadas en marketing/CRM.

Nacida como generalización del análisis hecho en [`marketing-campaign-customer-personality-analysis`](https://github.com/carlosarisco55-max/marketing-campaign-customer-personality-analysis): en vez de dejar ese cálculo atado a un solo dataset, lo convertí en una herramienta reutilizable para cualquier tabla de clientes o transacciones.

## Qué resuelve

Dado un CSV de clientes, responde: **¿quiénes son mis mejores clientes, a quiénes tengo que reactivar antes de perderlos, y en quiénes ya no merece la pena invertir presupuesto de marketing?**

## Cómo funciona (resumen)

1. Para cada cliente, calcula 3 métricas:
   - **Recencia** — días desde su última compra
   - **Frecuencia** — número de compras/pedidos
   - **Monetario** — gasto total
2. Puntúa cada métrica del 1 al 5 **de forma relativa a la propia base de clientes** (el 20% que más gasta saca un 5, el 20% que menos gasta saca un 1 — no hay umbrales fijos inventados)
3. Combina las tres puntuaciones con una tabla de reglas para asignar un segmento:

| Segmento | Significado |
|---|---|
| **Champions** | Compra mucho, gasta mucho, y lo hizo hace muy poco |
| **Clientes fieles** | Sólido en las tres métricas, sin ser extremo |
| **Nuevos / prometedores** | Compró hace poco, pero aún con poco historial |
| **En riesgo** | Antes valía mucho, hace tiempo que no vuelve — prioridad de reactivación |
| **Perdidos** | Bajo en todo — no vale la pena invertir en recuperarlos |
| **Necesitan atención** | Casos intermedios, a vigilar |

## Uso

Dos modos según cómo tengas los datos:

```bash
# Si ya tienes una fila por cliente con recencia/frecuencia/gasto calculados
python scripts/rfm_generic.py --input clientes.csv --mode aggregated \
  --id-col ID --recency-col Recency --frequency-col Total_Purchases \
  --monetary-col Total_Spend --output segmentos.csv

# Si tienes una fila por pedido/transacción (el script agrega solo)
python scripts/rfm_generic.py --input pedidos.csv --mode transactions \
  --id-col customer_id --date-col order_date --amount-col amount \
  --output segmentos.csv
```

Solo librería estándar de Python (`csv`, `statistics`, `datetime`) — sin pandas ni dependencias que instalar.

## Output

Un CSV con un segmento por cliente, más un resumen en consola: tamaño de cada segmento, valor medio, y recomendación de negocio para cada uno (a quién priorizar, a quién reactivar, en quién no gastar presupuesto).

## Ejemplo real

Aplicado sobre el dataset de [Customer Personality Analysis](https://www.kaggle.com/datasets/rodsaldanha/arketing-campaign) (2.236 clientes, ver caso completo en [`marketing-campaign-customer-personality-analysis/rfm`](https://github.com/carlosarisco55-max/marketing-campaign-customer-personality-analysis/tree/main/rfm)):

```
En riesgo (antes valiosos): 326 clientes (14.6%), valor medio 1.285€
Champions:                  320 clientes (14.3%), valor medio 1.247€
Clientes fieles:            463 clientes (20.7%), valor medio   778€
Necesitan atención:         415 clientes (18.6%), valor medio   305€
Nuevos / prometedores:      379 clientes (16.9%), valor medio    73€
Perdidos:                   333 clientes (14.9%), valor medio    67€
```

Insight accionable: los "en riesgo" gastaban casi lo mismo que los Champions — son el objetivo prioritario de una campaña de reactivación antes de darlos por perdidos.

## Nota técnica

Este proyecto está empaquetado también como **skill de [Claude Code](https://claude.com/claude-code)** (`SKILL.md` en la raíz), lo que permite invocarlo desde una conversación con el agente simplemente pasándole una tabla de clientes — pero el script (`scripts/rfm_generic.py`) funciona igual de bien como herramienta de línea de comandos independiente, sin necesidad de Claude Code.

## Autor

**Carlos García-Arisco**
Máster en Marketing Digital e IA — INESDI Business Tech School (Grupo Planeta)
[LinkedIn](https://www.linkedin.com/in/carlos-garcia-arisco-vilchez) · [GitHub](https://github.com/carlosarisco55-max)
