#!/usr/bin/env python3
"""
Problem 2 parse.py — Unified parser for gem5 stats.txt (Ruby or Classic caches)

Outputs per stats.txt:
  system, config, outdir
  simInsts/Ops, cycles, simSeconds, hostSeconds
  L1I_MPKI, L1D_MPKI, L2_MPKI, L1_total_MPKI
  IPC, CPI

Usage
  python3 parse.py --roots <dir1> [<dir2> ...] --out results.csv
  # or a single stats file:
  python3 parse.py --stats path/to/stats.txt --out results.csv
"""

import argparse, csv, math, re
from pathlib import Path
from typing import Dict, Optional

Number = float

# ---------- basic parsing ----------

def load_stats(path: Path) -> Dict[str, Number]:
    d: Dict[str, Number] = {}
    rx = re.compile(
        r"^\s*([A-Za-z0-9_.:\-/]+)\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+|inf|nan))\b",
        re.IGNORECASE,
    )
    with path.open("r", errors="ignore") as f:
        for line in f:
            m = rx.match(line)
            if not m:
                continue
            key, val = m.group(1), m.group(2)
            try:
                d[key] = float(val)
            except Exception:
                continue
    return d

def first(d: Dict[str, Number], keys):
    for k in keys:
        if k in d:
            return d[k]
    return None

def find_first(d: Dict[str, Number], pat: str, flags=re.IGNORECASE) -> Optional[Number]:
    rx = re.compile(pat, flags)
    for k, v in d.items():
        if rx.search(k):
            try:
                return float(v)
            except:
                pass
    return None

def sum_matching(d: Dict[str, Number], pat: str, flags=re.IGNORECASE) -> Optional[Number]:
    rx = re.compile(pat, flags)
    s, seen = 0.0, False
    for k, v in d.items():
        if rx.search(k):
            try:
                s += float(v); seen = True
            except:
                pass
    return s if seen else None

def detect_flavor(d: Dict[str, Number]) -> str:
    # Ruby stats always include 'ruby_system' keys.
    return "ruby" if any("ruby_system" in k for k in d.keys()) else "classic"

# ---------- MPKI helpers ----------

def mpki(misses: Optional[Number], sim_insts: Optional[Number]) -> Optional[Number]:
    if misses is None or sim_insts is None or sim_insts <= 0:
        return None
    return misses * 1000.0 / sim_insts

# ---------- extract metrics (both flavors) ----------

def extract_metrics(d: Dict[str, Number], outdir: Optional[Path]=None) -> Dict[str, Optional[Number]]:
    flavor = detect_flavor(d)
    m: Dict[str, Optional[Number]] = {}
    m["system"] = flavor
    m["outdir"] = str(outdir) if outdir else ""

    # Try to capture a readable config name from folder
    if outdir:
        m["config"] = outdir.name
    else:
        m["config"] = ""

    # Shared basics
    sim_insts = first(d, ["simInsts", "simOps"])
    m["simInsts/Ops"] = sim_insts
    m["simSeconds"]   = d.get("simSeconds")
    m["hostSeconds"]  = d.get("hostSeconds")
    m["cycles"] = first(d, [
        "board.processor.cores0.core.numCycles",
        "board.processor.cores.core.numCycles",
        "system.cpu.numCycles",
        "simCycles",
    ])
    m["IPC"] = first(d, ["board.processor.cores.core.ipc", "system.cpu.ipc"])
    m["CPI"] = first(d, ["board.processor.cores.core.cpi", "system.cpu.cpi"])

    if flavor == "ruby":
        # Sum across all controllers (multi-core / multi-bank safe)
        l1i_m = sum_matching(d, r"ruby_system\..*L1I.*cache\.m_demand_misses$")
        l1i_a = sum_matching(d, r"ruby_system\..*L1I.*cache\.m_demand_accesses$")
        l1d_m = sum_matching(d, r"ruby_system\..*L1D.*cache\.m_demand_misses$")
        l1d_a = sum_matching(d, r"ruby_system\..*L1D.*cache\.m_demand_accesses$")
        l2_m  = sum_matching(d, r"ruby_system\..*L2.*cache\.m_demand_misses$")
        l2_a  = sum_matching(d, r"ruby_system\..*L2.*cache\.m_demand_accesses$")
    else:
        # Classic (stdlib 'PrivateL1SharedL2CacheHierarchy')
        l1i_m = first(d, (
            "board.cache_hierarchy.l1icaches.demandMisses::total",
            "board.cache_hierarchy.l1icaches.overallMisses::total",
        ))
        l1i_a = first(d, (
            "board.cache_hierarchy.l1icaches.demandAccesses::total",
            "board.cache_hierarchy.l1icaches.overallAccesses::total",
        ))
        l1d_m = first(d, (
            "board.cache_hierarchy.l1dcaches.demandMisses::total",
            "board.cache_hierarchy.l1dcaches.overallMisses::total",
        ))
        l1d_a = first(d, (
            "board.cache_hierarchy.l1dcaches.demandAccesses::total",
            "board.cache_hierarchy.l1dcaches.overallAccesses::total",
        ))
        l2_m  = first(d, (
            "board.cache_hierarchy.l2cache.demandMisses::total",
            "board.cache_hierarchy.l2cache.overallMisses::total",
        ))
        l2_a  = first(d, (
            "board.cache_hierarchy.l2cache.demandAccesses::total",
            "board.cache_hierarchy.l2cache.overallAccesses::total",
        ))

    # Store raw counts (optional but handy)
    m["L1I_accesses"] = l1i_a; m["L1I_misses"] = l1i_m
    m["L1D_accesses"] = l1d_a; m["L1D_misses"] = l1d_m
    m["L2_accesses"]  = l2_a;  m["L2_misses"]  = l2_m

    # MPKI
    m["L1I_MPKI"] = mpki(l1i_m, sim_insts)
    m["L1D_MPKI"] = mpki(l1d_m, sim_insts)
    m["L2_MPKI"]  = mpki(l2_m,  sim_insts)
    if sim_insts and sim_insts > 0:
        m["L1_total_MPKI"] = (((l1i_m or 0.0) + (l1d_m or 0.0)) * 1000.0 / sim_insts)
    else:
        m["L1_total_MPKI"] = None

    return m

# ---------- CLI ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="*", help="directories to scan recursively for stats.txt")
    ap.add_argument("--stats", type=Path, help="single stats.txt to parse")
    ap.add_argument("--out",   type=Path, default=Path("summary.csv"), help="CSV output path")
    args = ap.parse_args()

    rows = []
    if args.stats:
        d = load_stats(args.stats)
        rows.append(extract_metrics(d, args.stats.parent))
    if args.roots:
        for root in args.roots:
            for p in Path(root).rglob("stats.txt"):
                d = load_stats(p)
                rows.append(extract_metrics(d, p.parent))

    # Print a compact preview
    for r in rows:
        print(f"[{r['system']}] {r['config']}: "
              f"simInsts={r['simInsts/Ops']:.0f} "
              f"IPC={r['IPC'] if r['IPC'] is not None else 'NA'} "
              f"L1I={r['L1I_MPKI']:.3f} L1D={r['L1D_MPKI']:.3f} L2={r['L2_MPKI']:.3f}"
              if all(v is not None for v in [r['simInsts/Ops'], r['L1I_MPKI'], r['L1D_MPKI'], r['L2_MPKI']])
              else f"[{r['system']}] {r['config']}: (partial metrics)")

    # Write CSV
    hdr = ["system","config","outdir",
           "simInsts/Ops","cycles","simSeconds","hostSeconds","IPC","CPI",
           "L1I_accesses","L1I_misses","L1I_MPKI",
           "L1D_accesses","L1D_misses","L1D_MPKI",
           "L1_total_MPKI",
           "L2_accesses","L2_misses","L2_MPKI"]
    write_header = not args.out.exists()
    with args.out.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hdr)
        if write_header:
            w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in hdr})

if __name__ == "__main__":
    main()
