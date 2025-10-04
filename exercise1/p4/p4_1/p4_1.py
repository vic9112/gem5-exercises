#!/usr/bin/env python3
"""
p4_1.py — FS X86: KVM fast-forward, switch to detailed CPU at 2nd m5 exit,
stop at 3rd. Stats are dump+reset at the 2nd exit so final stats.txt is ROI-only.

Usage examples:
  # switch to TimingSimpleCPU
  gem5-mesi --outdir=out_p4_1_timing p4_1/p4_1.py --detailed timing
  # switch to X86O3CPU
  gem5-mesi --outdir=out_p4_1_o3     p4_1/p4_1.py --detailed o3
"""

import argparse
from gem5.utils.requires import requires
from gem5.isas import ISA
from gem5.components.processors.cpu_types import CPUTypes

requires(isa_required=ISA.X86, kvm_required=True)

from gem5.components.cachehierarchies.classic.private_l1_private_l2_walk_cache_hierarchy import (
    PrivateL1PrivateL2WalkCacheHierarchy,
)
from gem5.components.boards.x86_board import X86Board
from gem5.components.memory.single_channel import SingleChannelDDR3_1600
from gem5.components.processors.simple_switchable_processor import SimpleSwitchableProcessor
from gem5.resources.resource import obtain_resource
from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator
from m5 import stats as m5stats

ap = argparse.ArgumentParser("Problem 4: KVM → switch at 2nd m5 exit")
ap.add_argument("--detailed", choices=["timing", "o3"], default="o3",
                help="Detailed CPU to switch to after boot (default: o3)")
ap.add_argument("--cores", type=int, default=2, help="core count (default 2)")
args = ap.parse_args()

cache_hierarchy = PrivateL1PrivateL2WalkCacheHierarchy(
    l1d_size="16kB", l1i_size="16kB", l2_size="256kB"
)

# Memory
memory = SingleChannelDDR3_1600(size="3GB")

# Pick detailed target
switch_to = CPUTypes.O3 if args.detailed == "o3" else CPUTypes.TIMING

# Start with KVM, declare what we'll switch to
processor = SimpleSwitchableProcessor(
    starting_core_type=CPUTypes.KVM,
    switch_core_type=switch_to,
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

workload = obtain_resource("x86-ubuntu-24.04-boot-with-systemd", resource_version="1.0.0")
board.set_workload(workload)

def exit_handler():
    print("first exit event: Kernel booted")
    yield False

    print("--> 2nd exit event: After boot (dump+reset stats, switch CPU)")
    m5stats.dump()
    m5stats.reset()

    print(f"--> Switching CPUs: KVM -> {args.detailed.upper()}")
    processor.switch()     # <— SimpleSwitchableProcessor
    yield False

    print("--> 3rd exit event: After run script (ROI end)")
    yield True

simulator = Simulator(
    board=board,
    on_exit_event={ExitEvent.EXIT: exit_handler()},
)
simulator.run()
