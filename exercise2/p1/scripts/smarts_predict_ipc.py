from pathlib import Path
import math

baseline_ipc = 0.0
baseline_stats_file = "/workspaces/gem5-exercises/exercise2/p1/log/simpoint_full_run/stats.txt"

with open(baseline_stats_file, "r") as f:
    for line in f:
        if "board.processor.cores.core.ipc" in line:
            line = line.split()
            baseline_ipc = float(line[1])
            break

smart_stats_file = Path("/workspaces/gem5-exercises/exercise2/p1/log/smarts/stats.txt")

with smart_stats_file.open("r") as f:
    num_samples = 0
    sample_ipc = []
    for line in f:
        if "board.processor.switch.core.ipc" in line:
            line = line.split()
            ipc = float(line[1])
            sample_ipc.append(ipc)
            num_samples += 1
    num_samples -= 1
    avg_ipc = sum(sample_ipc[:-1]) / num_samples
    print(f"Number of samples: {num_samples}")
    print(f"Predicted Overall IPC: {avg_ipc}")
    print(f"Actual Overall IPC: {baseline_ipc}") # board.processor.cores.core.ipc: 0.939719
    print(f"Relative Error: {(math.fabs(avg_ipc - baseline_ipc)/baseline_ipc)*100}%")