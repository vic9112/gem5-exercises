"""
- Set the ISA to X86 and use x86-npb-is-size-s-run as the benchmark.
- Compare both TimingSimpleCPU and X86O3CPU models to observe the 
  differences between a simple in-order core and out-of-order core.
- Experiment with key micro-architecture parameters for O3CPU. EX:
  - issueWidth (e.g., 2 vs 6)
  - numROBEntries (e.g., 64 vs 192)
  - LQEntries and SQEntries (load/store queue depth, e.g., 16 vs 64), 
    varied separately
- Report basic performance metrics such as IPC, CPI, MPKI, total cycles, 
  and simSeconds.
"""
import argparse

from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.cachehierarchies.ruby.mesi_two_level_cache_hierarchy import (
    MESITwoLevelCacheHierarchy,
)
from gem5.components.memory.single_channel import SingleChannelDDR4_2400
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.resources.resource import obtain_resource
from gem5.simulate.simulator import Simulator

ap = argparse.ArgumentParser()
ap.add_argument("--cpu", choices=["timing","o3"], required=True)
ap.add_argument("--width", type=int, default=4)
ap.add_argument("--rob",   type=int, default=128)
ap.add_argument("--lq",    type=int, default=64)
ap.add_argument("--sq",    type=int, default=64)
args = ap.parse_args()

# Setup a MESI Two Level Cache Hierarchy.
cache_hierarchy = MESITwoLevelCacheHierarchy(
    l1d_size="16kB", l1d_assoc=8,
    l1i_size="16kB", l1i_assoc=8,
    l2_size="256kB", l2_assoc=16,
    num_l2_banks=1,
)

# Setup the system memory.
memory = SingleChannelDDR4_2400()

#Set the ISA to X86 and use x86-npb-is-size-s-run as the benchmark
cpu_type = CPUTypes.TIMING if args.cpu == "timing" else CPUTypes.O3
print("Using TimingSimpleCPU") if args.cpu == "timing" else print("Using X86O3CPU")
processor = SimpleProcessor(cpu_type=cpu_type, isa=ISA.X86, num_cores=1)

if args.cpu == "o3":
    for core in processor.get_cores():
        # Reach the underlying O3 CPU object (DerivO3CPU / X86O3CPU)
        m = getattr(core, "_cpu", None) or getattr(core, "core", None) or core
        m.issueWidth    = args.width
        m.numROBEntries = args.rob
        m.LQEntries     = args.lq
        m.SQEntries     = args.sq

# Create board with the processor, memory and cache hierarchy.
board = SimpleBoard(
    clk_freq="3GHz", processor=processor, memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# Set the workload to run the benchmark
board.set_workload(obtain_resource("x86-npb-is-size-s-run"))

# Create a simulator with the board and run it.
simulator = Simulator(board=board)
simulator.run()