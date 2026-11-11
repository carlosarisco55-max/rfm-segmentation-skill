"""Construye un libro de Excel RFM 333 con fórmulas vivas a partir de un CSV de clientes.

Uso: python build_excel_ejemplo.py clientes_ejemplo.csv RFM_333_ejemplo.xlsx
Columnas del CSV: Id_Cliente, Fecha_Ultima_Compra (AAAA-MM-DD), Compras, Gasto.
Requiere openpyxl (solo para generar el Excel; el script rfm_333.py no lo necesita).
"""
import csv
import sys
from datetime import datetime

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

SRC, OUT = sys.argv[1], sys.argv[2]
with open(SRC, encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))
N = len(rows)
LAST = N + 1

NAVY = "1F3A68"
H_FILL, H_FONT = PatternFill("solid", fgColor=NAVY), Font(bold=True, color="FFFFFF")
YELLOW = PatternFill("solid", fgColor="FFF2CC")
NOTE_FILL = PatternFill("solid", fgColor="EEF3FA")
KEY_FILL = PatternFill("solid", fgColor="E2EFDA")
WARN_FILL = PatternFill("solid", fgColor="FCE4D6")
TITLE, SUB = Font(bold=True, size=14, color=NAVY), Font(bold=True, size=11, color=NAVY)
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
thin = Side(style="thin", color="BFBFBF")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
GROUP_COLORS = ["C6E0B4", "E2EFDA", "FFE699", "FFF2CC", "F8CBAD", "D9D9D9"]

GROUPS = [
    ("1. Campeones", "333 332 323 322", "Compraron hace ≤4 meses, repiten y gastan medio/alto.",
     "VIP: acceso anticipado y reconocimiento. Sin descuento: comprarían igual."),
    ("2. Recientes de una compra", "313 312 311 331 321", "Compra reciente pero (casi siempre) una sola.",
     "Acogida: conseguir la 2ª compra. Sin descuento."),
    ("3. Valiosos enfriándose", "233 232 223 222", "Recurrentes de valor que llevan 4-8 meses sin comprar.",
     "Reactivación temprana: recordatorio personalizado antes de que se vayan."),
    ("4. Ocasionales en pausa", "213 212 211 231 221", "Una compra hace 4-8 meses.",
     "Recordatorios de bajo coste y campañas estacionales. Up selling."),
    ("5. Valiosos en riesgo", "133 132 123 122", "Recurrentes de valor que llevan 8-12 meses sin comprar.",
     "Reactivación URGENTE con incentivo, y con grupo de control para medir la venta incremental."),
    ("6. A punto de perderse", "113 112 111 131 121", "Una compra hace 8-12 meses.",
     "Solo la oferta grande del año (Black Friday / liquidación). Un cupón personalizado aquí es tirar margen."),
]
CODE_TO_GROUP = {c: g[0] for g in GROUPS for c in g[1].split()}

wb = Workbook()


def title(ws, text, explanation, cols):
    ws["A1"], ws["A1"].font = text, TITLE
    ws["A2"] = explanation
    ws["A2"].alignment, ws["A2"].fill = WRAP, NOTE_FILL
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=cols)
    ws.row_dimensions[2].height = 15 * max(2, len(explanation) // 120 + 1)


def header(ws, row, labels):
    for i, lab in enumerate(labels, start=1):
        c = ws.cell(row=row, column=i, value=lab)
        c.fill, c.font, c.alignment, c.border = H_FILL, H_FONT, CENTER, BOX


def box(ws, r1, r2, c1, c2):
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            ws.cell(row=r, column=c).border = BOX
            ws.cell(row=r, column=c).alignment = WRAP


def widths(ws, w):
    for k, v in w.items():
        ws.column_dimensions[k].width = v


# ------------------------------------------------------------------ Parametros
P = wb.active
P.title = "Parametros"
title(P, "Parámetros del RFM 333 (celdas amarillas = decisiones editables)",
      "Cada eje se puntúa de 1 a 3 con cortes de NEGOCIO, no con terciles automáticos (la hoja Lecturas enseña por qué). "
      "Si cambias un corte, se recalculan los 27 cajones y los 6 grupos.", 5)
header(P, 4, ["Parámetro", "Valor", "Valor 2", "Regla", "Por qué"])
DM = f"Datos_Clientes!$D$2:$D${LAST}"
DC = f"Datos_Clientes!$C$2:$C${LAST}"
DG = f"Datos_Clientes!$G$2:$G${LAST}"
prm = [
    ("Fecha de corte", f"=MAX(Datos_Clientes!B2:B{LAST})", None, "",
     "La última compra registrada. NUNCA HOY(): con HOY() el resultado cambia cada día que abres el archivo."),
    ("Ventana (días)", 365, None, "", "12 meses. Quien lleva más sin comprar queda fuera del RFM (es inactivo, otro tratamiento)."),
    ("Ticket medio (en ventana)", f'=SUMIFS({DM},{DG},"Sí")/SUMIFS({DC},{DG},"Sí")', None, "Gasto ÷ compras",
     "Se usa para cortar el gasto en unidades que significan algo: tickets."),
    ("R (días): umbral score 3 / score 2", 120, 243, "3 si ≤ valor; 2 si ≤ valor 2; 1 resto", "Cuatrimestres: 0-4 meses / 4-8 / 8-12."),
    ("F (compras): umbral score 3 / score 2", 3, 2, "3 si ≥ valor; 2 si ≥ valor 2; 1 resto", "1 compra / 2 compras / 3 o más."),
    ("M (gasto): umbral score 3 / score 2", "=2*B7", "=B7", "3 si ≥ valor; 2 si ≥ valor 2; 1 resto", "Menos de 1 ticket / 1-2 tickets / 2 o más."),
]
for i, (k, v, v2, regla, why) in enumerate(prm, start=5):
    P.cell(row=i, column=1, value=k)
    P.cell(row=i, column=2, value=v).fill = YELLOW
    if v2 is not None:
        P.cell(row=i, column=3, value=v2).fill = YELLOW
    P.cell(row=i, column=4, value=regla)
    P.cell(row=i, column=5, value=why)
P["B5"].number_format = "dd/mm/yyyy"
for c in ("B7", "B10", "C10"):
    P[c].number_format = "0.00"
box(P, 5, 10, 1, 5)
widths(P, {"A": 38, "B": 13, "C": 11, "D": 32, "E": 80})

# ------------------------------------------------------------------ Grupos (mapping needed by Datos)
G = wb.create_sheet("Grupos")

# ------------------------------------------------------------------ Datos_Clientes
D = wb.create_sheet("Datos_Clientes", 1)
header(D, 1, ["Id_Cliente", "Fecha_Ultima_Compra", "Compras", "Gasto", "Dias_Desde_Ultima", "R_Score",
              "En_Ventana", "F_Score", "M_Score", "Codigo_RFM", "Grupo", "Compras_ventana", "Gasto_ventana"])
for i, r in enumerate(rows, start=2):
    D.cell(row=i, column=1, value=r["Id_Cliente"])
    D.cell(row=i, column=2, value=datetime.strptime(r["Fecha_Ultima_Compra"], "%Y-%m-%d")).number_format = "dd/mm/yyyy"
    D.cell(row=i, column=3, value=int(r["Compras"]))
    D.cell(row=i, column=4, value=float(r["Gasto"])).number_format = "0.00"
    D.cell(row=i, column=5, value=f"=Parametros!$B$5-B{i}")
    D.cell(row=i, column=6, value=f'=IF(G{i}="No","",IF(E{i}<=Parametros!$B$8,3,IF(E{i}<=Parametros!$C$8,2,1)))')
    D.cell(row=i, column=7, value=f'=IF(AND(E{i}>=0,E{i}<=Parametros!$B$6),"Sí","No")')
    D.cell(row=i, column=8, value=f'=IF(G{i}="No","",IF(C{i}>=Parametros!$B$9,3,IF(C{i}>=Parametros!$C$9,2,1)))')
    D.cell(row=i, column=9, value=f'=IF(G{i}="No","",IF(D{i}>=Parametros!$B$10,3,IF(D{i}>=Parametros!$C$10,2,1)))')
    D.cell(row=i, column=10, value=f'=IF(G{i}="No","Fuera",F{i}&H{i}&I{i})')
    D.cell(row=i, column=11, value=f'=IFERROR(VLOOKUP(J{i},Grupos!$K$5:$L$31,2,FALSE),"Fuera de ventana")')
    D.cell(row=i, column=12, value=f'=IF(G{i}="Sí",C{i},"")')
    D.cell(row=i, column=13, value=f'=IF(G{i}="Sí",D{i},"")')
D.freeze_panes = "B2"
D.auto_filter.ref = f"A1:M{LAST}"
widths(D, {"A": 13, "B": 13, "C": 9, "D": 10, "E": 11, "F": 9, "G": 11, "H": 9, "I": 9, "J": 11, "K": 27, "L": 11, "M": 11})
for idx, g in enumerate(GROUPS):
    D.conditional_formatting.add(f"K2:K{LAST}", FormulaRule(formula=[f'$K2="{g[0]}"'], fill=PatternFill("solid", fgColor=GROUP_COLORS[idx])))
DK = f"Datos_Clientes!$K$2:$K${LAST}"
DJ = f"Datos_Clientes!$J$2:$J${LAST}"
DL = f"Datos_Clientes!$L$2:$L${LAST}"
DMV = f"Datos_Clientes!$M$2:$M${LAST}"

# ------------------------------------------------------------------ Grupos content
title(G, "Los 27 cajones agrupados en 6 grupos de trabajo",
      "Nadie lanza 27 campañas. La recencia manda primero: un cliente de gasto alto que lleva 8-12 meses sin volver "
      "no es un campeón, es un valioso en riesgo. Ordena siempre por GASTO TOTAL, no por número de clientes.", 9)
header(G, 4, ["Grupo", "Cajones", "Quiénes son", "Acción", "Clientes", "% clientes", "Gasto total", "% gasto", "Gasto medio/cliente"])
for i, (g, codes, who, act) in enumerate(GROUPS, start=5):
    for j, v in enumerate((g, codes.replace(" ", ", "), who, act), start=1):
        G.cell(row=i, column=j, value=v)
    G.cell(row=i, column=1).fill = PatternFill("solid", fgColor=GROUP_COLORS[i - 5])
    G.cell(row=i, column=5, value=f"=COUNTIF({DK},A{i})")
    G.cell(row=i, column=6, value=f"=E{i}/SUM($E$5:$E$10)").number_format = "0.0%"
    G.cell(row=i, column=7, value=f"=SUMIFS(Datos_Clientes!$D$2:$D${LAST},{DK},A{i})").number_format = "#,##0"
    G.cell(row=i, column=8, value=f"=G{i}/SUM($G$5:$G$10)").number_format = "0.0%"
    G.cell(row=i, column=9, value=f"=IF(E{i}=0,\"\",G{i}/E{i})").number_format = "0.00"
box(G, 5, 10, 1, 9)
G["K3"], G["K3"].font = "Tabla cajón → grupo (la usa Datos_Clientes)", SUB
G["K4"], G["L4"] = "Código", "Grupo"
for c in ("K4", "L4"):
    G[c].fill, G[c].font = H_FILL, H_FONT
for i, (code, grp) in enumerate(CODE_TO_GROUP.items(), start=5):
    G.cell(row=i, column=11, value=code)
    G.cell(row=i, column=12, value=grp)
ch = BarChart()
ch.type, ch.title = "bar", "Gasto total por grupo"
ch.add_data(Reference(G, min_col=7, min_row=4, max_row=10), titles_from_data=True)
ch.set_categories(Reference(G, min_col=1, min_row=5, max_row=10))
ch.legend, ch.height, ch.width = None, 7, 15
ch.dataLabels = DataLabelList()
ch.dataLabels.showVal = True
ch.x_axis.scaling.orientation = "maxMin"
G.add_chart(ch, "A13")
widths(G, {"A": 26, "B": 20, "C": 40, "D": 48, "E": 9, "F": 10, "G": 11, "H": 9, "I": 12, "K": 9, "L": 26})

# ------------------------------------------------------------------ Cajones_27
K = wb.create_sheet("Cajones_27")
title(K, "Los 27 cajones (la tabla que va al comité)",
      "El valor de un cajón es clientes × frecuencia × ticket. El ranking por gasto suele sorprender: un cajón de recencia baja "
      "y gasto alto puede facturar más que el de 'campeones'. Ese es el grupo que de verdad necesita atención.", 11)
header(K, 4, ["Código", "Grupo", "Clientes", "% clientes", "Compras", "Frecuencia media", "Gasto total", "% gasto",
              "Gasto medio/cliente", "Ticket medio", "Ranking gasto"])
for i, code in enumerate(sorted(CODE_TO_GROUP, reverse=True), start=5):
    K.cell(row=i, column=1, value=code)
    K.cell(row=i, column=2, value=CODE_TO_GROUP[code])
    K.cell(row=i, column=3, value=f"=COUNTIF({DJ},A{i})")
    K.cell(row=i, column=4, value=f"=C{i}/SUM($C$5:$C$31)").number_format = "0.0%"
    K.cell(row=i, column=5, value=f"=SUMIFS(Datos_Clientes!$C$2:$C${LAST},{DJ},A{i})")
    K.cell(row=i, column=6, value=f'=IF(C{i}=0,"",E{i}/C{i})').number_format = "0.00"
    K.cell(row=i, column=7, value=f"=SUMIFS(Datos_Clientes!$D$2:$D${LAST},{DJ},A{i})").number_format = "#,##0"
    K.cell(row=i, column=8, value=f"=G{i}/SUM($G$5:$G$31)").number_format = "0.0%"
    K.cell(row=i, column=9, value=f'=IF(C{i}=0,"",G{i}/C{i})').number_format = "0.00"
    K.cell(row=i, column=10, value=f'=IF(E{i}=0,"",G{i}/E{i})').number_format = "0.00"
    K.cell(row=i, column=11, value=f"=RANK(G{i},$G$5:$G$31)")
box(K, 5, 31, 1, 11)
K.conditional_formatting.add("A5:K31", FormulaRule(formula=["$K5=1"], fill=KEY_FILL, font=Font(bold=True)))
K.conditional_formatting.add("A5:K31", FormulaRule(formula=["$C5=0"], font=Font(color="A6A6A6")))
widths(K, {"A": 9, "B": 26, "C": 9, "D": 10, "E": 9, "F": 11, "G": 11, "H": 9, "I": 12, "J": 11, "K": 10})

# ------------------------------------------------------------------ Lecturas
L = wb.create_sheet("Lecturas")
title(L, "Antes de puntuar: mira las curvas (y por qué no terciles automáticos)",
      "Todas las cifras se calculan sobre los clientes dentro de la ventana. Cada lectura cambia sola si cambian los datos.", 3)
header(L, 4, ["Indicador", "Valor", "Lectura"])
lect = [
    ("Clientes en ventana", f'=COUNTIF({DG},"Sí")', f'=TEXT(COUNTIF({DG},"No"),"0")&" clientes llevan más de "&Parametros!B6&" días sin comprar: quedan fuera (son inactivos, otro tratamiento)."'),
    ("% que solo ha comprado 1 vez", f"=COUNTIF({DL},1)/COUNT({DL})",
     '=IF(B6>2/3,"Más de 2 de cada 3 compran una sola vez: los terciles automáticos de frecuencia van a coincidir (fila siguiente).","Cuanto más alto sea este %, más riesgo de que los terciles automáticos vacíen una banda (fila siguiente).")'),
    ("Terciles automáticos de Compras", f'=ROUND(_xlfn.PERCENTILE.INC({DL},1/3),1)&" y "&ROUND(_xlfn.PERCENTILE.INC({DL},2/3),1)',
     f'=IF(_xlfn.PERCENTILE.INC({DL},1/3)=_xlfn.PERCENTILE.INC({DL},2/3),"Los dos cortes coinciden: la banda F=2 queda VACÍA y con ella 9 de los 27 cajones. Usa el corte de negocio 1 / 2 / 3+.","En esta base los terciles no vacían ninguna banda. Si más de 2 de cada 3 clientes compraran una sola vez, coincidirían en 1 y la banda F=2 quedaría vacía.")'),
    ("Cajones vacíos con cortes de negocio", "=COUNTIF(Cajones_27!C5:C31,0)", '=IF(B8=0,"Los 27 cajones tienen clientes.",B8&" cajones sin clientes. Es normal en combinaciones raras (p. ej. una sola compra con gasto de 2 tickets); revisa los cortes solo si se vacía una banda entera.")'),
    ("Gasto: media vs mediana", f'=TEXT(AVERAGE({DMV}),"0.00")&" vs "&TEXT(MEDIAN({DMV}),"0.00")',
     f'=TEXT(COUNTIF({DMV},"<"&AVERAGE({DMV}))/COUNT({DMV}),"0%")&" de los clientes gasta menos que la media. Presenta siempre la mediana al lado."'),
    ("Correlación Compras–Gasto", f"=CORREL({DL},{DMV})",
     '=IF(ABS(B10)>0.7,"Mayor que 0,7: F y M miden casi lo mismo (ticket casi fijo). El gasto apenas añade información sobre la frecuencia.","F y M aportan información distinta.")'),
]
for i, (k, v, t) in enumerate(lect, start=5):
    L.cell(row=i, column=1, value=k)
    L.cell(row=i, column=2, value=v)
    L.cell(row=i, column=3, value=t)
L["B6"].number_format = "0.0%"
L["B10"].number_format = "0.000"
box(L, 5, 10, 1, 3)
widths(L, {"A": 36, "B": 20, "C": 110})

# ------------------------------------------------------------------ Leeme
R = wb.create_sheet("Leeme", 0)
R["A1"], R["A1"].font = "RFM 333 · ejemplo con datos sintéticos", TITLE
txt = [
    ("Qué es", f"Un libro de trabajo con fórmulas vivas sobre {N} clientes INVENTADOS. Puntúa recencia, frecuencia y gasto de 1 a 3, "
               "forma 27 cajones y los agrupa en 6 grupos con una acción cada uno."),
    ("Qué responde", "¿Quiénes son mis mejores clientes, a quiénes reactivo antes de perderlos, y en quiénes no gasto presupuesto?"),
    ("Cómo usarlo con tus datos", "Pega tus clientes en Datos_Clientes, columnas A-D (id, fecha de la última compra, nº de compras, gasto) "
                                  "y arrastra las fórmulas de E a M hasta la última fila. Ajusta los cortes en Parametros (celdas amarillas)."),
    ("Tres reglas", "1) Fecha de corte fija (la última compra), nunca HOY(). 2) Mira las curvas antes de cortar: los terciles automáticos "
                    "pueden vaciar cajones (hoja Lecturas). 3) Ordena por gasto total, no por número de clientes."),
    ("Herramienta y skill", "Versión en script de Python y skill de Claude Code: github.com/carlosarisco55-max/rfm-segmentation-skill"),
]
for i, (k, v) in enumerate(txt, start=3):
    R.cell(row=i, column=1, value=k).font = Font(bold=True)
    R.cell(row=i, column=2, value=v)
    R.row_dimensions[i].height = 40
box(R, 3, 7, 1, 2)
R["A9"], R["A9"].font = "Hojas", SUB
for i, (sh, d) in enumerate([
    ("Parametros", "Fecha de corte, ventana y cortes de R, F y M (amarillo = editable)."),
    ("Datos_Clientes", "Cada cliente con sus días, puntuaciones, código de cajón y grupo. Filtrable."),
    ("Grupos", "Los 6 grupos con tamaño, gasto y la acción recomendada, más gráfico."),
    ("Cajones_27", "Los 27 cajones con frecuencia, ticket y ranking por gasto."),
    ("Lecturas", "Las comprobaciones previas: una compra, terciles, media vs mediana y correlación F-M."),
], start=10):
    c = R.cell(row=i, column=1, value=sh)
    c.hyperlink, c.font = f"#'{sh}'!A1", Font(color="0563C1", underline="single")
    R.cell(row=i, column=2, value=d)
widths(R, {"A": 26, "B": 120})

for ws in wb.worksheets:
    ws.sheet_view.showGridLines = ws.title == "Datos_Clientes"
    ws.page_setup.orientation = "landscape"
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
wb.calculation.fullCalcOnLoad = True
wb.save(OUT)
print("guardado", OUT)
