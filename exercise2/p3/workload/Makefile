CC = gcc
CFLAGS = -O2 -static

all: matmul_mt

matmul_mt: matmul_mt.c
	$(CC) $(CFLAGS) -o $@ $< -lpthread -lm -Wl,-z,noexecstack

clean:
	rm -f matmul_mt
