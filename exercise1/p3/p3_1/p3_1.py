"""
Problem 3 (part 1): Traffic generator -> Single-channel DDR4-2400 (512 MiB).
Defaults match the assignment: RandomGenerator, read 80%, target 32 GiB/s.
"""

import argparse
from m5.objects import MemorySize

from gem5.components.boards.test_board import TestBoard
from gem5.components.memory.single_channel import SingleChannelDDR4_2400
from gem5.components.processors.linear_generator import LinearGenerator
from gem5.components.processors.random_generator import RandomGenerator
from gem5.simulate.simulator import Simulator
from gem5.components.cachehierarchies.classic.no_cache import NoCache

def generator_factory(generator_class: str, rd_perc: int, rate, mem_size: MemorySize):
    if not (0 <= rd_perc <= 100):
        raise ValueError("Read percentage must be 0..100.")
    if generator_class == "LinearGenerator":
        return LinearGenerator(duration="1ms", rate=rate, max_addr=mem_size, rd_perc=rd_perc)
    elif generator_class == "RandomGenerator":
        return RandomGenerator(duration="1ms", rate=rate, max_addr=mem_size, rd_perc=rd_perc)
    else:
        raise ValueError(f"Unknown generator class {generator_class}")

parser = argparse.ArgumentParser(description="Single-channel DDR4-2400 traffic run.")
parser.add_argument("-c", "--generator_class", default="RandomGenerator")
parser.add_argument("-r", "--read_percentage", type=int, default=80)
parser.add_argument("-b", "--bandwidth", default="32GiB/s")
parser.add_argument("--size", default="512MiB")
args = parser.parse_args()

# Memory: single-channel DDR4-2400 (512 MiB by default)
memory = SingleChannelDDR4_2400(size=args.size)

# Traffic generator
generator = generator_factory(args.generator_class, args.read_percentage,
                              args.bandwidth, memory.get_size())

board = TestBoard(clk_freq="1GHz", generator=generator, memory=memory, cache_hierarchy=NoCache())

sim = Simulator(board=board)
sim.run()