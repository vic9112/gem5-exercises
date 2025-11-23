CC = gcc
CFLAGS = -O2 -static

all: resnet_mt

resnet_mt: resnet_mt.c
	$(CC) $(CFLAGS) -o $@ $< -lpthread -lm -Wl,-z,noexecstack

clean:
	rm -f resnet_mt
