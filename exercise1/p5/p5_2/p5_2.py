"""
Problem 5 - FS mode: x86 Ubuntu boots and runs NPB IS (size S) with ROI markers.
Boots a Linux kernel using KVM, runs a simple workload, and then switches to a 
Timing CPU at work begin and ends at the work end designation.

Refer to : https://github.com/gem5bootcamp/2024/blob/main/materials/archive/isca24/completed/05-fs-npb.py
"""

import argparse
from gem5.utils.requires import requires
from gem5.isas import ISA

from gem5.components.cachehierarchies.classic.private_l1_private_l2_walk_cache_hierarchy import \
    PrivateL1PrivateL2WalkCacheHierarchy
from gem5.components.boards.x86_board import X86Board
from gem5.components.memory.single_channel import SingleChannelDDR4_2400
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.processors.simple_switchable_processor import SimpleSwitchableProcessor
from gem5.components.processors.cpu_types import CPUTypes
from gem5.resources.resource import obtain_resource
from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator
from m5 import stats as m5stats

requires(isa_required=ISA.X86, kvm_required=True) # Since booting with KVM
ap = argparse.ArgumentParser("Problem 5 FS mode with ROI")
ap.add_argument("--cpu", choices=["timing","o3"], default="timing", help="CPU model (same as SE)")
ap.add_argument("--cores", type=int, default=1)
args = ap.parse_args()

detailed_type = CPUTypes.TIMING if args.cpu == "timing" else CPUTypes.O3

cache_hierarchy = PrivateL1PrivateL2WalkCacheHierarchy(
    l1d_size="16kB", l1i_size="16kB", l2_size="256kB"
)
memory = SingleChannelDDR4_2400(size="2GiB")

# This is a switchable CPU. We first boot Ubuntu using KVM, then will exit 
# the simulation by calling "m5 exit".
# Upon exiting from the simulation, the Exit Event handler will switch the
# CPU type to run the ROI.
processor = SimpleSwitchableProcessor(
    starting_core_type=CPUTypes.KVM,
    switch_core_type=detailed_type,
    isa=ISA.X86,
    num_cores=args.cores,
)

for c in processor.get_cores():
    c.core.usePerf = False

board = X86Board(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# FS image with ROI hypercalls that run IS size S
workload = obtain_resource("x86-ubuntu-24.04-npb-is-s", resource_version="1.0.0")
board.set_workload(workload)

def on_exit():
    print("Exiting the simulation for kernel boot")
    yield False
    print("Exiting the simulation for systemd complete")
    yield False

def on_work_begin():
    print("Work begin. Switching to detailed CPU")
    m5stats.reset()
    m5stats.dump()
    processor.switch()
    yield False

def on_work_end():
    print("Work end")
    yield True

sim = Simulator(
    board=board,
    on_exit_event={
        ExitEvent.EXIT: on_exit(),
        ExitEvent.WORKBEGIN: on_work_begin(),
        ExitEvent.WORKEND: on_work_end(),
    },
)

sim.run()