---
marp: true
paginate: true
---

# Local gem5 setup

This slide deck outlines the steps for running gem5 **without** using Codespaces. For instructions that require Codespaces, refer to [02-Getting-Started](https://bootcamp.gem5.org/#01-Introduction/02-getting-started).

---

## Finding PowerShell

Type `PowerShell` in the search bar and launch it by clicking on the PowerShell shortcut.

---

## Directory structure similar to Codespaces

Create an empty directory named `workspaces` on your local computer by executing the following command:

```sh
mkdir '.\workspaces\'
```

The directory should be named `workspaces`, as explained in [the documentation](https://docs.github.com/en/codespaces/getting-started/deep-dive#about-the-directory-structure-of-a-codespace) provided by GitHub. This naming convention ensures that the directory structure on your local computer is similar to that of Codespaces.

---

## Docker container

Run a container by executing the following command:

`docker container run --rm --interactive --tty --volume '.\workspaces\:/workspaces/' --workdir '/workspaces/2024/' --hostname 'codespaces-ae14be' 'ghcr.io/gem5/devcontainer:bootcamp-2024'`

The output should resemble the following:

```sh
root@codespaces-ae14be:/workspaces/2024#
```

The Bash prompt should appear exactly as shown in the screenshot on page 7 of the slide deck titled [02-getting-started](https://bootcamp.gem5.org/#01-Introduction/02-getting-started).

---

## Source code of gem5

Clone the repository maintained by the gem5 developers by executing the following command:

`time git clone --recurse-submodules 'https://github.com/gem5bootcamp/2024.git' '/workspaces/2024/'`

This command clones the gem5 bootcamp repository, including all submodules.

---

## Lifecycle script

Run the lifecycle script provided by the gem5 developers by executing the following commands:

```sh
cd '/workspaces/2024/'
time bash -v -x '/workspaces/2024/.devcontainer/on_create.sh'
```

This script is specified in the configuration file named [devcontainer.json](https://github.com/gem5bootcamp/2024/blob/main/.devcontainer/devcontainer.json). Running this script will download the Linux disk images suitable for simulation using the gem5 simulator.

---

## Running a simulation

To verify that the gem5 simulator works as expected, run the example presented in the slide deck titled [02-getting-started](https://bootcamp.gem5.org/#01-Introduction/02-getting-started) by executing the following commands:

```sh
cd '/workspaces/2024/materials/01-Introduction/02-getting-started/'
time gem5-mesi './completed/basic.py'
```

This command runs the gem5 simulator with the provided Python script.

---

## Simulation statistics

To view the simulation statistics, open `m5out/stats.txt` with a text editor. Alternatively, view the first few lines by executing the following commands:

```sh
cd '/workspaces/2024/materials/01-Introduction/02-getting-started/'
head './m5out/stats.txt'
```

The output should resemble the following:

```sh
root@codespaces-ae14be:/workspaces/2024/materials/01-Introduction/02-getting-started# head m5out/stats.txt
---------- Begin Simulation Statistics ----------
simSeconds       0.020000 # Number of seconds simulated (Second)
simTicks      20000000000 # Number of ticks simulated (Tick)
finalTick     20000000000 # Number of ticks from beginning of simulation (restored from checkpoints and never reset) (Tick)
simFreq     1000000000000 # The number of ticks per simulated second ((Tick/Second))
hostSeconds         36.08 # Real time elapsed on the host (Second)
hostTickRate    554378533 # The number of ticks simulated per host second (ticks/s) ((Tick/Second))
hostMemory        2771948 # Number of bytes of host memory used (Byte)
simInsts          7479814 # Number of instructions simulated (Count)
root@codespaces-ae14be:/workspaces/2024/materials/01-Introduction/02-getting-started#
```

---

## Next steps

Proceed to the steps outlined in the slide deck titled [01-stdlib](https://bootcamp.gem5.org/#02-Using-gem5/01-stdlib).
