# Cost model functions for various hardware components

def cpu_cost(width, rob_size, int_regs, fp_regs, num_cores, sq_lq):
    W = (width + width + width + width + width + width) / 6
    score = (10 * W + 12 * (rob_size / 16) + 8 * (int_regs / 32) + 8 * (fp_regs / 32) +
             6 * ((sq_lq + sq_lq) / 64) + 2 * (width + width))
    CLSQ = 0.05 * max(0, (sq_lq - 32) + (sq_lq - 32))
    CO3_per_core = 40 + (0.01 * score) + 9.6 + CLSQ
    total_cost = num_cores * CO3_per_core
    return total_cost

def cache_cost(l1_size, l2_size, l3_size=0):
    l1_cost = 3 * (l1_size // 16)
    l2_cost = ((l2_size * 1024) // 16)
    l3_cost = (l3_size // 64)
    return l1_cost + l2_cost + l3_cost

def memory_cost(capacity, channel=2):
    ''' DDR4_2400 cost model '''
    cost = 60 * channel
    frequency_cost = 5 * max(0, (2400 - 1600) // 400) * channel
    capacity_cost = 10 * capacity  # GB
    return cost + frequency_cost + capacity_cost

def network_cost(nrouters, nlinks):
    return 10 * nrouters + 5 * nlinks

# Example usage:
#cpu_cost = cpu_cost(width=4, rob_size=128, int_regs=64, fp_regs=64, num_cores=8, sq_lq=64)
#cache_cost = cache_cost(l1_size=32, l1_assoc=8, l2_size=256, l2_assoc=8)
#memory_cost = memory_cost(capacity=16)  # in GB
#network_cost = network_cost(nrouters=16, nlinks=32) 