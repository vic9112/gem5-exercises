#////////////////////////////////////////////////////////
# Design: Makefile for GEM5 project
# Author: Kuan-Hsi(Vic) Chen
# Email : s179038@gmail.com
# Update: [2025/11/10]: Automatically sweep variables
#////////////////////////////////////////////////////////

GEM5   ?= gem5
SCRIPT ?= hardware/fs_resnet.py
LOG    ?= ./log

# ---- cost limit ----
COST_LIMIT ?= 1500

# ---- use one bash shell per recipe ----
.ONESHELL:
SHELL := /bin/bash

CORES      ?= 8      # --num_cores
CAPS       ?= 2      # --capacity (GB)
CHANNELS   ?= 2

L1_SIZES   ?= 512     # --l1-size (KB)
L1_ASSOCS  ?= 8       # --l1-assoc
L2_SIZES   ?= 4 5 6   # --l2-size (MB)
L2_ASSOCS  ?= 16      # --l2-assoc
 
WIDTHS     ?= 8       # --width
ROB_SIZES  ?= 64 128  # --rob_size
INT_REGS   ?= 64 128  # --int_regs
FP_REGS    ?= 64 128  # --fp_regs
SQ_LQS     ?= 64      # --sq_lq

.PHONY: auto_sweep clean

auto_sweep:
	mkdir -p $(LOG)

	best_sec=""
	best_cfg=""
	best_cost=""

	for cores in $(CORES); do
	  for cap in $(CAPS); do
	    for ch in $(CHANNELS); do
	      for l1 in $(L1_SIZES); do
	        for l1a in $(L1_ASSOCS); do
	          for l2 in $(L2_SIZES); do
	            for l2a in $(L2_ASSOCS); do
	              for w in $(WIDTHS); do
	                for rob in $(ROB_SIZES); do
	                  for ireg in $(INT_REGS); do
	                    for fpreg in $(FP_REGS); do
	                      for sqlq in $(SQ_LQS); do

	                        cfg="c$${cores}_cap$${cap}_ch$${ch}_l1s$${l1}_l1a$${l1a}_l2s$${l2}_l2a$${l2a}_w$${w}_rob$${rob}_int$${ireg}_fp$${fpreg}_sqlq$${sqlq}"
	                        outdir="$(LOG)/$${cfg}"

	                        echo
	                        echo "=== Running $$cfg ==="

	                        mkdir -p "$$outdir"

	                        $(GEM5) --outdir="$$outdir" $(SCRIPT) \
	                          --num_cores $$cores \
	                          --capacity $$cap \
	                          --channels $$ch \
	                          --l1-size $$l1 \
	                          --l1-assoc $$l1a \
	                          --l2-size $$l2 \
	                          --l2-assoc $$l2a \
	                          --width $$w \
	                          --rob_size $$rob \
	                          --int_regs $$ireg \
	                          --fp_regs $$fpreg \
	                          --sq_lq $$sqlq \
	                          > "$$outdir/run.log" 2>&1

	                        # capture simSeconds
	                        if [[ -f "$$outdir/stats.txt" ]]; then
	                          sim_sec=$$(awk '/^simSeconds/ {val=$$2} END{if (val!="") print val}' "$$outdir/stats.txt")
	                        else
	                          sim_sec=""
	                        fi

	                        echo "    simSeconds = $$sim_sec"

	                        cost_line=$$(grep -m1 "Total cost of configuration" "$$outdir/run.log" || true)

	                        if [[ -n "$$cost_line" ]]; then
	                          echo "    $$cost_line"
	                          total_cost=$$(printf "%s\n" "$$cost_line" | grep -oE '[0-9]+' | head -n1)
	                        else
	                          echo "    (WARNING: cost line not found in run.log)"
	                          total_cost=""
	                        fi

	                        # update the better simSeconds only if cost < 1500
	                        if [[ -n "$$sim_sec" && -n "$$total_cost" ]]; then
	                          if (( $$total_cost <= $(COST_LIMIT) )); then
	                            if [[ -z "$$best_sec" ]]; then
	                              best_sec="$$sim_sec"
	                              best_cfg="$$cfg"
	                              best_cost="$$total_cost"
	                            elif python3 -c \
	                              "import sys; sys.exit(0 if float(sys.argv[1]) < float(sys.argv[2]) else 1)" \
	                              "$$sim_sec" "$$best_sec"; then
	                              best_sec="$$sim_sec"
	                              best_cfg="$$cfg"
	                              best_cost="$$total_cost"
	                            fi
	                          else
	                            echo "    SKIP: cost $$total_cost > $(COST_LIMIT) units (over limit)"
	                          fi
	                        else
	                          echo "    SKIP: simSeconds or cost missing; not considered for best"
	                        fi

	                      done
	                    done
	                  done
	                done
	              done
	            done
	          done
	        done
	      done
	    done
	  done
	done

	echo
	echo "----------------------------------------"
	echo "Best configuration: $$best_cfg"
	echo "Best simSeconds   : $$best_sec"
	echo "Best cost         : $$best_cost units (limit $(COST_LIMIT))"

clean:
	rm -rf $(LOG) *.csv