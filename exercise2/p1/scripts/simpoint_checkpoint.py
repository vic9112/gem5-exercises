'''
3. Use SimPoint to identify representative regions and weights.
4. Generate checkpoints
Refer to github.com/gem5bootcamp/2024/materials/02-Using-gem5/09-sampling/01-simpoint
'''

from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.classic.private_l1_private_l2_walk_cache_hierarchy import (
    PrivateL1PrivateL2WalkCacheHierarchy,
)
from gem5.components.memory import DualChannelDDR4_2400
from gem5.simulate.exit_event import ExitEvent
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.isas import ISA
from gem5.simulate.exit_event_generators import simpoints_save_checkpoint_generator
from gem5.utils.simpoint import SimPoint
from gem5.resources.resource import obtain_resource
from gem5.simulate.simulator import Simulator
from pathlib import Path

cache_hierarchy = PrivateL1PrivateL2WalkCacheHierarchy(
    l1d_size="16kB",
    l1i_size="16kB",
    l2_size="256kB",
)

memory = DualChannelDDR4_2400(size="3GB")

processor = SimpleProcessor(
    cpu_type=CPUTypes.O3,
    isa=ISA.X86,
    num_cores=1,
)

board = SimpleBoard(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# Use SimPoint to identify representative regions and weights
simpoint_info = SimPoint(
    simpoint_interval=1_000_000,
    simpoint_file_path=Path("/workspaces/gem5-exercises/exercise2/p1/log/simpoint_analysis/results.simpts"),
    weight_file_path=Path("/workspaces/gem5-exercises/exercise2/p1/log/simpoint_analysis/results.weights"),
    warmup_interval=1_000_000
)

board.set_se_simpoint_workload(
    obtain_resource("x86-matrix-multiply"),
    simpoint=simpoint_info
)

dir = Path("/workspaces/gem5-exercises/exercise2/p1/log/simpoint_checkpoint")

# Generate checkpoints and run each SimPoint in gem5.
simulator = Simulator(
    board=board,
    on_exit_event={
        # using the SimPoints event generator in the standard library to take checkpoints
        ExitEvent.SIMPOINT_BEGIN: simpoints_save_checkpoint_generator(dir, simpoint_info)
    },
)

simulator.run()

print("Simulation Done")