"""
Problem 5 — FS mode: x86 Ubuntu boots and runs NPB IS (size S) with ROI markers.
We use the same CPU model you choose for SE (via --cpu timing|o3).

Assumed ROI pattern in the resource:
  - 1st m5 exit: ROI begin  -> dump+reset, continue
  - 2nd m5 exit: ROI end    -> stop

If your image emits a boot marker before ROI begin, add a --has-boot-exit flag and
shift the handler (not needed for the provided resource).
"""

import argparse
from gem5.utils.requires import requires
from gem5.isas import ISA

from gem5.components.cachehierarchies.classic.private_l1_private_l2_walk_cache_hierarchy import \
    PrivateL1PrivateL2WalkCacheHierarchy
from gem5.components.boards.x86_board import X86Board
from gem5.components.memory.single_channel import SingleChannelDDR4_2400
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.processors.cpu_types import CPUTypes
from gem5.resources.resource import obtain_resource
from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator
from m5 import stats as m5stats

ap = argparse.ArgumentParser("Problem 5 FS mode with ROI")
ap.add_argument("--cpu", choices=["timing","o3"], default="timing", help="CPU model (same as SE)")
ap.add_argument("--cores", type=int, default=1)
args = ap.parse_args()

cpu_type = CPUTypes.TIMING if args.cpu == "timing" else CPUTypes.O3

cache_hierarchy = PrivateL1PrivateL2WalkCacheHierarchy(
    l1d_size="16kB", l1i_size="16kB", l2_size="256kB"
)
memory    = SingleChannelDDR4_2400(size="2GiB")
processor = SimpleProcessor(cpu_type=cpu_type, isa=ISA.X86, num_cores=args.cores)

board = X86Board(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# FS image with ROI hypercalls that run IS size S
workload = obtain_resource("x86-ubuntu-24.04-npb-is-s", resource_version="1.0.0")
board.set_workload(workload)

def roi_handler():
    print("ROI begin (1st exit): dump+reset stats")
    m5stats.dump()
    m5stats.reset()
    yield False
    print("ROI end (2nd exit): stopping simulation")
    yield True

sim = Simulator(
    board=board,
    on_exit_event={ExitEvent.EXIT: roi_handler()},
)
sim.run()
