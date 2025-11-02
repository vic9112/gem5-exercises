import os
import re
import csv

# ---- Problem 3 inputs ----
CONFIGS = {
    'classic_fs': 'log/fs_classic/stats.txt',
    'chi_fs'    : 'log/fs_chi/stats.txt',
}
OUT_CSV = 'p3_summary.csv'

BEGIN = '---------- Begin Simulation Statistics ----------'
END   = '---------- End Simulation Statistics   ----------'

def load_last_stats_block(path):
    """Parse only the *last* gem5 stats block."""
    stats = {}
    if not os.path.exists(path):
        print(f"[WARN] File not found: {path}")
        return stats

    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    # find last begin
    begin_idx = None
    for i, ln in enumerate(lines):
        if BEGIN in ln:
            begin_idx = i
    if begin_idx is None:
        print(f"[WARN] No stats block found in {path}")
        return stats

    # collect until end
    for ln in lines[begin_idx+1:]:
        if END in ln:
            break
        s = ln.strip()
        if not s or s.startswith('#'):
            continue
        parts = s.split()
        if len(parts) < 2:
            continue
        key = parts[0]
        try:
            val = float(parts[1])
        except ValueError:
            continue
        stats[key] = val
    return stats

def extract_classic(stats):
    """Classic coherence: L2 overall miss metrics exist; no Ruby/CHI counters."""
    return {
        # Classic L2 totals (present in your classic stats)
        'l2_overall_misses'    : stats.get('board.cache_hierarchy.l2cache.overallMisses::total', float('nan')),
        'l2_miss_rate'         : stats.get('board.cache_hierarchy.l2cache.overallMissRate::total', float('nan')),
        'l2_miss_latency_mean' : stats.get('board.cache_hierarchy.l2cache.overallAvgMissLatency::total', float('nan')),
        # Ruby-only fields → blank/NaN for classic
        'l2_ruby_m_demand_misses': float('nan'),
        'chi_ReadUnique_total'   : float('nan'),
        'chi_CleanUnique_total'  : float('nan'),
        'chi_ReadShared_total'   : float('nan'),
    }

def extract_chi(stats):
    """CHI/Ruby: no Classic overall*; use Ruby L2 and CHI op totals."""
    # Ruby L2 demand misses
    l2_m_demand = stats.get('board.cache_hierarchy.l2cache.cache.m_demand_misses', float('nan'))

    # CHI op totals: prefer Cache_Controller.<Op>::total; for ReadUnique add *_PoC if present
    def chi_total(op):
        total = 0.0
        key_plain = f'board.cache_hierarchy.ruby_system.Cache_Controller.{op}::total'
        if key_plain in stats:
            total += stats[key_plain]
        key_poc = f'board.cache_hierarchy.ruby_system.Cache_Controller.{op}_PoC::total'
        if op == 'ReadUnique' and key_poc in stats:
            total += stats[key_poc]
        return total if total != 0.0 else float('nan')

    return {
        'l2_overall_misses'       : float('nan'),
        'l2_miss_rate'            : float('nan'),
        'l2_miss_latency_mean'    : float('nan'),
        'l2_ruby_m_demand_misses' : l2_m_demand,
        'chi_ReadUnique_total'    : chi_total('ReadUnique'),
        'chi_CleanUnique_total'   : chi_total('CleanUnique'),
        'chi_ReadShared_total'    : chi_total('ReadShared'),
    }

rows = []
for cfg, path in CONFIGS.items():
    stats = load_last_stats_block(path)
    is_ruby = any(k.startswith('board.cache_hierarchy.ruby_system') for k in stats)

    common = {
        'config'     : cfg,
        'simSeconds' : stats.get('simSeconds', float('nan')),
        'hostSeconds': stats.get('hostSeconds', float('nan')),
    }
    if is_ruby:
        common.update(extract_chi(stats))
    else:
        common.update(extract_classic(stats))
    rows.append(common)

fieldnames = [
    'config',
    # Classic metrics
    'l2_overall_misses', 'l2_miss_rate', 'l2_miss_latency_mean',
    # Ruby/CHI metrics
    'l2_ruby_m_demand_misses', 'chi_ReadUnique_total', 'chi_CleanUnique_total', 'chi_ReadShared_total',
    # timing
    'simSeconds', 'hostSeconds',
]

with open(OUT_CSV, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, '') for k in fieldnames})

print(f"[OK] Wrote {OUT_CSV}")
