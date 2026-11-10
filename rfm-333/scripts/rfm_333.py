"""RFM 333: segmentación Recencia-Frecuencia-Monto con puntuación 1-3 por eje.

Entrada: CSV con una fila por cliente (id, fecha última compra, nº compras, gasto).
Salida: CSV con scores, código y grupo por cliente + resumen por consola.
Solo librería estándar de Python.

Ejemplo:
    python rfm_333.py --input clientes.csv --id-col Id_Cliente \
        --date-col Fecha_Ultima_Compra --date-format "%m/%d/%Y" \
        --frequency-col Compras --monetary-col Gasto \
        --r-cuts 120 243 --f-cuts 3 2 --m-cuts 70 35 --window 365
"""
import argparse
import csv
import re
import statistics
from collections import defaultdict
from datetime import datetime

GROUPS = {
    "1. Campeones": "333 332 323 322",
    "2. Recientes de una compra": "313 312 311 331 321",
    "3. Valiosos enfriandose": "233 232 223 222",
    "4. Ocasionales en pausa": "213 212 211 231 221",
    "5. Valiosos en riesgo": "133 132 123 122",
    "6. A punto de perderse": "113 112 111 131 121",
}
CODE_TO_GROUP = {c: g for g, codes in GROUPS.items() for c in codes.split()}


def to_number(text):
    # Acepta "57.01 €", "57,01", "1.234,50 €"
    s = re.sub(r"[^\d,.\-]", "", text)
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    return float(s)


def score_low_is_good(value, a, b):
    return 3 if value <= a else (2 if value <= b else 1)


def score_high_is_good(value, a, b):
    return 3 if value >= a else (2 if value >= b else 1)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", required=True)
    p.add_argument("--output", default="rfm_resultado.csv")
    p.add_argument("--id-col", required=True)
    p.add_argument("--date-col", required=True)
    p.add_argument("--date-format", default="%Y-%m-%d")
    p.add_argument("--frequency-col", required=True)
    p.add_argument("--monetary-col", required=True)
    p.add_argument("--cutoff", help="Fecha de corte AAAA-MM-DD. Por defecto, la última fecha de la base.")
    p.add_argument("--window", type=int, default=365, help="Días del periodo. Los clientes fuera quedan excluidos.")
    p.add_argument("--r-cuts", type=float, nargs=2, default=[120, 243], metavar=("R3_MAX", "R2_MAX"))
    p.add_argument("--f-cuts", type=float, nargs=2, default=[3, 2], metavar=("F3_MIN", "F2_MIN"))
    p.add_argument("--m-cuts", type=float, nargs=2, metavar=("M3_MIN", "M2_MIN"),
                   help="Por defecto: 2 y 1 veces el ticket medio.")
    p.add_argument("--auto-terciles", action="store_true", help="Usa terciles automáticos (didáctico).")
    a = p.parse_args()

    with open(a.input, encoding="utf-8-sig") as f:
        raw = list(csv.DictReader(f))
    rows = [{
        "id": r[a.id_col],
        "date": datetime.strptime(r[a.date_col].strip(), a.date_format),
        "f": int(to_number(r[a.frequency_col])),
        "m": to_number(r[a.monetary_col]),
    } for r in raw]

    cutoff = datetime.strptime(a.cutoff, "%Y-%m-%d") if a.cutoff else max(r["date"] for r in rows)
    for r in rows:
        r["days"] = (cutoff - r["date"]).days
    inside = [r for r in rows if 0 <= r["days"] <= a.window]
    print(f"Fecha de corte: {cutoff.date()} | periodo: {a.window} días")
    print(f"Clientes en el periodo: {len(inside)} de {len(rows)} ({len(rows) - len(inside)} fuera)")

    fs = [r["f"] for r in inside]
    ms = [r["m"] for r in inside]
    ds = [r["days"] for r in inside]
    ticket = sum(ms) / sum(fs)
    mean_m, med_m = statistics.mean(ms), statistics.median(ms)
    print(f"Gasto: media {mean_m:.2f} | mediana {med_m:.2f} | "
          f"{sum(1 for x in ms if x < mean_m) / len(ms) * 100:.1f}% por debajo de la media")
    print(f"Ticket medio: {ticket:.2f} | clientes con 1 compra: {fs.count(1) / len(fs) * 100:.1f}%")
    if len(set(fs)) > 1 and len(set(ms)) > 1:
        r_fm = statistics.correlation(fs, ms)
        print(f"Correlación F-M: {r_fm:.3f}" + ("  <- F y M miden casi lo mismo" if abs(r_fm) > 0.7 else ""))

    if a.auto_terciles:
        td, tf, tm = (statistics.quantiles(v, n=3) for v in (ds, fs, ms))
        r_cuts, f_cuts, m_cuts = td, [tf[1] + 1e-9, tf[0] + 1e-9], [tm[1] + 1e-9, tm[0] + 1e-9]
        print(f"Terciles -> días {td}, compras {tf}, gasto {[round(x, 2) for x in tm]}")
    else:
        r_cuts, f_cuts = a.r_cuts, a.f_cuts
        m_cuts = a.m_cuts or [2 * ticket, ticket]
    print(f"Cortes -> R {r_cuts} | F {f_cuts} | M {[round(x, 2) for x in m_cuts]}")

    boxes = defaultdict(lambda: [0, 0, 0.0])
    bands = {k: defaultdict(lambda: [0, 0.0]) for k in "RFM"}
    for r in inside:
        R = score_low_is_good(r["days"], *r_cuts)
        F = score_high_is_good(r["f"], *f_cuts)
        M = score_high_is_good(r["m"], *m_cuts)
        r["code"] = f"{R}{F}{M}"
        r["group"] = CODE_TO_GROUP[r["code"]]
        r["scores"] = (R, F, M)
        b = boxes[r["code"]]
        b[0] += 1; b[1] += r["f"]; b[2] += r["m"]
        for k, s in zip("RFM", (R, F, M)):
            bands[k][s][0] += 1; bands[k][s][1] += r["m"]

    n, total = len(inside), sum(ms)
    print("\nBandas (clientes · % gasto):")
    for k in "RFM":
        parts = [f"{s}: {bands[k][s][0]} · {bands[k][s][1] / total * 100:.1f}%" for s in (3, 2, 1)]
        empty = [s for s in (3, 2, 1) if bands[k][s][0] == 0]
        print(f"  {k}  " + " | ".join(parts) + (f"  <- AVISO: banda {empty} vacía" if empty else ""))

    print("\n27 cajones ordenados por gasto total:")
    print("  código  clientes  frec.media  gasto_total  %gasto  grupo")
    for code, (c, comp, g) in sorted(boxes.items(), key=lambda kv: -kv[1][2]):
        print(f"  {code}    {c:>7}  {comp / c:>10.2f}  {g:>11,.0f}  {g / total * 100:>5.1f}%  {CODE_TO_GROUP[code]}")
    empty_boxes = 27 - len(boxes)
    if empty_boxes:
        print(f"  ({empty_boxes} cajones sin clientes)")

    print("\nGrupos:")
    agg = defaultdict(lambda: [0, 0.0])
    for r in inside:
        agg[r["group"]][0] += 1; agg[r["group"]][1] += r["m"]
    for g in GROUPS:
        c, s = agg[g]
        if c:
            print(f"  {g}: {c} clientes ({c / n * 100:.1f}%) · {s:,.0f} ({s / total * 100:.1f}% del gasto)")

    with open(a.output, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Id", "Dias", "Compras", "Gasto", "R", "F", "M", "Codigo_RFM", "Grupo"])
        for r in inside:
            w.writerow([r["id"], r["days"], r["f"], f"{r['m']:.2f}", *r["scores"], r["code"], r["group"]])
    print(f"\nResultado guardado en {a.output}")


if __name__ == "__main__":
    main()
