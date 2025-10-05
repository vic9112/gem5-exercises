#!/usr/bin/env python3
"""
p5/parse.py — SE vs FS summary with aligned wall-clock comparisons + ROI stats.

Outputs, per outdir:
  - hostSeconds_total (from final block)
  - hostSeconds_ROI   (final - prior if two blocks; else final)
  - simSeconds_total / simSeconds_ROI
  - simInsts, cycles, IPC/CPI (with robust fallbacks)
  - L1I/L1D/L2 MPKI (classic stdlib names; per-instance or aggregated)
  - TLB miss rate (legacy + FS/.mmu patterns)
"""

import argparse, csv, re, glob
from pathlib import Path
from typing import Dict, List, Optional, Iterable, Set

Number = float
NUM_RE = re.compile(r"^\s*([A-Za-z0-9_.:\-/\[\]]+)\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+|inf|nan))\b")

def _parse_block(lines: List[str]) -> Dict[str, Number]:
    d: Dict[str, Number] = {}
    for line in lines:
        m = NUM_RE.match(line)
        if not m:
            continue
        k, v = m.group(1), m.group(2)
        try:
            d[k] = float(v)
        except:
            pass
    return d

def load_blocks(stats_path: Path) -> List[Dict[str, Number]]:
    if not stats_path.exists():
        return []
    blocks, cur = [], []
    with stats_path.open("r", errors="ignore") as f:
        for line in f:
            if "Begin Simulation Statistics" in line:
                if cur:
                    blocks.append(cur)
                    cur = []
                continue
            if "End Simulation Statistics" in line:
                if cur:
                    blocks.append(cur)
                    cur = []
                continue
            cur.append(line)
    if cur:
        blocks.append(cur)
    return [_parse_block(b) for b in blocks if b]

def first(d: Dict[str, Number], keys) -> Optional[Number]:
    for k in keys:
        if k in d:
            return d[k]
    return None

def sum_matching(d: Dict[str, Number], pat: str) -> Optional[Number]:
    rx = re.compile(pat)
    s = 0.0
    seen = False
    for k, v in d.items():
        if rx.search(k):
            s += float(v); seen = True
    return s if seen else None

def mpki(m: Optional[Number], insts: Optional[Number]) -> Optional[Number]:
    return (m * 1000.0 / insts) if (m is not None and insts and insts > 0) else None

def cache_stat_first(d: Dict[str, Number], bases: List[str], kinds: List[str]) -> Optional[Number]:
    for base in bases:
        for suf in kinds:
            key = f"{base}.{suf}"
            if key in d:
                return d[key]
    return None

def extract_row(blocks: List[Dict[str, Number]], outdir: Path) -> Dict[str, Optional[Number]]:
    row = {"config": outdir.name, "outdir": str(outdir)}
    if not blocks:
        return row

    final = blocks[-1]
    prior = blocks[-2] if len(blocks) >= 2 else None

    # Totals from final block
    row["hostSeconds_total"] = final.get("hostSeconds")
    row["simSeconds_total"]  = final.get("simSeconds")

    # ROI time:
    # If we have a sane prior block, use (final - prior).
    # Otherwise, treat the final block itself as ROI (common when only ROI block is printed).
    def roi_val(key: str) -> Optional[Number]:
        f = final.get(key)
        if prior is not None and key in prior and f is not None:
            p = prior.get(key)
            if p is not None and f >= p:
                return f - p
        return f  # fallback: final value

    row["hostSeconds_ROI"] = roi_val("hostSeconds")
    row["simSeconds_ROI"]  = roi_val("simSeconds")

    d = final  # ROI stats

    # Instructions & cycles
    sim_insts = first(d, ["simInsts", "simOps"])
    if sim_insts is None:
        sim_insts = sum_matching(d, r"\.core\.(committedInsts|thread_\d+\.numInsts)$")

    cycles = first(d, [
        "board.processor.cores0.core.numCycles",
        "board.processor.cores.core.numCycles",
        "system.cpu.numCycles",
        "simCycles",
        "board.processor.switch.core.numCycles",
        "board.processor.start.core.numCycles",
    ])
    if cycles is None:
        cycles = sum_matching(d, r"^board\.processor\.(?:start|switch|cores)\d+\.core\.numCycles$")

    row["simInsts"] = sim_insts
    row["cycles"]   = cycles

    ipc = first(d, ["board.processor.cores.core.ipc", "system.cpu.ipc",
                    "board.processor.switch.core.ipc", "board.processor.start.core.ipc"])
    cpi = first(d, ["board.processor.cores.core.cpi", "system.cpu.cpi",
                    "board.processor.switch.core.cpi", "board.processor.start.core.cpi"])
    if ipc is None and cpi is not None and cpi > 0:
        ipc = 1.0 / cpi
    if (ipc is None or (ipc != ipc)) and sim_insts and cycles and cycles > 0:
        ipc = sim_insts / cycles
    if cpi is None and ipc is not None and ipc > 0:
        cpi = 1.0 / ipc
    row["IPC"] = ipc
    row["CPI"] = cpi

    # Cache counters (aggregated and per-instance)
    l1i_bases = [
        "board.cache_hierarchy.l1icaches",
        "board.cache_hierarchy.l1i-caches",
        "board.cache_hierarchy.l1i-cache-0",
    ]
    l1d_bases = [
        "board.cache_hierarchy.l1dcaches",
        "board.cache_hierarchy.l1d-caches",
        "board.cache_hierarchy.l1d-cache-0",
    ]
    l2_bases = [
        "board.cache_hierarchy.l2cache",
        "board.cache_hierarchy.l2-caches",
        "board.cache_hierarchy.l2-cache-0",
    ]
    miss_kinds = [
        "demandMisses::total",
        "overallMisses::total",
        "ReadReq.misses::total",
        "ReadReq.misses",
    ]
    acc_kinds = [
        "demandAccesses::total",
        "overallAccesses::total",
        "ReadReq.accesses::total",
        "ReadReq.accesses",
    ]

    L1I_m = cache_stat_first(d, l1i_bases, miss_kinds)
    L1I_a = cache_stat_first(d, l1i_bases, acc_kinds)
    L1D_m = cache_stat_first(d, l1d_bases, miss_kinds)
    L1D_a = cache_stat_first(d, l1d_bases, acc_kinds)
    L2_m  = cache_stat_first(d, l2_bases,  miss_kinds)
    L2_a  = cache_stat_first(d, l2_bases,  acc_kinds)

    row["L1I_accesses"] = L1I_a; row["L1I_misses"] = L1I_m; row["L1I_MPKI"] = mpki(L1I_m, sim_insts)
    row["L1D_accesses"] = L1D_a; row["L1D_misses"] = L1D_m; row["L1D_MPKI"] = mpki(L1D_m, sim_insts)
    row["L2_accesses"]  = L2_a;  row["L2_misses"]  = L2_m;  row["L2_MPKI"]  = mpki(L2_m,  sim_insts)
    row["L1_total_MPKI"] = (((L1I_m or 0.0) + (L1D_m or 0.0)) * 1000.0 / sim_insts) \
        if (sim_insts and sim_insts > 0) else None

    # TLB (legacy + FS/.mmu, incl. rd/wr counters)
    itb_m = sum_matching(d, r"\.itb\.(misses|walk_misses|inst_misses|rdMisses|wrMisses)(::total)?$")
    dtb_m = sum_matching(d, r"\.dtb\.(misses|walk_misses|data_misses|rdMisses|wrMisses)(::total)?$")
    itb_a = sum_matching(d, r"\.itb\.(accesses|lookups|inst_lookups|rdAccesses|wrAccesses)(::total)?$")
    dtb_a = sum_matching(d, r"\.dtb\.(accesses|lookups|data_lookups|rdAccesses|wrAccesses)(::total)?$")
    tlb_m = (itb_m or 0.0) + (dtb_m or 0.0)
    tlb_a = (itb_a or 0.0) + (dtb_a or 0.0)
    row["TLB_accesses"] = tlb_a if tlb_a else None
    row["TLB_misses"]   = tlb_m if tlb_m else None
    row["TLB_miss_rate"] = (tlb_m / tlb_a) if (tlb_a and tlb_a > 0) else None

    return row

def iter_outdirs_from_roots(roots: List[str]) -> List[Path]:
    """Expand --roots patterns and return unique directories that contain a stats.txt."""
    found: List[Path] = []
    seen: Set[Path] = set()

    def _add(p: Path):
        if p not in seen:
            seen.add(p); found.append(p)

    for pat in roots:
        matches = glob.glob(pat)
        if not matches:
            matches = [pat]
        for m in sorted(matches):
            p = Path(m)
            if p.is_file() and p.name == "stats.txt":
                _add(p.parent); continue
            if p.is_dir():
                st = p / "stats.txt"
                if st.exists(): _add(p); continue
                for child in sorted(p.glob("*/stats.txt")): _add(child.parent)
                for child in sorted(p.rglob("stats.txt")):  _add(child.parent)
            else:
                par = p.parent if p.parent != Path("") else Path(".")
                for child in sorted(par.rglob("stats.txt")): _add(child.parent)
    return found

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", required=True, help="outdir roots to scan (e.g., log/*)")
    ap.add_argument("--out", default="p5-summary.csv")
    args = ap.parse_args()

    rows = []
    for d in iter_outdirs_from_roots(args.roots):
        stats = Path(d) / "stats.txt"
        if stats.exists():
            blocks = load_blocks(stats)
            rows.append(extract_row(blocks, Path(d)))

    for r in rows:
        print(f"{r['config']}: host_total={r.get('hostSeconds_total')}  host_ROI={r.get('hostSeconds_ROI')}  "
              f"IPC={r.get('IPC')}  L1I={r.get('L1I_MPKI')}  L1D={r.get('L1D_MPKI')}  L2={r.get('L2_MPKI')}  "
              f"TLBmr={r.get('TLB_miss_rate')}")

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
