"""
Design: Ring topology for the Ruby network.
Modify by KUAN-HSI(Vic), CHEN (s179038@gmail.com)
  - Add bidirectional ring option
  - Automatically connect routers in a ring
"""

from m5.objects import (
    SimpleExtLink,
    SimpleIntLink,
    SimpleNetwork,
    Switch,
)

class Ring(SimpleNetwork):
    def __init__(self, ruby_system):
        super().__init__()
        self.netifs = [] # Used for garnet
        self.ruby_system = ruby_system

    def connectControllers(
        self, l1i_ctrls, l1d_ctrls, l2_ctrls, mem_ctrls, dma_ctrls
    ):
        nL1i = len(l1i_ctrls)
        nL1d = len(l1d_ctrls)
        nL2  = len(l2_ctrls)
        nMem = len(mem_ctrls)
        print("===============================")
        print("Build RING Network...")
        print("Get L1:  " + str(nL1i))
        print("Get L2:  " + str(nL2))
        print("Get MEM: " + str(nMem))
        print("===============================")
        bidirectional = True

        # Create routers
        self.l1_routers  = [Switch(router_id=i)          for i in range(nL1i)]
        self.l2_routers  = [Switch(router_id=nL1i+i)     for i in range(nL2) ]
        self.mem_routers = [Switch(router_id=nL1i+nL2+i) for i in range(nMem)]

        # Create external links
        lid = 0
        self.l1i_ext_links = [
            SimpleExtLink(link_id=lid+i, ext_node=c, int_node=self.l1_routers[i])
            for i, c in enumerate(l1i_ctrls)
        ]
        lid += nL1i
        self.l1d_ext_links = [
            SimpleExtLink(link_id=lid+i, ext_node=c, int_node=self.l1_routers[i])
            for i, c in enumerate(l1d_ctrls)
        ]
        lid += nL1d
        self.l2_ext_links = [
            SimpleExtLink(link_id=lid+i, ext_node=c, int_node=self.l2_routers[i])
            for i, c in enumerate(l2_ctrls)
        ]
        lid += nL2
        self.mem_ext_links = [
            SimpleExtLink(link_id=lid+i, ext_node=c, int_node=self.mem_routers[i])
            for i, c in enumerate(mem_ctrls)
        ]
        lid += nMem
        if dma_ctrls:
            self.dma_ext_links = [
                SimpleExtLink(
                    link_id=lid+i, ext_node=c, int_node=self.mem_routers[0]
                )
                for i, c in enumerate(dma_ctrls)
            ]

        # Create internal links to form a ring topology
        # Placement: L1 - Mem - L2 - L1 - L1 - Mem - L2 - L1
        def place_nodes(l1, mem, l2):
            k = max(1, min(len(mem), len(l2))) # number of groups
            q, r = divmod(len(l1), k) # split L1 into k groups
            seq, i = [], 0
            for g in range(k):
                t = q + (g < r)  # number of L1 to place
                seq += l1[i:i+t]; i += t
                if g < len(mem): seq.append(mem[g])
                if g < len(l2):  seq.append(l2[g])
            return seq + l1[i:] + mem[k:] + l2[k:] # concat remaining nodes

        ring_nodes = place_nodes(self.l1_routers, self.mem_routers, self.l2_routers)
        n = len(ring_nodes)

        forward = [SimpleIntLink(link_id=i,
                                 src_node=ring_nodes[i],
                                 dst_node=ring_nodes[(i+1) % n])
                   for i in range(n)]
        if bidirectional:
            reverse = [SimpleIntLink(link_id=n+i,
                                     src_node=ring_nodes[(i+1) % n],
                                     dst_node=ring_nodes[i])
                       for i in range(n)]
            self.int_links = forward + reverse
        else:
            self.int_links = forward

        # Required by SimpleNetwork for some magic behind the scenes
        self.ext_links = (
            self.l1i_ext_links
            + self.l1d_ext_links
            + self.l2_ext_links
            + self.mem_ext_links
            + getattr(self, "dma_ext_links", [])
        )
        self.routers = (
            self.l1_routers
            + self.l2_routers
            + self.mem_routers
        )
