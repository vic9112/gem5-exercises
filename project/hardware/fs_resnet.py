#////////////////////////////////////////////////////////
# Design: GEM5 Project
# Author: Kuan-Hsi(Vic) Chen
# Email : s179038@gmail.com
#////////////////////////////////////////////////////////

from gem5.coherence_protocol import CoherenceProtocol
from gem5.components.boards.x86_board import X86Board
from gem5.components.memory.single_channel import SingleChannelDDR4_2400
from gem5.components.memory.multi_channel import DualChannelDDR4_2400
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.resources.resource import KernelResource, DiskImageResource
from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator
from gem5.utils.requires import requires
import m5
from m5.objects import Root
from m5.util import convert

requires(
    isa_required=ISA.X86,
    kvm_required=True,
)

import argparse
from component.hierarchy import PrivateL1SharedL2CacheHierarchy
from component.factories import kvm_core_factory_x86, o3_core_factory_x86
from component.custom_switch_processor import FactorySwitchableProcessor
from component.cost_models import cpu_cost, cache_cost, memory_cost, network_cost

ap = argparse.ArgumentParser()
ap.add_argument("--num_cores", type=int, default=4)   # 1 <= cores <= 16
ap.add_argument("--capacity" , type=int, default=2)   # in GB
ap.add_argument("--channels" , type=int, default=2)   # 1 <= channels <= 4
ap.add_argument("--l1-size"  , type=int, default=512) # in KB
ap.add_argument("--l1-assoc" , type=int, default=8) 
ap.add_argument("--l2-size"  , type=int, default=2)   # in MB
ap.add_argument("--l2-assoc" , type=int, default=16)
ap.add_argument("--width"    , type=int, default=10)  # 1  <= W <= 32
ap.add_argument("--rob_size" , type=int, default=256) # 16 <= R <= 512
ap.add_argument("--int_regs" , type=int, default=256) # 32 <= I <= 512
ap.add_argument("--fp_regs"  , type=int, default=256) # 32 <= F <= 512
ap.add_argument("--sq_lq"    , type=int, default=256) # 16 <= LQ, SQ <= 512
ap.add_argument("--bidir"    , type=bool,default=True) # For RING network!!
args = ap.parse_args()
nrouters = (2 * args.num_cores) + 2 + (args.channels)  # (L1i + L1d) + L2 + MEM
if args.bidir:
    print("=> RING Network: Bidirectional")
    nlinks = 2 * nrouters
else:
    print("=> RING Network: Unidirectional")
    nlinks = nrouters

cpu_cost = cpu_cost(args.width, args.rob_size, args.int_regs, args.fp_regs, args.num_cores, args.sq_lq)
cache_cost = cache_cost(args.l1_size, args.l2_size)
memory_cost = memory_cost(args.capacity, args.channels)
network_cost = network_cost(nrouters, nlinks)

total_cost = cpu_cost + cache_cost + memory_cost + network_cost

# Output the total cost
print(f"Total cost of configuration: {total_cost} units")

# Setup the Ruby cache hierarchy with ring topology
cache_hierarchy = PrivateL1SharedL2CacheHierarchy(
    l1_size=f"{args.l1_size}KiB", l1_assoc=args.l1_assoc,
    l2_size=f"{args.l2_size}MiB", l2_assoc=args.l2_assoc
)

if args.channels == 1:
    memory = SingleChannelDDR4_2400(size=f"{args.capacity}GB")
else:
    memory = DualChannelDDR4_2400(size=f"{args.capacity}GB")

processor = FactorySwitchableProcessor(
    start_core_factory=kvm_core_factory_x86(ISA.X86),
    switch_core_factory=o3_core_factory_x86(
        ISA.X86, 
        width=args.width, 
        rob=args.rob_size, 
        n_int=args.int_regs, 
        n_fp=args.fp_regs,
        lq=args.sq_lq,
        sq=args.sq_lq
    ),
    num_cores=args.num_cores,
    isa=ISA.X86,
    starting_core_type_for_memmode=CPUTypes.KVM,
)

for c in processor.get_cores():
    c.core.usePerf = False

# The X86Board allows for Full-System X86 simulations.
board = X86Board(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

kernel = KernelResource(local_path="binaries/vmlinux-4.4.186")
disk   = DiskImageResource(local_path="disks/parsec.img", root_partition="1")

core_id = args.num_cores - 1

rcs = f"""
echo "[rcS] Boot done → request CPU switch (KVM→TIMING)"
M5=$(command -v m5 || echo /sbin/m5)
$M5 exit

echo "[rcS] Now in TIMING, reset stats and run workload"
$M5 resetstats
taskset -c 0-{core_id} ./resnet_mt --channels 16 --size 8 --blocks 4 --threads {args.num_cores}
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

#============ Prevent simQuantim=0 for multi-thread =============#
TICKS_PER_SEC = 1_000_000_000_000  # 1 THz (gem5 default global frequency)

def to_ticks(s: str) -> int:
    s = s.strip().lower()
    if s.endswith("ns"): return int(float(s[:-2]) * TICKS_PER_SEC * 1e-9)
    if s.endswith("us"): return int(float(s[:-2]) * TICKS_PER_SEC * 1e-6)
    if s.endswith("ms"): return int(float(s[:-2]) * TICKS_PER_SEC * 1e-3)
    if s.endswith("s"):  return int(float(s[:-1])  * TICKS_PER_SEC)
    return int(s)  # suppor integer ticks

Root.sim_quantum = to_ticks("1ms")   # "100us"/"1us"
print("[dbg] preset Root.sim_quantum (ticks) =", Root.sim_quantum)
#================================================================#

sim = Simulator(
    board=board,
    on_exit_event={
        ExitEvent.EXIT: exit_event_handler(),
    },
)
sim.run()
