---
marp: true
paginate: true
theme: gem5
title: gem5 tutorial
---

<!-- _class: title -->

## gem5 tutorial

References:

- https://github.com/gem5bootcamp

---

## Environment

The steps outlined in this slide deck have been tested on the computers located in Delta 219.
These computers are equipped with:

- CPU: 13th Gen Intel(R) Core(TM) i5-13500
- RAM: 16 GB
- SSD: 954 GB

Docker Desktop is pre-installed:

- https://docs.docker.com/

---

## Back up files from $HOME\workspaces\ to a flash drive

Delta 219 computers are configured to automatically revert to a previously saved system state (a restore point) without prior notice.

- Your files may be permanently deleted without warning at any time (unannounced data loss).
- You cannot predict when these reverts will occur, nor can you prevent them from happening (limited user control).

**Temporary data storage**:
Your files are temporarily stored in the `$HOME\workspaces\` directory; however, these files are deleted during the automatic system revert process.

**Protecting your data**:
To avoid data loss, regularly back up your data using external USB drives or cloud storage services.

**Reason for automatic system reverts**:
This feature is designed to maintain a consistent simulation environment for all users.

---

## Open Docker Desktop on Windows

For Windows users:

1. Left-click on the **Start button** (or press the [`Windows key`](https://en.wikipedia.org/wiki/Windows_key)).

1. Select **Docker Desktop** (or type `Docker Desktop` and press `Enter`).

1. Expected outcome: Docker Desktop will open.

---

## Open a terminal emulator on Windows

For Windows users:

1. Right-click on the **Start button** (or press the [`Windows key`](https://en.wikipedia.org/wiki/Windows_key) + `X`).

1. Select **Windows PowerShell** (or press `I`).

1. Expected outcome: A terminal emulator will open.

```sh
Windows PowerShell
Copyright (C) Microsoft Corporation. 著作權所有，並保留一切權利。

請嘗試新的跨平台 PowerShell https://aka.ms/pscore6

PS C:\Users\user>
```

---

<!-- _class: two-col -->

## Run a container in PowerShell

For PowerShell users, run this command:

```sh
docker container run `
--rm --interactive --tty `
--volume $HOME\workspaces\:/workspaces/ `
--workdir /workspaces/2024/ `
--hostname codespaces-ae14be `
ghcr.io/gem5/devcontainer:bootcamp-2024
```

Expected outcome: An interactive TTY will indicate its readiness to accept commands.

```sh
root@codespaces-ae14be:/workspaces/2024#
```

Alternative outcome: A newer image will be downloaded before the interactive TTY prints the username, hostname, and working directory.

```sh
PS C:\Users\user> docker container run `
>> --rm --interactive --tty `
>> --volume $HOME\workspaces\:/workspaces/ `
>> --workdir /workspaces/2024/ `
>> --hostname codespaces-ae14be `
>> ghcr.io/gem5/devcontainer:bootcamp-2024
Unable to find image 'ghcr.io/gem5/devcontainer:bootcamp-2024' locally
bootcamp-2024: Pulling from gem5/devcontainer
00d679a470c4: Pull complete
c782a11a41b6: Pull complete
4f6b9996da3d: Pull complete
bb60cbcef558: Pull complete
92c0abbbf0ee: Pull complete
865d1839a002: Pull complete
2ceb23f2c7bb: Pull complete
31825ae2d134: Pull complete
Digest: sha256:dc299b8bf11b324cbd89aab82bdbe31bf9ce71a33386f2a2153a590a803d2c71
Status: Downloaded newer image for ghcr.io/gem5/devcontainer:bootcamp-2024
root@codespaces-ae14be:/workspaces/2024#
```

---

## Get the source code of gem5

Run this command:

```sh
time git clone --recurse-submodules \
https://gitlab.larc-nthu.net/ee6455/public-gem5bootcamp-2024 /workspaces/2024/
```

Expected outcome: A repository will be cloned, including its submodules.

```sh
root@codespaces-ae14be:/workspaces/2024# time git clone --recurse-submodules \
> https://gitlab.larc-nthu.net/ee6455/public-gem5bootcamp-2024 /workspaces/2024/
Cloning into '/workspaces/2024'...
warning: redirecting to https://gitlab.larc-nthu.net/ee6455/public-gem5bootcamp-2024.git/
remote: Enumerating objects: 10982, done.
remote: Counting objects: 100% (6/6), done.
remote: Compressing objects: 100% (6/6), done.
remote: Total 10982 (delta 0), reused 0 (delta 0), pack-reused 10976
Receiving objects: 100% (10982/10982), 378.29 MiB | 28.30 MiB/s, done.
Resolving deltas: 100% (7432/7432), done.
Updating files: 100% (952/952), done.
Submodule 'gem5' (https://github.com/gem5/gem5) registered for path 'gem5'
Submodule 'gem5-resources' (https://github.com/gem5/gem5-resources) registered for path 'gem5-resources'
Cloning into '/workspaces/2024/gem5'...
remote: Enumerating objects: 284540, done.
remote: Counting objects: 100% (1403/1403), done.
remote: Compressing objects: 100% (741/741), done.
remote: Total 284540 (delta 909), reused 963 (delta 641), pack-reused 283137 (from 1)
Receiving objects: 100% (284540/284540), 263.01 MiB | 22.75 MiB/s, done.
Resolving deltas: 100% (163364/163364), done.
Cloning into '/workspaces/2024/gem5-resources'...
remote: Enumerating objects: 24775, done.
remote: Counting objects: 100% (617/617), done.
remote: Compressing objects: 100% (248/248), done.
remote: Total 24775 (delta 469), reused 369 (delta 369), pack-reused 24158 (from 1)
Receiving objects: 100% (24775/24775), 48.15 MiB | 14.22 MiB/s, done.
Resolving deltas: 100% (10877/10877), done.
Submodule path 'gem5': checked out 'bb418d41eb6d87c0a0591869097005c16420c6aa'
Submodule path 'gem5-resources': checked out '6734bb4940dd90f3b7c0349eedeefcf3ee405938'

real    3m39.695s
user    0m32.154s
sys     0m14.243s
root@codespaces-ae14be:/workspaces/2024#
```

---

## Run a simulation using gem5

Run this command:

```sh
time gem5-mesi --outdir=/workspaces/m5out/ \
/workspaces/2024/materials/01-Introduction/02-getting-started/completed/basic.py
```

Expected outcome: The `X86DemoBoard` will be simulated using `x86-ubuntu-24.04-img` as a workload.

```sh
root@codespaces-ae14be:/workspaces/2024# time gem5-mesi --outdir=/workspaces/m5out/ \
> /workspaces/2024/materials/01-Introduction/02-getting-started/completed/basic.py
gem5 Simulator System.  https://www.gem5.org
gem5 is copyrighted software; use the --copyright option for details.

gem5 version 24.0.0.0
gem5 compiled Jul 25 2024 18:47:27
gem5 started Sep  8 2024 12:45:46
gem5 executing on codespaces-ae14be, pid 13
command line: gem5-mesi --outdir=/workspaces/m5out/ /workspaces/2024/materials/01-Introduction/02-getting-started/completed/basic.py

warn: The X86DemoBoard is solely for demonstration purposes. This board is not known to be be representative of any real-world system. Use with caution.
info: Using default config
Resource 'x86-linux-kernel-5.4.0-105-generic' was not found locally. Downloading to '/root/.cache/gem5/x86-linux-kernel-5.4.0-105-generic'...
Finished downloading resource 'x86-linux-kernel-5.4.0-105-generic'.
Resource 'x86-ubuntu-24.04-img' was not found locally. Downloading to '/root/.cache/gem5/x86-ubuntu-24.04-img.gz'...
Finished downloading resource 'x86-ubuntu-24.04-img'.
Decompressing resource 'x86-ubuntu-24.04-img' ('/root/.cache/gem5/x86-ubuntu-24.04-img.gz')...
Finished decompressing resource 'x86-ubuntu-24.04-img'.
warn: Max ticks has already been set prior to setting it through the run call. In these cases the max ticks set through the `run` function is used
Global frequency set at 1000000000000 ticks per second
src/mem/dram_interface.cc:690: warn: DRAM device capacity (8192 Mbytes) does not match the address range assigned (2048 Mbytes)
src/sim/kernel_workload.cc:46: info: kernel located at: /root/.cache/gem5/x86-linux-kernel-5.4.0-105-generic
src/base/statistics.hh:279: warn: One of the stats is a legacy stat. Legacy stat is a stat that does not belong to any statistics::Group. Legacy stat is deprecated.
      0: board.pc.south_bridge.cmos.rtc: Real-time clock set to Sun Jan  1 00:00:00 2012
board.pc.com_1.device: Listening for connections on port 3456
src/base/statistics.hh:279: warn: One of the stats is a legacy stat. Legacy stat is a stat that does not belong to any statistics::Group. Legacy stat is deprecated.
src/dev/intel_8254_timer.cc:128: warn: Reading current count from inactive timer.
board.remote_gdb: Listening for connections on port 7000
src/sim/simulate.cc:199: info: Entering event queue @ 0.  Starting simulation...
src/mem/ruby/system/Sequencer.cc:680: warn: Replacement policy updates recently became the responsibility of SLICC state machines. Make sure to setMRU() near callbacks in .sm files!
build/ALL/arch/x86/generated/exec-ns.cc.inc:27: warn: instruction 'fninit' unimplemented

real    1m57.553s
user    0m39.148s
sys     0m11.054s
root@codespaces-ae14be:/workspaces/2024#
```

---

## Retrieve the simulation statistics on Windows

For Windows users, open `$HOME\workspaces\m5out\stats.txt` using a text editor.

Expected outcome: The first few lines will resemble this:

```sh
---------- Begin Simulation Statistics ----------
simSeconds                                   0.020000                       # Number of seconds simulated (Second)
simTicks                                  20000000000                       # Number of ticks simulated (Tick)
finalTick                                 20000000000                       # Number of ticks from beginning of simulation (restored from checkpoints and never reset) (Tick)
simFreq                                  1000000000000                       # The number of ticks per simulated second ((Tick/Second))
hostSeconds                                     18.88                       # Real time elapsed on the host (Second)
hostTickRate                               1059100397                       # The number of ticks simulated per host second (ticks/s) ((Tick/Second))
hostMemory                                    2770924                       # Number of bytes of host memory used (Byte)
simInsts                                      7479814                       # Number of instructions simulated (Count)
simOps                                       34912342                       # Number of ops (including micro ops) simulated (Count)
hostInstRate                                   396059                       # Simulator instruction rate (inst/s) ((Count/Second))
hostOpRate                                    1848597                       # Simulator op (including micro ops) rate (op/s) ((Count/Second))
board.cache_hierarchy.ruby_system.delayHistogram::bucket_size            2                       # delay histogram for all message (Unspecified)
board.cache_hierarchy.ruby_system.delayHistogram::max_bucket           19                       # delay histogram for all message (Unspecified)
board.cache_hierarchy.ruby_system.delayHistogram::samples       735551                       # delay histogram for all message (Unspecified)
board.cache_hierarchy.ruby_system.delayHistogram::mean     1.036855                       # delay histogram for all message (Unspecified)
board.cache_hierarchy.ruby_system.delayHistogram::stdev     2.687016                       # delay histogram for all message (Unspecified)
```

---

## Retrieve the simulation configuration on Windows

For Windows users, open `$HOME\workspaces\m5out\config.ini` using a text editor.

Expected outcome: The first few lines will resemble this:

```sh
[board]
type=System
children=cache_hierarchy clk_domain dvfs_handler iobus memory pc processor workload
auto_unlink_shared_backstore=false
cache_line_size=64
eventq_index=0
exit_on_work_items=true
init_param=0
m5ops_base=4294901760
mem_mode=timing
mem_ranges=0:2147483648 3221225472:3222274048
memories=board.memory.mem_ctrl.dram
mmap_using_noreserve=false
multi_thread=false
num_work_ids=16
readfile=
redirect_paths=
shadow_rom_ranges=
shared_backstore=
symbolfile=
thermal_components=
thermal_model=Null
work_begin_ckpt_count=0
work_begin_cpu_id_exit=-1
work_begin_exit_count=0
work_cpus_ckpt_count=0
work_end_ckpt_count=0
work_end_exit_count=0
work_item_id=-1
workload=board.workload
system_port=board.cache_hierarchy.ruby_system.sys_port_proxy.in_ports[0]
```
