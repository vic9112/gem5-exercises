#!/usr/bin/env python3
"""
parse.py — Problem 4 summary with correct ROI handling.

- Each "Begin Simulation Statistics" block is a per-interval dump (since you
  call m5.stats.reset() at the 2nd exit). Therefore:
    * hostSeconds_total = sum(hostSeconds over all blocks)
    * hostSeconds_ROI   = hostSeconds in the final block
  (same for simSeconds)

- ROI micro-arch metrics (IPC/CPI, MPKI, TLB) are taken from the FINAL block.

Usage:
  python3 parse.py --roots out_p4_1_timing out_p4_1_o3 out_p4_2_kvm --out p4-summary.csv
"""

import argparse
import csv
import re
from pathlib import Path
from typing import Dict, List, Optional

Num = float

# Matches: "metric.name   12345"
NUM_RE = re.compile(
    r"^\s*([A-Za-z0-9_.:\-/\[\]]+)\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+|inf|nan))\b"
)

def _to_float(s: str) -> Optional[Num]:
    try:
        return float(s)
    except Exception:
        return None

def _parse_block(lines: List[str]) -> Dict[str, Num]:
    d: Dict[str, Num] = {}
    for line in lines:
        m = NUM_RE.match(line)
        if not m:
            continue
        val = _to_float(m.group(2))
        if val is not None:
            d[m.group(1)] = val
    return d

def load_blocks(stats_path: Path) -> List[Dict[str, Num]]:
    """Split stats.txt into list of dict blocks, one per 'Begin Simulation Statistics'."""
    if not stats_path.exists():
        return []
    blocks_raw: List[List[str]] = []
    cur: List[str] = []
    with stats_path.open("r", errors="ignore") as f:
        for line in f:
            if "Begin Simulation Statistics" in line:
                if cur:
                    blocks_raw.append(cur)
                    cur = []
                continue
            cur.append(line)
    if cur:
        blocks_raw.append(cur)
    return [_parse_block(b) for b in blocks_raw if b]

def first(d: Dict[str, Num], keys) -> Optional[Num]:
    for k in keys:
        if k in d:
            return d[k]
    return None

def sum_matching(d: Dict[str, Num], pat: str) -> Optional[Num]:
    """Sum all stats whose key matches 'pat'. Returns None if no matches."""
    rx = re.compile(pat)
    total = 0.0
    hit = False
    for k, v in d.items():
        if rx.search(k):
            total += float(v)
            hit = True
    return total if hit else None

def mpki(misses: Optional[Num], insts: Optional[Num]) -> Optional[Num]:
    if misses is None or insts is None or insts <= 0:
        return None
    return misses * 1000.0 / insts

def compute_ipc_cpi(insts: Optional[Num], cycles: Optional[Num],
                    ipc_field: Optional[Num], cpi_field: Optional[Num]):
    ipc = ipc_field
    cpi = cpi_field
    # If only CPI is present, invert to get IPC.
    if ipc is None and cpi is not None and cpi > 0:
        ipc = 1.0 / cpi
    # If neither given, derive from insts/cycles if available.
    if (ipc is None or (ipc != ipc)) and insts and cycles and cycles > 0:  # NaN-safe
        ipc = insts / cycles
    if cpi is None and ipc is not None:
        cpi = (1.0 / ipc) if ipc > 0 else None
    return ipc, cpi

def extract_row(blocks: List[Dict[str, Num]], outdir: Path) -> Dict[str, Optional[Num]]:
    row: Dict[str, Optional[Num]] = {
        "config": outdir.name,
        "outdir": str(outdir),
    }
    if not blocks:
        return row

    # --- Totals & ROI time ---
    host_list = [b.get("hostSeconds") for b in blocks if b.get("hostSeconds") is not None]
    sim_list  = [b.get("simSeconds")  for b in blocks if b.get("simSeconds")  is not None]

    row["hostSeconds_total"] = sum(host_list) if host_list else None
    row["simSeconds_total"]  = sum(sim_list)  if sim_list  else None
    row["hostSeconds_ROI"]   = host_list[-1]  if host_list else None
    row["simSeconds_ROI"]    = sim_list[-1]   if sim_list  else None

    # --- ROI micro-arch metrics from FINAL block ---
    d = blocks[-1]

    # Instructions & cycles
    simInsts = first(d, ["simInsts", "simOps"])
    cycles   = first(d, [
        "simCycles",
        "board.processor.cores.core.numCycles",
        "board.processor.cores0.core.numCycles",
        "system.cpu.numCycles",
    ])

    # Fallback: sum per-core/thread counters if totals aren't present.
    if simInsts is None:
        # e.g., ...core.committedInsts   or   ...core.thread_0.numInsts
        simInsts = sum_matching(d, r"\.core\.(?:committedInsts|thread_\d+\.numInsts)$")
    if cycles is None:
        cycles = sum_matching(d, r"\.core\.numCycles$")

    ipc_field = first(d, ["board.processor.cores.core.ipc", "system.cpu.ipc"])
    cpi_field = first(d, ["board.processor.cores.core.cpi", "system.cpu.cpi"])
    IPC, CPI = compute_ipc_cpi(simInsts, cycles, ipc_field, cpi_field)

    row["simInsts"] = simInsts
    row["cycles"]   = cycles
    row["IPC"]      = IPC
    row["CPI"]      = CPI

    # Cache stats (Classic): handle both aggregated groups and per-instance names.
    # Misses
    L1I_m = first(d, (
        "board.cache_hierarchy.l1icaches.demandMisses::total",
        "board.cache_hierarchy.l1icaches.overallMisses::total",
    ))
    if L1I_m is None:
        L1I_m = sum_matching(d, r"board\.cache_hierarchy\.l1i-cache-\d+\.(?:demand|overall)Misses::total$")
    L1D_m = first(d, (
        "board.cache_hierarchy.l1dcaches.demandMisses::total",
        "board.cache_hierarchy.l1dcaches.overallMisses::total",
    ))
    if L1D_m is None:
        L1D_m = sum_matching(d, r"board\.cache_hierarchy\.l1d-cache-\d+\.(?:demand|overall)Misses::total$")
    L2_m = first(d, (
        "board.cache_hierarchy.l2cache.demandMisses::total",
        "board.cache_hierarchy.l2cache.overallMisses::total",
    ))
    if L2_m is None:
        L2_m = sum_matching(d, r"board\.cache_hierarchy\.l2-cache-\d+\.(?:demand|overall)Misses::total$")

    # Accesses
    L1I_a = first(d, (
        "board.cache_hierarchy.l1icaches.demandAccesses::total",
        "board.cache_hierarchy.l1icaches.overallAccesses::total",
    ))
    if L1I_a is None:
        L1I_a = sum_matching(d, r"board\.cache_hierarchy\.l1i-cache-\d+\.(?:demand|overall)Accesses::total$")
    L1D_a = first(d, (
        "board.cache_hierarchy.l1dcaches.demandAccesses::total",
        "board.cache_hierarchy.l1dcaches.overallAccesses::total",
    ))
    if L1D_a is None:
        L1D_a = sum_matching(d, r"board\.cache_hierarchy\.l1d-cache-\d+\.(?:demand|overall)Accesses::total$")
    L2_a = first(d, (
        "board.cache_hierarchy.l2cache.demandAccesses::total",
        "board.cache_hierarchy.l2cache.overallAccesses::total",
    ))
    if L2_a is None:
        L2_a = sum_matching(d, r"board\.cache_hierarchy\.l2-cache-\d+\.(?:demand|overall)Accesses::total$")

    row["L1I_accesses"] = L1I_a
    row["L1I_misses"]   = L1I_m
    row["L1D_accesses"] = L1D_a
    row["L1D_misses"]   = L1D_m
    row["L2_accesses"]  = L2_a
    row["L2_misses"]    = L2_m

    row["L1I_MPKI"] = mpki(L1I_m, simInsts)
    row["L1D_MPKI"] = mpki(L1D_m, simInsts)
    row["L2_MPKI"]  = mpki(L2_m,  simInsts)
    row["L1_total_MPKI"] = (((L1I_m or 0.0) + (L1D_m or 0.0)) * 1000.0 / simInsts) \
        if (simInsts and simInsts > 0) else None

    # ---- TLB miss rate (sum across cores; support both naming styles) ----
    # Newer/FS stdlib style: ... .mmu.itb/dtb.(rdAccesses|wrAccesses|rdMisses|wrMisses)
    itb_a_rw = sum_matching(d, r"\.mmu\.itb\.(?:rdAccesses|wrAccesses)(::total)?$")
    dtb_a_rw = sum_matching(d, r"\.mmu\.dtb\.(?:rdAccesses|wrAccesses)(::total)?$")
    itb_m_rw = sum_matching(d, r"\.mmu\.itb\.(?:rdMisses|wrMisses)(::total)?$")
    dtb_m_rw = sum_matching(d, r"\.mmu\.dtb\.(?:rdMisses|wrMisses)(::total)?$")

    # Legacy style: ... .itb/dtb.(accesses|lookups|misses|walk_misses|inst_misses)
    itb_a_legacy = sum_matching(d, r"\.itb\.(?:accesses|lookups|inst_lookups)(::total)?$")
    dtb_a_legacy = sum_matching(d, r"\.dtb\.(?:accesses|lookups|data_lookups)(::total)?$")
    itb_m_legacy = sum_matching(d, r"\.itb\.(?:misses|walk_misses|inst_misses)(::total)?$")
    dtb_m_legacy = sum_matching(d, r"\.dtb\.(?:misses|walk_misses|data_misses)(::total)?$")

    # Prefer the newer mmu.* if present; else fall back to legacy names.
    itb_a = itb_a_rw if itb_a_rw is not None else itb_a_legacy
    dtb_a = dtb_a_rw if dtb_a_rw is not None else dtb_a_legacy
    itb_m = itb_m_rw if itb_m_rw is not None else itb_m_legacy
    dtb_m = dtb_m_rw if dtb_m_rw is not None else dtb_m_legacy

    # Only blank the CSV fields if no keys matched at all; otherwise show 0.0
    tlb_a = None
    tlb_m = None
    if itb_a is not None or dtb_a is not None:
        tlb_a = (itb_a or 0.0) + (dtb_a or 0.0)
    if itb_m is not None or dtb_m is not None:
        tlb_m = (itb_m or 0.0) + (dtb_m or 0.0)

    row["TLB_accesses"] = tlb_a
    row["TLB_misses"]   = tlb_m
    row["TLB_miss_rate"] = (tlb_m / tlb_a) if (tlb_a is not None and tlb_a > 0) else None

    return row

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", required=True,
                    help="Outdir roots (dirs containing stats.txt or parents of such dirs)")
    ap.add_argument("--out", default="p4-summary.csv")
    args = ap.parse_args()

    rows = []
    for root in args.roots:
        rp = Path(root)
        # If rp itself has stats.txt, use it; otherwise scan its children.
        candidates = [rp] if (rp.is_dir() and (rp / "stats.txt").exists()) else list(rp.glob("*"))
        for d in candidates:
            stats = Path(d) / "stats.txt"
            if stats.exists():
                blocks = load_blocks(stats)
                rows.append(extract_row(blocks, Path(d)))

    # quick preview
    for r in rows:
        print(
            f"{r['config']}: host_total={r.get('hostSeconds_total')}  "
            f"host_ROI={r.get('hostSeconds_ROI')}  "
            f"IPC={r.get('IPC')}  L1I={r.get('L1I_MPKI')}  "
            f"L1D={r.get('L1D_MPKI')}  L2={r.get('L2_MPKI')}  "
            f"TLB_miss_rate={r.get('TLB_miss_rate')}"
        )

    hdr = [
        "config","outdir",
        "hostSeconds_total","hostSeconds_ROI",
        "simSeconds_total","simSeconds_ROI",
        "simInsts","cycles","IPC","CPI",
        "L1I_accesses","L1I_misses","L1I_MPKI",
        "L1D_accesses","L1D_misses","L1D_MPKI",
        "L1_total_MPKI",
        "L2_accesses","L2_misses","L2_MPKI",
        "TLB_accesses","TLB_misses","TLB_miss_rate",
    ]
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hdr)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in hdr})

    print(f"Wrote {args.out} with {len(rows)} rows.")

if __name__ == "__main__":
    main()
