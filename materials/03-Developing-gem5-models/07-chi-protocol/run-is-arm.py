"""
Run script for the IS-A benchmark (ARM + KVM).

This script runs the IS-A benchmark on a gem5 simulator with the CHI hierarchy
defined in `hierarchy.py`. This version is for ARM hosts, leveraging KVM for
fast boot and switching to a Timing model for detailed execution.

To run this script:
> gem5 run-is-arm.py
"""

from gem5.components.memory.single_channel import SingleChannelDDR4_2400
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_switchable_processor import (
    SimpleSwitchableProcessor,
)
from gem5.isas import ISA
from gem5.resources.resource import obtain_resource
from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator

import m5

# FILL THIS IN
# cache_hierarchy = ...

memory = SingleChannelDDR4_2400(size="3GiB")

def get_arm_board(cache_hierarchy, memory):
    from gem5.components.boards.simple_board import SimpleBoard

    # Switchable ARM processor: start with KVM, then switch to Timing
    processor = SimpleSwitchableProcessor(
        starting_core_type=CPUTypes.KVM,
        switch_core_type=CPUTypes.TIMING,
        isa=ISA.ARM,
        num_cores=4,
    )

    # KVM core on ARM doesn’t need perf
    for proc in processor.start:
        proc.core.usePerf = False

    board = SimpleBoard(
        clk_freq="3GHz",
        processor=processor,
        memory=memory,
        cache_hierarchy=cache_hierarchy,
    )

    # ARM workload (NPB IS)
    board.set_workload(obtain_resource("arm-ubuntu-24.04-npb-is-a", resource_version="2.0.0"))
    return board

def get_x86_board(cache_hierarchy, memory):
    from gem5.components.boards.simple_board import SimpleBoard
    from gem5.components.processors.simple_processor import SimpleProcessor
    processor = SimpleProcessor(
        cpu_type=CPUTypes.TIMING,
        num_cores=4,
        isa=ISA.X86,
    )
    board = SimpleBoard(
        clk_freq="3GHz",
        processor=processor,
        memory=memory,
        cache_hierarchy=cache_hierarchy,
    )
    board.set_workload(obtain_resource("x86-npb-is-size-s"))
    return board

# board = get_arm_board(cache_hierarchy, memory)
board = get_arm_board(cache_hierarchy, memory)
processor = board.processor

def on_exit():
    print("Exiting the simulation for kernel boot (ARM/KVM)")
    yield False
    print("Exiting the simulation for systemd complete (ARM/KVM)")
    yield False

def on_work_begin():
    print("Work begin. Switching to detailed CPU")
    m5.stats.reset()
    processor.switch()
    print("Running for 10,000,000 instructions (on one thread)")
    simulator.schedule_max_insts(10_000_000)
    yield False

def on_work_end():
    print("Work end")
    yield True

simulator = Simulator(
    board=board,
    on_exit_event={
        ExitEvent.EXIT: on_exit(),
        ExitEvent.WORKBEGIN: on_work_begin(),
        ExitEvent.WORKEND: on_work_end(),
    },
)

simulator.run()
