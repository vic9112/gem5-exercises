'''
Refer to github.com/gem5bootcamp/2024/materials/02-Using-gem5/09-sampling/01-simpoint
'''

baseline_ipc = 0.0
baseline_stats_file = "/workspaces/gem5-exercises/exercise2/p1/log/simpoint_full_run/stats.txt"

with open(baseline_stats_file, "r") as f:
    for line in f:
        if "board.processor.cores.core.ipc" in line:
            line = line.split()
            baseline_ipc = float(line[1])
            break

num_simpoints = 4
simpoint_ipcs = []
simpoint_weights = []

for i in range(num_simpoints):
    simpoint_stats_file = f"/workspaces/gem5-exercises/exercise2/p1/log/simpoint_run_{i}/stats.txt"
    with open(simpoint_stats_file, "r") as f:
        simpoint_ipc = 0.0
        for line in f:
            if "board.processor.cores.core.ipc" in line:
                line = line.split()
                simpoint_ipc = float(line[1])
        simpoint_ipcs.append(simpoint_ipc)
    simpoint_stdout_file = f"/workspaces/gem5-exercises/exercise2/p1/log/simpoint_run_{i}/simout.txt"
    simpoint_weight = 0.0
    with open(simpoint_stdout_file, "r") as f:
        for line in f:
            if "Finish SimPoint" in line:
                line = line.split()
                simpoint_weight = float(line[-1])
    simpoint_weights.append(simpoint_weight)

predicted_ipc = 0.0

for i in range(num_simpoints):
    predicted_ipc += simpoint_ipcs[i] * simpoint_weights[i]

print(f"predicted IPC: {predicted_ipc}")
print(f"actual IPC: {baseline_ipc}")
print(f"relative error: {(abs(baseline_ipc - predicted_ipc)/baseline_ipc)*100}%")