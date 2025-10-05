"""
FS X86: KVM only, no CPU switch.
Still dump+reset at the 2nd m5 exit so the final stats are ROI-only,
and exit on the 3rd m5 exit.
"""

from gem5.utils.requires import requires
from gem5.isas import ISA
from gem5.components.processors.cpu_types import CPUTypes

# Ensure X86 + KVM host support
requires(isa_required=ISA.X86, kvm_required=True)

from gem5.components.cachehierarchies.classic.private_l1_private_l2_walk_cache_hierarchy import (
    PrivateL1PrivateL2WalkCacheHierarchy,
)
from gem5.components.boards.x86_board import X86Board
from gem5.components.memory.single_channel import SingleChannelDDR3_1600
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.resources.resource import obtain_resource
from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator
from m5 import stats as m5stats

cache_hierarchy = PrivateL1PrivateL2WalkCacheHierarchy(
    l1d_size="16kB", l1i_size="16kB", l2_size="256kB"
)
memory = SingleChannelDDR3_1600(size="3GB")

processor = SimpleProcessor(cpu_type=CPUTypes.KVM, isa=ISA.X86, num_cores=2)

for c in processor.get_cores():
    c.core.usePerf = False

board = X86Board(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

workload = obtain_resource("x86-ubuntu-24.04-boot-with-systemd", resource_version="1.0.0")
board.set_workload(workload)

def exit_handler():
    print("--> 1st exit event: Kernel booted")
    yield False

    print("--> 2nd exit event: After boot (dump+reset stats, continue KVM)")
    m5stats.dump()
    m5stats.reset()
    # No switch here — keep KVM
    yield False

    print("--> 3rd exit event: After run script (ROI end)")
    yield True

simulator = Simulator(
    board=board,
    on_exit_event={ExitEvent.EXIT: exit_handler()},
)
simulator.run()
