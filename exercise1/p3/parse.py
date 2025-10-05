#!/usr/bin/env python3
"""
parse.py — Summarize Problem 3 runs (throughput + avgMemAccLat) into CSV.

For each stats.txt:
  - simSeconds, hostSeconds
  - bytesRead, bytesWritten, total bytes
  - throughput (GiB/s, MiB/s)
  - avgMemAccLat (aggregate across memory controllers; print ticks + ns)

Assumes gem5 default tick rate (1e12 ticks/s => 1 tick = 1 ps, 1000 ticks = 1 ns).
"""

import argparse, csv, re
from pathlib import Path
from typing import Dict, Optional, List

Number = float

def load_stats(path: Path) -> Dict[str, Number]:
    d: Dict[str, Number] = {}
    rx = re.compile(r"^\s*([A-Za-z0-9_.:\-/]+)\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+|inf|nan))\b")
    with path.open("r", errors="ignore") as f:
        for line in f:
            m = rx.match(line)
            if m:
                k, v = m.group(1), m.group(2)
                try:
                    d[k] = float(v)
                except:
                    pass
    return d

def sum_matching(d: Dict[str, Number], pat: str) -> Optional[Number]:
    rx = re.compile(pat)
    s, seen = 0.0, False
    for k, v in d.items():
        if rx.search(k):
            s += float(v); seen = True
    return s if seen else None

def list_matching(d: Dict[str, Number], pat: str) -> List[Number]:
    rx = re.compile(pat)
    vals = []
    for k, v in d.items():
        if rx.search(k):
            vals.append(float(v))
    return vals

def find_weighted_avg_mem_lat(d: Dict[str, Number]) -> (Optional[Number], Optional[Number]):
    """
    Aggregate avgMemAccLat across any controllers present.
    Weight by (numReads + numWrites) if available; else simple mean.
    Returns (avg_ticks, avg_ns).
    """
    lats = []       # per-controller avgMemAccLat (ticks)
    weights = []    # per-controller accesses
    # Match any controller path that ends in avgMemAccLat
    for key, val in d.items():
        if key.endswith(".avgMemAccLat"):
            lats.append(float(val))
            # Try to infer a controller prefix to fetch its reads/writes
            prefix = key[: -len(".avgMemAccLat")]
            nr = d.get(prefix + ".numReads")
            nw = d.get(prefix + ".numWrites")
            if nr is None and nw is None:
                # Sometimes there's a combined counter
                acc = d.get(prefix + ".numReqs")
            else:
                acc = (nr or 0.0) + (nw or 0.0)
            weights.append(acc if acc is not None else 0.0)

    if not lats:
        return (None, None)

    if any(w > 0 for w in weights):
        total_w = sum(weights) if sum(weights) > 0 else 1.0
        avg_ticks = sum(L * W for L, W in zip(lats, weights)) / total_w
    else:
        avg_ticks = sum(lats) / len(lats)

    avg_ns = avg_ticks / 1000.0  # 1 ps per tick
    return (avg_ticks, avg_ns)

def parse_one(stats_path: Path) -> Dict[str, Number]:
    d = load_stats(stats_path)

    # Sum across generator cores (usually one)
    br = sum_matching(d, r"board\.processor\.cores\d*\.generator\.bytesRead$")
    bw = sum_matching(d, r"board\.processor\.cores\d*\.generator\.bytesWritten$")
    simsec = d.get("simSeconds")
    hostsec = d.get("hostSeconds")

    total_bytes = (br or 0.0) + (bw or 0.0)
    thru_Bps = (total_bytes / simsec) if (simsec and simsec > 0) else None

    lat_ticks, lat_ns = find_weighted_avg_mem_lat(d)

    return {
        "config": stats_path.parent.name,
        "outdir": str(stats_path.parent),
        "simSeconds": simsec,
        "hostSeconds": hostsec,
        "bytesRead": br,
        "bytesWritten": bw,
        "bytesTotal": total_bytes,
        "throughput_Bps": thru_Bps,
        "avgMemAccLat_ticks": lat_ticks,
        "avgMemAccLat_ns": lat_ns,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", required=True,
                    help='outdir roots (globs OK), e.g. "p3/out_*"')
    ap.add_argument("--out", default="p3-summary.csv")
    args = ap.parse_args()

    rows = []
    for root in args.roots:
        for p in Path().glob(root):
            for stats in Path(p).rglob("stats.txt"):
                rows.append(parse_one(stats))

    # Preview
    for r in rows:
        g = r["throughput_Bps"]
        a = r["avgMemAccLat_ns"]
        if g is not None:
            print(f"{r['config']:<25}: {g:.3f} B/s, avgMemAccLat={a:.3f} ns" if a is not None
                else f"{r['config']:<25}: {g:.3f} B/s, avgMemAccLat=N/A")
        else:
            print(f"{r['config']}: (incomplete)")

    # CSV
    hdr = ["config","outdir","simSeconds","hostSeconds",
           "bytesRead","bytesWritten","bytesTotal",
           "throughput_Bps","avgMemAccLat_ticks","avgMemAccLat_ns"]
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hdr)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"Wrote {args.out} with {len(rows)} rows.")

if __name__ == "__main__":
    main()
