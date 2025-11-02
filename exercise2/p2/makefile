#////////////////////////////////////////////////////////
# Design: Makefile for GEM5 simulation
# Author: Kuan-Hsi(Vic) Chen
# Email : s179038@gmail.com
# Update: [2025/11/01]: Automatically sweep variables
#////////////////////////////////////////////////////////

PYTHON ?= python3
GEM5   ?= gem5

# Python scripts
MODEL    ?= scripts/pwr_model.py
PARSER   ?= scripts/parse.py
CORE_NUM ?= 2 4
L3_SIZE  ?= 2MB 4MB
CPU_FREQ ?= 2GHz 3GHz

# Output folders
OUT_CORE_NUM ?= log/core_num
OUT_L3_SIZE  ?= log/l3_size
OUT_CPU_FREQ ?= log/cpu_freq

.PHONY: all power_modeling parse clean

all: power_modeling parse

power_modeling:
	for a in $(CORE_NUM); do \
	  echo "== Core count: $$a =="; \
	  $(GEM5) --outdir=$(OUT_CORE_NUM)_$$a $(MODEL) --num_cores $$a; \
	done
	for a in $(L3_SIZE); do \
	  echo "== L3 cache size: $$a =="; \
	  $(GEM5) --outdir=$(OUT_L3_SIZE)_$$a $(MODEL) --l3_size $$a; \
	done
	for a in $(CPU_FREQ); do \
	  echo "== CPU frequency: $$a =="; \
	  $(GEM5) --outdir=$(OUT_CPU_FREQ)_$$a $(MODEL) --cpu_freq $$a; \
	done

parse:
	$(PYTHON) $(PARSER)

clean:
	@rm -rf log
	@rm -rf *.csv