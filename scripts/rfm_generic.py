"""Generic RFM (Recency, Frequency, Monetary) segmentation.

Works in two modes:

1. `aggregated` — the input CSV already has one row per customer with a
   recency, frequency and monetary column (e.g. Recency/Total_Purchases/Total_Spend).
2. `transactions` — the input CSV has one row per order/transaction
   (customer id, order date, amount). The script aggregates it into R/F/M
   per customer first.

Stdlib only (csv, statistics, datetime, argparse) — no pandas required.

Usage:
    python rfm_generic.py --input customers.csv --mode aggregated \
        --id-col ID --recency-col Recency --frequency-col Total_Purchases \
        --monetary-col Total_Spend --output segments.csv

    python rfm_generic.py --input orders.csv --mode transactions \
        --id-col customer_id --date-col order_date --amount-col amount \
        --output segments.csv
"""
import argparse
import csv
import statistics
from collections import defaultdict
from datetime import datetime


def score_breakpoints(values):
    return statistics.quantiles(values, n=5)


def score_of(value, breakpoints, invert=False):
    score = 1
    for bp in breakpoints:
        if value > bp:
            score += 1
    return (6 - score) if invert else score


def segment_of(r_score, fm_score):
    """Simplified 6-segment RFM map. See SKILL.md for the reasoning behind
    each rule and why the order matters (first match wins)."""
    if r_score >= 4 and fm_score >= 4:
        return "Champions"
    if r_score >= 3 and fm_score >= 3:
        return "Clientes fieles"
    if r_score >= 4 and fm_score < 3:
        return "Nuevos / prometedores"
    if r_score < 3 and fm_score >= 4:
        return "En riesgo (antes valiosos)"
    if r_score <= 2 and fm_score <= 2:
        return "Perdidos"
    return "Necesitan atencion"


def build_aggregated(rows, id_col, recency_col, frequency_col, monetary_col):
    customers = []
    for r in rows:
        customers.append(
            {
                "id": r[id_col],
                "recency": float(r[recency_col]),
                "frequency": float(r[frequency_col]),
                "monetary": float(r[monetary_col]),
            }
        )
    return customers


def build_from_transactions(rows, id_col, date_col, amount_col, date_format, reference_date):
    by_customer = defaultdict(list)
    for r in rows:
        d = datetime.strptime(r[date_col], date_format)
        by_customer[r[id_col]].append((d, float(r[amount_col])))

    if reference_date:
        ref = datetime.strptime(reference_date, date_format)
    else:
        ref = max(d for dates in by_customer.values() for d, _ in dates)

    customers = []
    for cust_id, txns in by_customer.items():
        last_purchase = max(d for d, _ in txns)
        customers.append(
            {
                "id": cust_id,
                "recency": (ref - last_purchase).days,
                "frequency": len(txns),
                "monetary": sum(a for _, a in txns),
            }
        )
    return customers


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True)
    p.add_argument("--output", default="rfm_segments.csv")
    p.add_argument("--mode", choices=["aggregated", "transactions"], required=True)
    p.add_argument("--id-col", required=True)
    p.add_argument("--recency-col")
    p.add_argument("--frequency-col")
    p.add_argument("--monetary-col")
    p.add_argument("--date-col")
    p.add_argument("--amount-col")
    p.add_argument("--date-format", default="%Y-%m-%d")
    p.add_argument("--reference-date", default=None, help="YYYY-MM-DD; defaults to the latest date in the data")
    args = p.parse_args()

    with open(args.input, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if args.mode == "aggregated":
        for req in ("recency_col", "frequency_col", "monetary_col"):
            if not getattr(args, req):
                p.error(f"--{req.replace('_', '-')} is required in aggregated mode")
        customers = build_aggregated(rows, args.id_col, args.recency_col, args.frequency_col, args.monetary_col)
    else:
        for req in ("date_col", "amount_col"):
            if not getattr(args, req):
                p.error(f"--{req.replace('_', '-')} is required in transactions mode")
        customers = build_from_transactions(
            rows, args.id_col, args.date_col, args.amount_col, args.date_format, args.reference_date
        )

    n = len(customers)
    r_bp = score_breakpoints([c["recency"] for c in customers])
    f_bp = score_breakpoints([c["frequency"] for c in customers])
    m_bp = score_breakpoints([c["monetary"] for c in customers])

    results = []
    for c in customers:
        r_score = score_of(c["recency"], r_bp, invert=True)
        f_score = score_of(c["frequency"], f_bp)
        m_score = score_of(c["monetary"], m_bp)
        fm_score = (f_score + m_score) / 2
        results.append(
            {
                "ID": c["id"],
                "Recency": c["recency"],
                "Frequency": c["frequency"],
                "Monetary": c["monetary"],
                "R_score": r_score,
                "F_score": f_score,
                "M_score": m_score,
                "RFM_Segment": segment_of(r_score, fm_score),
            }
        )

    with open(args.output, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    print("=== RFM SEGMENTS ===")
    seg_groups = defaultdict(lambda: [0, 0.0])
    for res, c in zip(results, customers):
        seg_groups[res["RFM_Segment"]][0] += 1
        seg_groups[res["RFM_Segment"]][1] += c["monetary"]

    for seg, (count, monetary) in sorted(seg_groups.items(), key=lambda x: -x[1][1]):
        pct = count / n * 100
        avg = monetary / count
        print(f"{seg}: {count} clientes ({pct:.1f}%), valor medio {avg:,.2f}")

    print(f"\nOutput guardado en {args.output} ({n} clientes)")


if __name__ == "__main__":
    main()
