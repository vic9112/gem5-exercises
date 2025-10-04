#!/usr/bin/env python3
"""
Problem 3 (part 3): Compare SimpleMemory vs DDR4 at SAME size/bandwidth,
and allow varying request rate (bandwidth) and read percentage.

Defaults (per assignment spirit): 512 MiB, RandomGenerator, read 80%, 32 GiB/s.

Examples:
  # DDR4 @ 32 GiB/s, 80% reads
  gem5 --outdir=p3/out_cmp_ddr4 p3_3/p3_3.py --mem ddr4

  # SimpleMemory @ 32 GiB/s, 80% reads (device bw matched to generator)
  gem5 --outdir=p3/out_cmp_simple p3_3/p3_3.py --mem simple

  # Sweep parameters by overriding -b and -r
  gem5 --outdir=p3/out_ddr4_b16_r50 p3_3/p3_3.py --mem ddr4 -b 16GiB/s -r 50
  gem5 --outdir=p3/out_simple_b16_r100 p3_3/p3_3.py --mem simple -b 16GiB/s -r 100
"""

import argparse
from m5.objects import MemorySize

from gem5.components.boards.test_board import TestBoard
from gem5.components.memory.single_channel import SingleChannelDDR4_2400
from gem5.components.memory.simple import SingleChannelSimpleMemory
from gem5.components.processors.linear_generator import LinearGenerator
from gem5.components.processors.random_generator import RandomGenerator
from gem5.simulate.simulator import Simulator
from gem5.components.cachehierarchies.classic.no_cache import NoCache


def generator_factory(generator_class: str, rd_perc: int, rate, mem_size: MemorySize):
    if not (0 <= rd_perc <= 100):
        raise ValueError("Read percentage must be 0..100.")
    cls = LinearGenerator if generator_class == "LinearGenerator" else RandomGenerator
    return cls(duration="1ms", rate=rate, max_addr=mem_size, rd_perc=rd_perc)


parser = argparse.ArgumentParser(description="SimpleMemory vs DDR4 (same size/bandwidth).")
parser.add_argument("--mem", choices=["ddr4", "simple"], default="ddr4",
                    help="Memory device to run (default ddr4)")
parser.add_argument("-c", "--generator_class", default="RandomGenerator",
                    help="LinearGenerator or RandomGenerator (default RandomGenerator)")
parser.add_argument("-r", "--read_percentage", type=int, default=80,
                    help="Read ops percentage (default 80)")
parser.add_argument("-b", "--bandwidth", default="32GiB/s",
                    help="Generator request rate (default 32GiB/s)")
parser.add_argument("--size", default="512MiB", help="Memory size (default 512MiB)")

# SimpleMemory device parameters (match device bw to generator unless overridden)
parser.add_argument("--simple-latency", default="50ns", help="SimpleMemory base latency")
parser.add_argument("--simple-latency-var", default="10ns", help="SimpleMemory latency variation")
parser.add_argument("--simple-bw", default=None,
                    help="SimpleMemory device bandwidth (default: match --bandwidth)")

args = parser.parse_args()

# Memory device
if args.mem == "ddr4":
    memory = SingleChannelDDR4_2400(size=args.size)
else:
    dev_bw = args.simple_bw if args.simple_bw is not None else args.bandwidth
    memory = SingleChannelSimpleMemory(size=args.size,
                                       latency=args.simple_latency,
                                       latency_var=args.simple_latency_var,
                                       bandwidth=dev_bw)

# Traffic generator
generator = generator_factory(args.generator_class, args.read_percentage,
                              args.bandwidth, memory.get_size())

# Direct connect (no caches)
board = TestBoard(clk_freq="1GHz", generator=generator, memory=memory, cache_hierarchy=NoCache())

sim = Simulator(board=board)
sim.run()
