"""
CPU/L3 Power Modeling
Refer to github for L3 power instantiate:
gem5bootcamp/2024/materials/02-Using-gem5/10-modeling-power/test-cache.py
gem5bootcamp/2024/materials/02-Using-gem5/10-modeling-power/completed/three_level.py
"""

import argparse
from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.memory.single_channel import SingleChannelDDR3_1600
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.isas import ISA
from gem5.resources.resource import obtain_resource
from gem5.simulate.simulator import Simulator
from three_level import PrivateL1PrivateL2SharedL3CacheHierarchy
from m5.objects import MathExprPowerModel, PowerModel

# Power Models Definition
class CPUPowerOn(MathExprPowerModel):
    def __init__(self, cpu_path, **kwargs):
        super().__init__(**kwargs)
        # Dynamic power
        self.dyn = (
            "voltage * (4 * {}.ipc + 6 * 0.00001 * "
            "{}.dcache.overallMisses / simSeconds)".format(cpu_path, cpu_path)
        )
        # Static power
        self.st = "4 * temp"

class CPUPowerOff(MathExprPowerModel):
    dyn = "0"
    st = "0"

class CPUPowerModel(PowerModel):
    def __init__(self, cpu_path, **kwargs):
        super().__init__(**kwargs)
        self.pm = [
            CPUPowerOn(cpu_path),   # ON
            CPUPowerOff(),          # CLK_GATED
            CPUPowerOff(),          # SRAM_RETENTION
            CPUPowerOff(),          # OFF
        ]

# Argument parsing for easy configuration
parser = argparse.ArgumentParser(description="Run gem5 with power modeling.")
parser.add_argument("--num_cores", type=int, default=2, help="Number of CPU cores.")
parser.add_argument("--cpu_freq", type=str, default="2GHz", help="CPU clock frequency.")
parser.add_argument("--l3_size", type=str, default="2MiB", help="L3 cache sizes.")
args = parser.parse_args()

# Setup the cache hierarchy
cache_hierarchy=PrivateL1PrivateL2SharedL3CacheHierarchy(
    l1d_size="32KiB",
    l1d_assoc=8,
    l1i_size="32KiB",
    l1i_assoc=8,
    l2_size="256KiB",
    l2_assoc=16,
    l3_size=args.l3_size,
    l3_assoc=32,
)

memory = SingleChannelDDR3_1600(size="2GB")

processor = SimpleProcessor(
    cpu_type=CPUTypes.O3,
    isa=ISA.X86,
    num_cores=args.num_cores,
)

board = SimpleBoard(
    clk_freq=args.cpu_freq,
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

board.set_workload(
    obtain_resource("x86-matrix-multiply-run")
)

# Attaching the Power Models
def setup_cpu_power_model(board: SimpleBoard):
    for i, wrapper in enumerate(board.get_processor().get_cores()):
        cpu = wrapper.core
        cpu_path = cpu.path()
        cpu.power_state.default_state = "ON"##
        cpu.power_model = CPUPowerModel(cpu_path)
        print(f"Attached CPU Power Model to core {i} using path: {cpu_path}")

def setup_l3_power_model(board):
    board.get_cache_hierarchy().add_power_model()
    print(f"Attached L3 Power Model to core")

def _instantiate(simulator):
    from m5.objects import Root
    import m5
    simulator._board._pre_instantiate()

    root = Root(
        full_system=False,
        board=simulator._board,
    )
    
    setup_l3_power_model(simulator._board)

    simulator._root = root
    m5.instantiate()
    simulator._instantiated = True
    simulator._board._post_instantiate()

sim = Simulator(board)
# [VicChen]: should follow this order: cpu -> l3 instantiate
setup_cpu_power_model(board)
_instantiate(sim)
sim.run()

print("Simulation finished!")