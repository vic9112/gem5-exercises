#!/usr/bin/env python3
"""
p5/parse.py — SE vs FS summary with aligned wall-clock comparisons + ROI stats.

Outputs, per outdir:
  - hostSeconds_total (start->final)
  - hostSeconds_ROI   (prev->final) if multiple dumps (FS with ROI)
  - simSeconds_total / simSeconds_ROI
  - simInsts, cycles, IPC/CPI
  - L1I/L1D/L2 MPKI (classic stdlib names)
  - TLB miss rate
"""

import argparse, csv, re
from pathlib import Path
from typing import Dict, List, Optional

Number = float
NUM_RE = re.compile(r"^\s*([A-Za-z0-9_.:\-/]+)\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+|inf|nan))\b")

def _parse_block(lines: List[str]) -> Dict[str, Number]:
    d: Dict[str, Number] = {}
    for line in lines:
        m = NUM_RE.match(line)
        if not m: continue
        k, v = m.group(1), m.group(2)
        try: d[k] = float(v)
        except: pass
    return d

def load_blocks(stats_path: Path) -> List[Dict[str, Number]]:
    if not stats_path.exists(): return []
    blocks, cur = [], []
    with stats_path.open("r", errors="ignore") as f:
        for line in f:
            if "Begin Simulation Statistics" in line:
                if cur: blocks.append(cur); cur = []
                continue
            cur.append(line)
    if cur: blocks.append(cur)
    return [_parse_block(b) for b in blocks if b]

def first(d: Dict[str, Number], keys) -> Optional[Number]:
    for k in keys:
        if k in d: return d[k]
    return None

def sum_matching(d: Dict[str, Number], pat: str) -> Optional[Number]:
    rx = re.compile(pat); s = 0.0; seen = False
    for k, v in d.items():
        if rx.search(k): s += float(v); seen = True
    return s if seen else None

def mpki(m: Optional[Number], insts: Optional[Number]) -> Optional[Number]:
    return (m * 1000.0 / insts) if (m is not None and insts and insts > 0) else None

def extract_row(blocks: List[Dict[str, Number]], outdir: Path) -> Dict[str, Optional[Number]]:
    row = {"config": outdir.name, "outdir": str(outdir)}
    if not blocks: return row
    final = blocks[-1]
    prior = blocks[-2] if len(blocks) >= 2 else None

    # Wall-clock totals and ROI via hostSeconds diff
    row["hostSeconds_total"] = final.get("hostSeconds")
    row["simSeconds_total"]  = final.get("simSeconds")
    row["hostSeconds_ROI"] = (final.get("hostSeconds") - prior.get("hostSeconds")) \
        if (prior and "hostSeconds" in prior and "hostSeconds" in final) else None
    row["simSeconds_ROI"] = (final.get("simSeconds") - prior.get("simSeconds")) \
        if (prior and "simSeconds" in prior and "simSeconds" in final) else None

    d = final  # ROI stats (FS after reset; SE single dump)
    row["simInsts"] = first(d, ["simInsts", "simOps"])
    row["cycles"]   = first(d, [
        "board.processor.cores0.core.numCycles",
        "board.processor.cores.core.numCycles",
        "system.cpu.numCycles",
        "simCycles",
    ])
    row["IPC"] = first(d, ["board.processor.cores.core.ipc", "system.cpu.ipc"])
    row["CPI"] = first(d, ["board.processor.cores.core.cpi", "system.cpu.cpi"])

    # Classic cache counters
    L1I_m = first(d, ("board.cache_hierarchy.l1icaches.demandMisses::total",
                      "board.cache_hierarchy.l1icaches.overallMisses::total"))
    L1I_a = first(d, ("board.cache_hierarchy.l1icaches.demandAccesses::total",
                      "board.cache_hierarchy.l1icaches.overallAccesses::total"))
    L1D_m = first(d, ("board.cache_hierarchy.l1dcaches.demandMisses::total",
                      "board.cache_hierarchy.l1dcaches.overallMisses::total"))
    L1D_a = first(d, ("board.cache_hierarchy.l1dcaches.demandAccesses::total",
                      "board.cache_hierarchy.l1dcaches.overallAccesses::total"))
    L2_m  = first(d, ("board.cache_hierarchy.l2cache.demandMisses::total",
                      "board.cache_hierarchy.l2cache.overallMisses::total"))
    L2_a  = first(d, ("board.cache_hierarchy.l2cache.demandAccesses::total",
                      "board.cache_hierarchy.l2cache.overallAccesses::total"))

    row["L1I_accesses"] = L1I_a; row["L1I_misses"] = L1I_m; row["L1I_MPKI"] = mpki(L1I_m, row["simInsts"])
    row["L1D_accesses"] = L1D_a; row["L1D_misses"] = L1D_m; row["L1D_MPKI"] = mpki(L1D_m, row["simInsts"])
    row["L2_accesses"]  = L2_a;  row["L2_misses"]  = L2_m;  row["L2_MPKI"]  = mpki(L2_m,  row["simInsts"])
    row["L1_total_MPKI"] = (((L1I_m or 0.0) + (L1D_m or 0.0)) * 1000.0 / row["simInsts"]) \
        if (row["simInsts"] and row["simInsts"] > 0) else None

    # TLB (best-effort across cores)
    itb_m = sum_matching(d, r"\.itb\.(misses|walk_misses|inst_misses)(::total)?$")
    dtb_m = sum_matching(d, r"\.dtb\.(misses|walk_misses|data_misses)(::total)?$")
    itb_a = sum_matching(d, r"\.itb\.(accesses|lookups|inst_lookups)(::total)?$")
    dtb_a = sum_matching(d, r"\.dtb\.(accesses|lookups|data_lookups)(::total)?$")
    tlb_m = (itb_m or 0.0) + (dtb_m or 0.0)
    tlb_a = (itb_a or 0.0) + (dtb_a or 0.0)
    row["TLB_accesses"] = tlb_a if tlb_a else None
    row["TLB_misses"]   = tlb_m if tlb_m else None
    row["TLB_miss_rate"] = (tlb_m / tlb_a) if (tlb_a and tlb_a > 0) else None

    return row

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", required=True, help="outdir roots to scan")
    ap.add_argument("--out", default="p5-summary.csv")
    args = ap.parse_args()

    rows = []
    for root in args.roots:
        rp = Path(root)
        dirs = [rp] if (rp.is_dir() and (rp / "stats.txt").exists()) else list(rp.glob("*"))
        for d in dirs:
            stats = Path(d) / "stats.txt"
            if stats.exists():
                blocks = load_blocks(stats)
                rows.append(extract_row(blocks, Path(d)))

    for r in rows:
        print(f"{r['config']}: host_total={r['hostSeconds_total']}  host_ROI={r['hostSeconds_ROI']}  "
              f"IPC={r['IPC']}  L1I={r['L1I_MPKI']}  L1D={r['L1D_MPKI']}  L2={r['L2_MPKI']}")

    hdr = ["config","outdir",
           "hostSeconds_total","hostSeconds_ROI",
           "simSeconds_total","simSeconds_ROI",
           "simInsts","cycles","IPC","CPI",
           "L1I_accesses","L1I_misses","L1I_MPKI",
           "L1D_accesses","L1D_misses","L1D_MPKI",
           "L1_total_MPKI",
           "L2_accesses","L2_misses","L2_MPKI",
           "TLB_accesses","TLB_misses","TLB_miss_rate"]
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hdr)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in hdr})

    print(f"Wrote {args.out} with {len(rows)} rows.")

if __name__ == "__main__":
    main()
