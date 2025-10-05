"""
SE mode for x86 NPB IS (size S).
Uses the same CPU model you choose for FS ROI (via --cpu timing|o3).
Do not need to add an ROI handler in SE. The SE workload 
(x86-npb-is-size-s-run) is already just the application; 
gem5 will write one final stats block at program exit, 
which is exactly the ROI. With the parser change above, 
the final block is treated as ROI, so your SE run lines up 
cleanly with the FS ROI block.
"""

import argparse
from gem5.utils.requires import requires
from gem5.isas import ISA

from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.classic.private_l1_private_l2_walk_cache_hierarchy import \
    PrivateL1PrivateL2WalkCacheHierarchy
from gem5.components.memory.single_channel import SingleChannelDDR4_2400
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.processors.cpu_types import CPUTypes
from gem5.resources.resource import obtain_resource
from gem5.simulate.simulator import Simulator

ap = argparse.ArgumentParser("Problem 5 SE mode")
ap.add_argument("--cpu", choices=["timing","o3"], default="timing")
args = ap.parse_args()

cpu_type = CPUTypes.TIMING if args.cpu == "timing" else CPUTypes.O3

cache_hierarchy = PrivateL1PrivateL2WalkCacheHierarchy(
    l1d_size="16kB", l1i_size="16kB", l2_size="256kB"
)

memory = SingleChannelDDR4_2400(size="2GiB")
processor = SimpleProcessor(cpu_type=cpu_type, isa=ISA.X86, num_cores=1)

board = SimpleBoard(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# SE workload (same as Problem 1)
board.set_workload(obtain_resource("x86-npb-is-size-s-run"))

sim = Simulator(board=board)
sim.run()
