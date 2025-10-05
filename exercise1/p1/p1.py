"""
Goal: Run x86-npb-is-size-s-run using X86 ISA as the benchmark.
Step:
- Compare both TimingSimpleCPU and X86O3CPU models to observe the 
  differences between a simple in-order core and out-of-order core.
- Experiment with key micro-architecture parameters for O3CPU. EX:
  - issueWidth (e.g., 2 vs 6)
  - numROBEntries (e.g., 64 vs 192)
  - LQEntries and SQEntries (load/store queue depth, e.g., 16 vs 64), 
    varied separately

Reference: https://github.com/gem5bootcamp/2024/blob/main/materials/02-Using-gem5/01-stdlib/completed/02-processor.py
"""

import argparse

from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.ruby.mesi_two_level_cache_hierarchy import (
    MESITwoLevelCacheHierarchy,
)
from gem5.components.memory.single_channel import SingleChannelDDR4_2400
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.processors.cpu_types import CPUTypes

# Bootcamp-style custom OOO processor built from X86O3CPU
from gem5.components.processors.base_cpu_core import BaseCPUCore
from gem5.components.processors.base_cpu_processor import BaseCPUProcessor
from m5.objects import X86O3CPU, TournamentBP

from gem5.isas import ISA
from gem5.resources.resource import obtain_resource
from gem5.simulate.simulator import Simulator

class MyOutOfOrderCore(BaseCPUCore):
    def __init__(self, width: int, rob_size: int, lq: int, sq: int):
        super().__init__(X86O3CPU(), ISA.X86)

        self.core.issueWidth    = width
        self.core.numROBEntries = rob_size
        self.core.LQEntries     = lq
        self.core.SQEntries     = sq

        # Keep a small stability cushion for Ruby + O3
        self.core.forwardComSize = 20
        self.core.backComSize    = 20

        self.core.branchPred = TournamentBP()

class MyOutOfOrderProcessor(BaseCPUProcessor):
    def __init__(self, cores: int, width: int, rob_size: int, lq: int, sq: int):
        super().__init__([
            MyOutOfOrderCore(width=width, rob_size=rob_size, lq=lq, sq=sq)
            for _ in range(cores)
        ])

ap = argparse.ArgumentParser()
ap.add_argument("--cpu", choices=["timing", "o3"], required=True)
ap.add_argument("--cores", type=int, default=1)
# vary one at a time
ap.add_argument("--width", type=int, default=4,   help="issue width (O3)")
ap.add_argument("--rob",   type=int, default=128, help="numROBEntries (O3)")
ap.add_argument("--lq",    type=int, default=64,  help="LQEntries (O3)")
ap.add_argument("--sq",    type=int, default=64,  help="SQEntries (O3)")
args = ap.parse_args()

cache_hierarchy = MESITwoLevelCacheHierarchy(
    l1d_size="16kB", l1d_assoc=8,
    l1i_size="16kB", l1i_assoc=8,
    l2_size="256kB", l2_assoc=16,
    num_l2_banks=1,
)

# Memory
memory = SingleChannelDDR4_2400()

# CPU / Processor
if args.cpu == "timing":
    processor = SimpleProcessor(cpu_type=CPUTypes.TIMING, isa=ISA.X86, num_cores=args.cores)
    print("===== Use Simple Processor =====")
else:
    processor = MyOutOfOrderProcessor(
        cores=args.cores, width=args.width, rob_size=args.rob, lq=args.lq, sq=args.sq
    )
    print("===== Use X86O3CPU =====")

board = SimpleBoard(
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
    clk_freq="3GHz",
)

# Workload: X86 NPB IS
board.set_workload(obtain_resource("x86-npb-is-size-s-run"))

# Run
simulator = Simulator(board=board)
simulator.run()
