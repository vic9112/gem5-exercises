'''
4. run each SimPoint in gem5.
Refer to github.com/gem5bootcamp/2024/materials/02-Using-gem5/09-sampling/01-simpoint
'''
import argparse
from pathlib import Path

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
import m5

# parse arguments for SimPoints
parser = argparse.ArgumentParser()
parser.add_argument("--sid", type=int, required=True)
args = parser.parse_args()

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

simpoint_info = SimPoint(
    simpoint_interval=1_000_000,
    simpoint_file_path=Path("/workspaces/gem5-exercises/exercise2/p1/log/simpoint_analysis/results.simpts"),
    weight_file_path=Path("/workspaces/gem5-exercises/exercise2/p1/log/simpoint_analysis/results.weights"),
    warmup_interval=1_000_000
)

board.set_se_simpoint_workload(
    obtain_resource("x86-matrix-multiply"),
    simpoint=simpoint_info,
    checkpoint=Path(f"log/simpoint_checkpoint/cpt.SimPoint{args.sid}")
)

def max_inst():
    warmed_up = False
    while True:
        if warmed_up:
            print("end of SimPoint interval")
            yield True
        else:
            print("end of warmup, starting to simulate SimPoint")
            warmed_up = True
            # Schedule a MAX_INSTS exit event during the simulation
            simulator.schedule_max_insts(
                board.get_simpoint().get_simpoint_interval()
            )
            m5.stats.dump()
            m5.stats.reset()
            yield False

simulator = Simulator(
    board=board,
    on_exit_event={ExitEvent.MAX_INSTS: max_inst()},
)

warmup_interval = board.get_simpoint().get_warmup_list()[args.sid]
if warmup_interval == 0:
    warmup_interval = 1
print(f"Starting Simulation with warmup interval {warmup_interval}")
simulator.schedule_max_insts(warmup_interval)
simulator.run()

print("Simulation Done")
print(f"Finish SimPoint {args.sid} with weight {board.get_simpoint().get_weight_list()[args.sid]}")