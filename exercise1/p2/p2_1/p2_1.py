'''
Ruby cache hierarchy
Goal: Evaluate different configurations by varying L2 cache size or L2 associativity.
'''
import argparse

from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.ruby.mesi_two_level_cache_hierarchy import (
    MESITwoLevelCacheHierarchy,
)
from gem5.components.memory.single_channel import SingleChannelDDR4_2400
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.resources.resource import obtain_resource
from gem5.simulate.simulator import Simulator

# Parse arguments
ap = argparse.ArgumentParser()
ap.add_argument("--l2-size", default="256kB", help="L2 size (e.g., 128kB, 256kB, 512kB, 1MB)")
ap.add_argument("--l2-assoc", type=int, default=16, help="L2 associativity")
args = ap.parse_args()

cache_kwargs = dict(
    l1d_size="16kB",
    l1d_assoc=8,
    l1i_size="16kB",
    l1i_assoc=8,
    l2_size=args.l2_size,
    l2_assoc=args.l2_assoc,
    num_l2_banks=1,
)

cache_hierarchy = MESITwoLevelCacheHierarchy(**cache_kwargs)
memory = SingleChannelDDR4_2400()
# With a single L1, the directory never needs to forward a request to another L1, 
# so Fwd_* counters stay zero and many Ruby distributions are simply not emitted.
# Fwd_GETS/GETX happen when one core requests a block that another core currently 
# owns/shares, prompting the directory to forward that request to the peer L1.
processor = SimpleProcessor(cpu_type=CPUTypes.TIMING, isa=ISA.X86, num_cores=1)

board = SimpleBoard(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

board.set_workload(obtain_resource("x86-npb-is-size-s-run"))

sim = Simulator(board=board)
sim.run()

