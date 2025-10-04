#////////////////////////////////////////////////////////
# Design: Makefile for GEM5 simulation
# Author: Kuan-Hsi(Vic) Chen
# Email : s179038@gmail.com
# Update: [2025/09/29]: Automatically sweep variables
#////////////////////////////////////////////////////////

PYTHON      ?= python3
GEM5        ?= gem5
GEM5_MESI   ?= gem5-mesi

# Scripts
RUBY_PY     ?= p2_1/p2_1.py
CLASSIC_PY  ?= p2_2/p2_2.py
PARSER      ?= parse.py

# Output roots
OUT_RUBY    ?= ruby
OUT_CLASSIC ?= classic
CSV_OUT     ?= p2-summary.csv

# Sweeps (ignore cache line size)
SIZES  ?= 128kB 256kB 512kB 1MB
ASSOCS ?= 8 16 32

.PHONY: all sweep parse clean \
        run-ruby-size run-ruby-assoc run-classic-size run-classic-assoc

all: sweep parse

# ---- Ruby sweeps ----
run-ruby-size:
	@set -e; for s in $(SIZES); do \
	  echo "== Ruby L2 size $$s =="; \
	  $(GEM5_MESI) --outdir=log/$(OUT_RUBY)_l2_$$s $(RUBY_PY) --l2-size $$s; \
	done

run-ruby-assoc:
	@set -e; for a in $(ASSOCS); do \
	  echo "== Ruby L2 assoc $$a =="; \
	  $(GEM5_MESI) --outdir=log/$(OUT_RUBY)_l2_a$$a $(RUBY_PY) --l2-assoc $$a; \
	done

# ---- Classic sweeps ----
run-classic-size:
	@set -e; for s in $(SIZES); do \
	  echo "== Classic L2 size $$s =="; \
	  $(GEM5) --outdir=log/$(OUT_CLASSIC)_l2_$$s $(CLASSIC_PY) --l2-size $$s; \
	done

run-classic-assoc:
	@set -e; for a in $(ASSOCS); do \
	  echo "== Classic L2 assoc $$a =="; \
	  $(GEM5) --outdir=log/$(OUT_CLASSIC)_l2_a$$a $(CLASSIC_PY) --l2-assoc $$a; \
	done

# Convenience aggregate targets
sweep: run-ruby-size run-classic-size run-ruby-assoc run-classic-assoc

parse:
	$(PYTHON) $(PARSER) --roots "log" --out $(CSV_OUT)

clean:
	@rm -f $(CSV_OUT)
	@rm -rf log
