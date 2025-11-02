from gem5.coherence_protocol import CoherenceProtocol
from gem5.components.boards.x86_board import X86Board
from gem5.components.memory.single_channel import SingleChannelDDR3_1600
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import (
    SimpleProcessor,
)
from gem5.isas import ISA
from gem5.resources.resource import KernelResource, DiskImageResource
from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator
from gem5.utils.requires import requires
from gem5.components.processors.simple_switchable_processor import ( SimpleSwitchableProcessor, )

requires(
    isa_required=ISA.X86,
    kvm_required=True,
)

from hierarchy import PrivateL1SharedL2CacheHierarchy

# CHI Protocol with Private L1 and Shared L2 Caches.
cache_hierarchy = PrivateL1SharedL2CacheHierarchy(
    l1_size="16KiB", l2_size="256KiB",
    l1_assoc=8, l2_assoc=16,
)

memory = SingleChannelDDR3_1600(size="3GB")

processor = SimpleSwitchableProcessor( 
    starting_core_type=CPUTypes.KVM, 
    switch_core_type=CPUTypes.TIMING, 
    isa=ISA.X86, 
    num_cores=4, # required to be 4 cores
)
for c in processor.get_cores():
    c.core.usePerf = False

# use local kernel / disk image
kernel = KernelResource(local_path="workload/binaries/vmlinux-4.4.186")
disk   = DiskImageResource(local_path="workload/disks/parsec.img", root_partition="1")

board = X86Board(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

rcs = r"""
echo "[rcS] Boot done → request CPU switch (KVM→TIMING)"
M5=$(command -v m5 || echo /sbin/m5)
$M5 exit

echo "[rcS] Now in TIMING, reset stats and run workload"
$M5 resetstats
taskset -c 0-3 ./workload/matmul_mt --size 16 --threads 4
$M5 dumpstats
$M5 exit
"""

board.set_kernel_disk_workload(
    kernel=kernel,
    disk_image=disk,
    readfile_contents=rcs,
    kernel_args=[
        "console=ttyS0",       # force serial console output
        "earlyprintk=ttyS0",   # early boot messages to serial console
        "root=/dev/hda1",      # specify root filesystem partition
    ],
)

def exit_event_handler():
    print("first exit event: Kernel booted, switching CPU")
    processor.switch()
    yield False

    print("second exit event: Done, now exit")
    yield True

simulator = Simulator(
    board=board,
    on_exit_event={
        ExitEvent.EXIT: exit_event_handler(),
    },
)
simulator.run()

