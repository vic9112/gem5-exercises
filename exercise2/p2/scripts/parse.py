import os
import re
import csv

CONFIGS = {
    'core_num2'   : 'log/core_num_2/stats.txt',
    'core_num4'   : 'log/core_num_4/stats.txt',
    'cpu_freq_2GHz': 'log/cpu_freq_2GHz/stats.txt',
    'cpu_freq_3GHz': 'log/cpu_freq_3GHz/stats.txt',
    'l3_size_2MB' : 'log/l3_size_2MB/stats.txt',
    'l3_size_4MB' : 'log/l3_size_4MB/stats.txt',
}

OUT_CSV = 'power_summary.csv'

def load_stats(file_path):
    stats = {}
    if not os.path.exists(file_path):
        print(f"[WARN] File not found: {file_path}")
        return stats

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            key = parts[0]
            try:
                val = float(parts[1])
            except ValueError:
                continue
            stats[key] = val
    return stats

CPU_DYN_RE   = re.compile(r'^board\.processor\.cores\d+\.core\.power_model\.dynamicPower$')
CPU_STA_RE   = re.compile(r'^board\.processor\.cores\d+\.core\.power_model\.staticPower$')
L3_DYN_RE    = re.compile(r'^board\.cache_hierarchy\.l3_cache(?:\.\w+)?\.power_model\.dynamicPower$')
L3_STA_RE    = re.compile(r'^board\.cache_hierarchy\.l3_cache(?:\.\w+)?\.power_model\.staticPower$')

def extract_powers(stats):
    cpu_dynamic = 0.0
    cpu_static_vals = []
    l3_dynamic = 0.0
    l3_static = 0.0

    for k, v in stats.items():
        if CPU_DYN_RE.match(k):
            cpu_dynamic += v
        elif CPU_STA_RE.match(k):
            cpu_static_vals.append(v)
        elif L3_DYN_RE.match(k):
            l3_dynamic += v
        elif L3_STA_RE.match(k):
            l3_static += v

    cpu_static = (cpu_static_vals[0] if cpu_static_vals else float('nan'))

    if cpu_dynamic == 0.0 and not any(CPU_DYN_RE.match(k) for k in stats):
        print("[WARN] CPU dynamicPower key not found.")
    if not cpu_static_vals:
        print("[WARN] CPU staticPower key not found.")
    if l3_dynamic == 0.0 and not any(L3_DYN_RE.match(k) for k in stats):
        print("[WARN] L3 dynamicPower key not found.")
    if l3_static == 0.0 and not any(L3_STA_RE.match(k) for k in stats):
        print("[WARN] L3 staticPower key not found.")

    return cpu_dynamic, cpu_static, l3_dynamic, l3_static

rows = []
for cfg, path in CONFIGS.items():
    stats = load_stats(path)
    cpu_dyn, cpu_sta, l3_dyn, l3_sta = extract_powers(stats)

    total_dyn = cpu_dyn + l3_dyn
    total_sta = cpu_sta + l3_sta
    total     = total_dyn + total_sta

    rows.append({
        'config': cfg,
        'cpu_dynamic_w': cpu_dyn,
        'cpu_static_w':  cpu_sta,
        'l3_dynamic_w':  l3_dyn,
        'l3_static_w':   l3_sta,
        'total_dynamic_w': total_dyn,
        'total_static_w':  total_sta,
        'total_w':         total
    })

fieldnames = ['config', 'cpu_dynamic_w', 'cpu_static_w', 'l3_dynamic_w', 'l3_static_w',
              'total_dynamic_w', 'total_static_w', 'total_w']

with open(OUT_CSV, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"[OK] Wrote {OUT_CSV}")
