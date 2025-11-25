
# Gem5 project

- 'makefile': makefile runner, which will run all corner. For single run, please see 'run_example.sh'
- scripts/: All Python configuration scripts used in your design, including custom hierarchy, topology, and runner scripts('hardware/fs_resnet.py')
- results/: Simulation logs and output files such as stats.txt for both baseline and optimized configurations, showing simSeconds measured strictly within the ROI.
- 'run_example.sh': example makefile configuration
- report.pdf

# Suggest Configuration

| # | Cores | L1 size(KB) | L1 assoc | L2 size(MB) | L2 assoc | ring dir. | ROB, int/fp_reg, LQ/SQ |
| - | ----- | ----------- | -------- | ----------- | -------- | --------- | ---------------------- |
| 1 | 4     | 512         | 8        | 2           | 16       | bidir.    | 256                    |
| 2 | 4     | 512         | 16       | 4           | 16       | bidir.    | 256                    |
| 3 | 4     | 1024        | 8        | 2           | 16       | bidir.    | 256                    |
| 4 | 4     | 512         | 8        | 4           | 16       | bidir.    | 256                    |

or simply just:
```
gem5 --outdir=./log hardware/fs_resnet.py
```

This document describes how to build and run workloads in gem5 using **FS (full-system)** mode. It also includes instructions for preparing disk images, inserting workloads, and collecting simulation statistics.

## Build Workloads
Go into the `software/` folder and compile the workload:
```
cd software/
make
cd ..
```

### Makefile content:

To build your **ResNet benchmark** for gem5, we use **static linking** whenever possible.
Static linking embeds all required libraries (like `glibc`, `libm`, `libpthread`) directly into the binary, so it does not depend on the host system’s runtime environment.
```
gcc -O2 -static -o resnet_mt resnet_mt.c -lpthread -lm -Wl,-z,noexecstack
```

### Why `-static` is Recommended
- The full-system image used later in gem5 is based on **Ubuntu 18.04**, which includes **glibc 2.27**.
- If your host machine uses a newer glibc (e.g., 2.31 or 2.39), dynamically linked binaries may fail to run inside gem5 with an error like:
```
./resnet_mt: /lib/x86_64-linux-gnu/libc.so.6: version `GLIBC_2.29' not found
```
- Using `-static` ensures the binary contains its own copy of glibc, removing compatibility issues.

### Verify the Binary Type:
After building, check whether the binary is statically linked:
```
file software/resnet_mt
```
You should see output containing “statically linked”, confirming that no external glibc dependency exists.


## FS Mode (Full-System)

1. Make sure you have added `--privileged` before building container. If you didn't, juse remove it and rebuild one:
    ```
    docker run -it `
    --device /dev/kvm `
    --name ee6455-gem5-project `
    --privileged `
    --volume $HOME\workspaces\:/workspaces/ `
    --workdir /workspaces/2025/ `
    --hostname EE6455-gem5 `
    ghcr.io/gem5/devcontainer:v25-0
    ```

2. Prepare directories

    ```
    cd /workspaces/2025/gem5-project
    mkdir disks binaries
    ```

3. Download kernel
    ```
    wget http://dist.gem5.org/dist/v22-0/kernels/x86/static/vmlinux-4.4.186
    mv vmlinux-4.4.186 binaries/
    ```

4. Download disk (~24GB)
    ```
    wget http://dist.gem5.org/dist/v22-0/images/x86/ubuntu-18-04/parsec.img.gz
    gzip -d parsec.img.gz
    mv parsec.img disks/
    ```

5. Insert workload into disk

Copy your workload to image
```
mkdir -p /tmp/rootfs
sudo mount -o loop,offset=$((2048*512)) disks/parsec.img /tmp/rootfs
cp software/resnet_mt  /tmp/rootfs/root
sudo umount /tmp/rootfs
```

## Run FS Simulation example 1
```
gem5 --outdir=m5out/resnet hardware/fs_ex1.py
```

1. Connect to Guest
    Open another terminal:
    ```
    m5term 3456
    ```
    You should see Linux boot messages and get a root shell inside the simulated machine.
    
    Note: If you want to quit m5term, first type `~` then `.` .


2. Switch CPU Type
    Inside the guest (`via m5term`), type:
    ```
    m5 exit
    ```
    This triggers the CPU switch from KVM → Timing mode (handled by your Python `exit_event_handler`).

3. Run Workload and Collect Statistics
    After the system resumes in Timing mode, run:
    ```
    m5 resetstats
    taskset -c 0-3 ./resnet_mt --channels 8 --size 8 --blocks 8 --threads 4
    m5 dumpstats
    m5 exit
    ```
    - `m5 resetstats` → Reset gem5 statistics counters.
    - `taskset -c 0-3 ./resnet_mt` → Run the workload pinned to cores 0–3.
    - `m5 dumpstats` → Dump the collected statistics to `stats.txt`.
    - `m5 exit` → Trigger gem5 to exit (or advance to the next event handler).

    > Important:
    > Do **not** run `m5 resetstats` before the CPU has switched to Timing mode.
    > Doing so can cause invalid statistics or a segmentation fault in gem5.


## Run FS Simulation — Automated CPU Switch and Workload Execution

This example automates the entire Full-System (FS) flow:
the CPU automatically switches from KVM → Timing mode, executes the workload, collects statistics, and exits gem5 — all without manual `m5term` interaction.
```
gem5 --outdir=m5out/resnet_auto hardware/fs_resnet.py
```

### Description

The `fs_resnet.py` script embeds an `rcS` startup script that automatically:
1. Boots Linux and triggers the **CPU switch** from KVM → Timing mode.
2. Runs the `resnet_mt` workload pinned to four cores.
3. Collects gem5 statistics (`resetstats` / `dumpstats`).
4. Exits the simulation cleanly when finished.

### Key Points

- No manual `m5term` interaction is required.
- The CPU switch, workload execution, and statistics collection happen automatically.
- Ideal for batch runs or reproducible performance measurements.
