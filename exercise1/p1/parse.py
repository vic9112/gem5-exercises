#!/usr/bin/env python3
# Walk log/* folders, parse stats.txt, and write p1/results.csv
# Metrics: simSeconds, simInsts, totalCycles, IPC, CPI, MPKI_I/D/L2
# Still includes classic fallbacks (system.cpu.*).

import os, glob, csv
from pathlib import Path

OUT_GLOB = "./log/*"
STATS_FILE = "stats.txt"
CSV_OUT = "results.csv"

# Key candidates in priority order (new stdlib/Ruby first, then classic)
KEYS = {
    "simSeconds": [
        "simSeconds",
        "board.simSeconds",  # very unlikely, but harmless
    ],
    "simInsts": [
        "simInsts",
        "board.processor.cores.core.commitStats0.numInsts",  # thread-level committed insts
        "board.processor.cores.core.fetchStats0.numInsts",
        "system.cpu.commit.committedInsts",
        "sim_insts",
    ],
    "cycles": [
        "board.processor.cores.core.numCycles",
        "system.cpu.numCycles",
        "simCycles",
        "system.cpu.cycle",
    ],
    # L1I demand misses
    "l1i_m": [
        "board.cache_hierarchy.ruby_system.l1_controllers.L1Icache.m_demand_misses",
        "system.cpu.icache.overall_misses::total",
        "system.cpu.icache.ReadReq_misses::total",
        "system.cpu.icache.Overall_Misses",
    ],
    # L1D demand misses (prefer total; else sum R/W)
    "l1d_m_total": [
        "board.cache_hierarchy.ruby_system.l1_controllers.L1Dcache.m_demand_misses",
        "system.cpu.dcache.overall_misses::total",
        "system.cpu.dcache.Overall_Misses",
    ],
    "l1d_m_r": [
        "system.cpu.dcache.ReadReq_misses::total",
        "system.cpu.dcache.ReadReq_misses",
    ],
    "l1d_m_w": [
        "system.cpu.dcache.WriteReq_misses::total",
        "system.cpu.dcache.WriteReq_misses",
    ],
    # L2 demand misses
    "l2_m": [
        "board.cache_hierarchy.ruby_system.l2_controllers.L2cache.m_demand_misses",
        "system.l2cache.overall_misses::total",
        "system.l2.overall_misses::total",
        "system.l2cache.Overall_Misses",
        "system.l2.Overall_Misses",
    ],
}

def to_number(s):
    try:
        # int if it rounds cleanly, else float
        if any(ch in s for ch in ".eE"):
            return float(s)
        return int(s)
    except Exception:
        return None

def load_stats(path):
    stats = {}
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("-"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            key, val = parts[0], parts[1]
            num = to_number(val)
            if num is not None:
                stats[key] = num
    return stats

def pick(stats, names, default=None):
    for n in names:
        if n in stats:
            return stats[n]
    return default

def compute_metrics(run_dir, stats):
    sim_seconds = pick(stats, KEYS["simSeconds"])
    sim_insts   = pick(stats, KEYS["simInsts"])
    cycles      = pick(stats, KEYS["cycles"])

    # L1I misses
    l1i_m = pick(stats, KEYS["l1i_m"], 0)

    # L1D misses (prefer total; else sum of read/write)
    l1d_m = pick(stats, KEYS["l1d_m_total"])
    if l1d_m is None:
        l1d_m = (pick(stats, KEYS["l1d_m_r"], 0) or 0) + (pick(stats, KEYS["l1d_m_w"], 0) or 0)

    # L2 misses
    l2_m = pick(stats, KEYS["l2_m"], 0)

    # IPC/CPI
    ipc = cpi = None
    if sim_insts and cycles and cycles > 0:
        ipc = sim_insts / cycles
        cpi = 1.0 / ipc if ipc > 0 else None

    # MPKI (Missed Predictions per Kilo Instructions)
    mpki_i = (l1i_m / (sim_insts / 1000.0)) if sim_insts and sim_insts > 0 else None
    mpki_d = (l1d_m / (sim_insts / 1000.0)) if sim_insts and sim_insts > 0 else None
    mpki_l2 = (l2_m / (sim_insts / 1000.0)) if sim_insts and sim_insts > 0 else None

    # Decode params from folder name (same conventions as sweep.sh)
    name = Path(run_dir).name
    cpu  = "o3" if "o3" in name.lower() else ("timing" if "timing" in name.lower() else None)

    def grab_int(prefix):
        for token in name.split("_"):
            if token.startswith(prefix):
                try:
                    return int(token[len(prefix):])
                except ValueError:
                    pass
        return None

    issue = grab_int("issue")
    rob   = grab_int("rob")
    lq    = grab_int("lq")
    sq    = grab_int("sq")

    return {
        "run": name,
        "cpu": cpu,
        "issueWidth": issue,
        "numROBEntries": rob,
        "LQEntries": lq,
        "SQEntries": sq,
        "simSeconds": sim_seconds,
        "simInsts": sim_insts,
        "totalCycles": cycles,
        "IPC": ipc,
        "CPI": cpi,
        "L1I_misses": l1i_m,
        "L1D_misses": l1d_m,
        "L2_misses": l2_m,
        "MPKI_I": mpki_i,
        "MPKI_D": mpki_d,
        "MPKI_L2": mpki_l2,
    }

def main():
    rows = []
    for run_dir in sorted(glob.glob(OUT_GLOB)):
        stats_path = os.path.join(run_dir, STATS_FILE)
        if not os.path.isfile(stats_path):
            continue
        stats = load_stats(stats_path)
        rows.append(compute_metrics(run_dir, stats))

    cols = ["run","cpu","issueWidth","numROBEntries","LQEntries","SQEntries",
            "simSeconds","simInsts","totalCycles","IPC","CPI",
            "L1I_misses","L1D_misses","L2_misses","MPKI_I","MPKI_D","MPKI_L2"]

    os.makedirs("p1", exist_ok=True)
    with open(CSV_OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"Wrote {CSV_OUT} with {len(rows)} rows.")

if __name__ == "__main__":
    main()
