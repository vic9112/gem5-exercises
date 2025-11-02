'''
1. Run in SE mode using PrivateL1PrivateL2WalkCacheHierarchy and CPU O3 type.
2. Generate basic block vectors.
Refer to github.com/gem5bootcamp/2024/materials/02-Using-gem5/09-sampling/01-simpoint
'''
from pathlib import Path
from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.classic.private_l1_private_l2_walk_cache_hierarchy import PrivateL1PrivateL2WalkCacheHierarchy
from gem5.components.memory import DualChannelDDR4_2400
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.resources.resource import obtain_resource
from gem5.simulate.simulator import Simulator

cache = PrivateL1PrivateL2WalkCacheHierarchy(l1d_size="16kB", l1i_size="16kB", l2_size="256kB")
mem = DualChannelDDR4_2400(size="3GB")
proc = SimpleProcessor(cpu_type=CPUTypes.ATOMIC, isa=ISA.X86, num_cores=1)
board = SimpleBoard(clk_freq="3GHz", processor=proc, memory=mem, cache_hierarchy=cache)

proc.get_cores()[0].core.addSimPointProbe(1_000_000)  # BBV

board.set_se_binary_workload(obtain_resource("x86-matrix-multiply"))

sim = Simulator(board=board)
sim.run()
print("BBV generation done")