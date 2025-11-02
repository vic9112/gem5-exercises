import json
import matplotlib.pyplot as plt
import os

# Load the stats files
def load_stats(file_path):
    stats = {}
    with open(file_path, 'r') as f:
        for line in f:
            # Skip empty lines or lines that start with '#' (comments)
            if not line.strip() or line.startswith('#'):
                continue
            
            # Split the line into parts and handle possible errors
            try:
                parts = line.split()
                if len(parts) >= 2:
                    # Check if the value can be converted to a float
                    try:
                        stats[parts[0]] = float(parts[1])
                    except ValueError:
                        print(f"Skipping non-numeric value: {parts[1]} in line: {line.strip()}")
            except IndexError:
                print(f"Skipping malformed line: {line.strip()}")
    return stats

# Example file paths
baseline_path = r'log\simpoint_full_run\stats.txt'
simpoint_path = r'log\simpoint_run_1\stats.txt'
smarts_path = r'log\smarts\stats.txt'

print(f"Loading baseline stats from: {os.path.abspath(baseline_path)}")
print(f"Loading simpoint stats from: {os.path.abspath(simpoint_path)}")
print(f"Loading smarts stats from: {os.path.abspath(smarts_path)}")

# Load the stats data
baseline_stats = load_stats(baseline_path)
simpoint_stats = load_stats(simpoint_path)
smarts_stats = load_stats(smarts_path)

# Extract IPC, L1 Miss Rates, L2 Miss Rates, and Simulation Time
baseline_ipc = baseline_stats['board.processor.cores.core.ipc']  # Replace with actual IPC if available
simpoint_ipc = simpoint_stats['board.processor.cores.core.ipc']
smarts_ipc = smarts_stats['board.processor.start.core.ipc']

baseline_l1_miss_rate = baseline_stats['board.cache_hierarchy.l1d-cache-0.demandMissRate::total']
simpoint_l1_miss_rate = simpoint_stats['board.cache_hierarchy.l1d-cache-0.demandMissRate::total']
smarts_l1_miss_rate = smarts_stats['board.cache_hierarchy.l1d-cache-0.demandMissRate::total']

baseline_l2_miss_rate = baseline_stats['board.cache_hierarchy.l2-cache-0.demandMissRate::total']
simpoint_l2_miss_rate = simpoint_stats['board.cache_hierarchy.l2-cache-0.demandMissRate::total']
smarts_l2_miss_rate = smarts_stats['board.cache_hierarchy.l2-cache-0.demandMissRate::total']

baseline_time = baseline_stats['simSeconds']
simpoint_time = simpoint_stats['simSeconds']
smarts_time = smarts_stats['simSeconds']

# IPC Comparison
plt.figure(figsize=(10, 6))
plt.bar(['Baseline', 'Simpoint', 'SMARTS'], [baseline_ipc, simpoint_ipc, smarts_ipc], color='skyblue')
plt.title('IPC Comparison')
plt.ylabel('IPC')
plt.show()

# Miss Rate Comparison
plt.figure(figsize=(10, 6))
plt.bar(['Baseline', 'Simpoint', 'SMARTS'], [baseline_l1_miss_rate, simpoint_l1_miss_rate, smarts_l1_miss_rate], color='lightgreen')
plt.title('L1 Miss Rate Comparison')
plt.ylabel('Miss Rate')
plt.show()

# L2 Miss Rate Comparison
plt.figure(figsize=(10, 6))
plt.bar(['Baseline', 'Simpoint', 'SMARTS'], [baseline_l2_miss_rate, simpoint_l2_miss_rate, smarts_l2_miss_rate], color='lightcoral')
plt.title('L2 Miss Rate Comparison')
plt.ylabel('Miss Rate')
plt.show()

# Time Comparison
plt.figure(figsize=(10, 6))
plt.bar(['Baseline', 'Simpoint', 'SMARTS'], [baseline_time, simpoint_time, smarts_time], color='lightyellow')
plt.title('Simulation Time Comparison')
plt.ylabel('Time (seconds)')
plt.show()
