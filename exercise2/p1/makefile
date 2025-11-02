#////////////////////////////////////////////////////////
# Design: Makefile for GEM5 simulation
# Author: Kuan-Hsi(Vic) Chen
# Email : s179038@gmail.com
# Update: [2025/11/01]: Automatically sweep variables
#////////////////////////////////////////////////////////

PYTHON ?= python3
GEM5   ?= gem5
GEM5RE ?= gem5 -re

# Python Scripts
ANALYSIS ?= scripts/simpoint_analysis.py
CHECKPT  ?= scripts/simpoint_checkpoint.py
RUN      ?= scripts/simpoint_run.py
FULL_RUN ?= scripts/simpoint_full_run.py
SIM_P    ?= scripts/simpoint_predict_ipc.py
SMARTS   ?= scripts/smarts.py
SMARTS_P ?= scripts/smarts_predict_ipc.py
SID      ?= 0 1 2 3

# Output Folders
OUT_ANALYSIS ?= log/simpoint_analysis
OUT_CHECKPT  ?= log/simpoint_checkpoint
OUT_RUN      ?= log/simpoint_run
OUT_FULL_RUN ?= log/simpoint_full_run
OUT_SMARTS   ?= log/smarts

# Output Files
SIMPOINT ?= /workspaces/gem5-exercises/materials/02-Using-gem5/09-sampling/01-simpoint/simpoint
SIM_BBV  ?= log/simpoint_analysis/simpoint.bb.gz
SIM_PT   ?= log/simpoint_analysis/results.simpts
SIM_WEI  ?= log/simpoint_analysis/results.weights

.PHONY: all simpoint \
		simpoint_analysis simpoint_checkpoint \
		simpoint_full_run simpoint_predict \
		smart clean

all: simpoint smarts

simpoint: simpoint_analysis simpoint_checkpoint simpoint_run simpoint_predict

# To generate bb.gz and extract for SimPoint
simpoint_analysis:
	$(GEM5) --outdir=$(OUT_ANALYSIS) $(ANALYSIS)
	$(SIMPOINT) -inputVectorsGzipped -loadFVFile $(SIM_BBV) \
  		-k 5 \
  		-saveSimpoints $(SIM_PT) \
  		-saveSimpointWeights $(SIM_WEI)

# Use SimPoints and Weights to generate CheckPoints
simpoint_checkpoint:
	$(GEM5) --outdir=$(OUT_CHECKPT) $(CHECKPT)

# Run each CheckPoint of SimPoint
simpoint_run:
	for a in $(SID); do \
	  echo "== Check Point $$a =="; \
	  $(GEM5) --outdir=$(OUT_RUN)_$$a $(RUN) --sid=$$a | \
	  tee -i  $(OUT_RUN)_$$a/simout.txt ;\
	done

# Run full-detailed for benchmarking, 
# then predict IPC and compare with the baseline full run.
simpoint_predict:
	$(GEM5) --outdir=$(OUT_FULL_RUN) $(FULL_RUN)
	$(PYTHON) $(SIM_P)

# SMARTS sample method
smart:
	$(GEM5RE) --outdir=$(OUT_SMARTS) $(SMARTS)
	$(PYTHON) $(SMARTS_P)

clean:
	@rm -rf log
