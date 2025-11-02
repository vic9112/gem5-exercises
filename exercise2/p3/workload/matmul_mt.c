#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>
#include <sched.h>
#include <unistd.h>
#include <getopt.h>

/* ============================================================
 * Multithreaded Matrix Multiplication (POSIX threads version)
 * ------------------------------------------------------------
 * - Each thread computes a subset of rows of the output matrix C = A * B.
 * - Thread affinity is set to reduce scheduling interference.
 * - Supports both deterministic and random initialization modes.
 * ============================================================ */

#define MAX_THREADS 16
#define DEFAULT_MATRIX_SIZE 512
#define DEFAULT_NUM_THREADS 4

int N;                  // matrix size NxN
int num_threads;        // number of worker threads
float **A, **B, **C;    // global matrices

/* ============================================================
 * Worker thread function: compute assigned rows of matrix C
 * Additional prints: thread name, pthread id, CPU it's running on,
 * and affinity mask to help verify binding/affinity.
 * ============================================================ */
 void* worker(void* arg) {
    int tid = *(int*)arg;

    /* Bind this thread to a specific CPU core to improve performance */
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    int nprocs = sysconf(_SC_NPROCESSORS_ONLN);
    if (nprocs <= 0) nprocs = 1;
    CPU_SET(tid % nprocs, &cpuset);
    pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset);

    /* Set a short thread name for easier identification (max 16 chars incl. \\0) */
    char tname[16];
    snprintf(tname, sizeof(tname), "worker%d", tid);
#ifdef __linux__
    pthread_setname_np(pthread_self(), tname);
#endif

    /* Query actual CPU this thread is running on (best-effort) */
    int curcpu = -1;
#ifdef __linux__
    curcpu = sched_getcpu(); /* returns current CPU number or -1 if not supported */
#endif

    /* Print identification + affinity mask */
    unsigned long pthread_id_val = (unsigned long)pthread_self();
    printf("[thread %d] pthread=%lu name=\"%s\" requested_affinity=CPU%u actual_cpu=%d\n",
           tid, pthread_id_val, tname, (unsigned int)(tid % nprocs), curcpu);

    /* Print affinity mask: list allowed CPUs */
    printf("[thread %d] affinity mask: ", tid);
    for (int c = 0; c < nprocs; ++c) {
        if (CPU_ISSET(c, &cpuset)) {
            printf("%d ", c);
        }
    }
    printf("\n");

    /* Determine row range handled by this thread */
    int rows_per_thread = N / num_threads;
    int start = tid * rows_per_thread;
    int end = (tid == num_threads - 1) ? N : start + rows_per_thread;

    /* Standard triple-loop matrix multiplication */
    for (int i = start; i < end; i++) {
        for (int j = 0; j < N; j++) {
            float sum = 0.0f;
            for (int k = 0; k < N; k++)
                sum += A[i][k] * B[k][j];
            C[i][j] = sum;
        }
    }
    return NULL;
}

/* ============================================================
 * Return current time in milliseconds
 * Used to measure total computation time
 * ============================================================ */
double get_time_ms() {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1000.0 + t.tv_nsec / 1.0e6;
}

/* ============================================================
 * Print usage information for command-line arguments
 * ============================================================ */
void print_usage(const char *prog) {
    printf("Usage: %s [options]\n", prog);
    printf(" Options:\n");
    printf("  -s, --size <N>        : matrix size NxN (default %d)\n", DEFAULT_MATRIX_SIZE);
    printf("  -t, --threads <T>     : number of threads (default %d)\n", DEFAULT_NUM_THREADS);
    printf("  -r, --seed <seed>     : random seed for initialization (default 0)\n");
    printf("  -a, --mode <mode>     : init mode: 0 = deterministic (default), 1 = random\n");
    printf("  -v, --verify <count>  : print verification elements count (default 2)\n");
    printf("  -h, --help            : show this help message\n\n");
    printf(" Example:\n");
    printf("  %s --size 1024 --threads 8 -r 42 -a 1\n", prog);
}

/* ============================================================
 * Safe memory allocation with error checking
 * ============================================================ */
void *xmalloc(size_t s) {
    void *p = malloc(s);
    if (!p) { fprintf(stderr, "malloc failed\n"); exit(EXIT_FAILURE); }
    return p;
}

/* ============================================================
 * Main Function
 * ------------------------------------------------------------
 * 1. Parse command-line arguments
 * 2. Allocate and initialize matrices
 * 3. Spawn worker threads
 * 4. Join all threads
 * 5. Print verification results
 * ============================================================ */
int main(int argc, char** argv) {
    int init_mode = 0;      /* 0 deterministic, 1 random initialization */
    unsigned int seed = 0;
    int print_count = 4;    /* number of verification prints */

    /* Default values */
    N = DEFAULT_MATRIX_SIZE;
    num_threads = DEFAULT_NUM_THREADS;

    /* Command-line options definition */
    static struct option long_opts[] = {
        {"size",     required_argument, 0, 's'},
        {"threads",  required_argument, 0, 't'},
        {"seed",     required_argument, 0, 'r'},
        {"mode",     required_argument, 0, 'a'},
        {"verify",   required_argument, 0, 'v'},
        {"help",     no_argument,       0, 'h'},
        {0, 0, 0, 0}
    };

    /* Parse all arguments */
    int opt, opt_index = 0;
    while ((opt = getopt_long(argc, argv, "s:t:r:a:v:h", long_opts, &opt_index)) != -1) {
        switch (opt) {
            case 's': N = atoi(optarg); break;
            case 't': num_threads = atoi(optarg); break;
            case 'r': seed = (unsigned int)atoi(optarg); break;
            case 'a': init_mode = atoi(optarg); break;
            case 'v': print_count = atoi(optarg); break;
            case 'h': print_usage(argv[0]); return 0;
            default : print_usage(argv[0]); return 1;
        }
    }

    /* Sanity checks */
    if (num_threads > MAX_THREADS) num_threads = MAX_THREADS;
    if (num_threads < 1) num_threads = 1;
    if (N <= 0) N = DEFAULT_MATRIX_SIZE;

    printf("Matrix size = %d, Threads = %d\n", N, num_threads);

    /* ============================================================
     * Matrix allocation (row pointers + rows)
     * ============================================================ */
    A = (float**)xmalloc(N * sizeof(float*));
    B = (float**)xmalloc(N * sizeof(float*));
    C = (float**)xmalloc(N * sizeof(float*));
    for (int i = 0; i < N; i++) {
        A[i] = (float*)xmalloc(N * sizeof(float));
        B[i] = (float*)xmalloc(N * sizeof(float));
        C[i] = (float*)xmalloc(N * sizeof(float));
    }

    /* ============================================================
     * Initialize matrices A and B
     * ------------------------------------------------------------
     * mode=0 : deterministic pattern (for reproducible results)
     * mode=1 : random pattern (for variability)
     * ============================================================ */
    if (init_mode == 1) {
        srand(seed);
        for (int i = 0; i < N; i++)
            for (int j = 0; j < N; j++) {
                A[i][j] = ((float)rand() / RAND_MAX) - 0.5f;
                B[i][j] = ((float)rand() / RAND_MAX) - 0.5f;
            }
    } else {
        for (int i = 0; i < N; i++)
            for (int j = 0; j < N; j++) {
                A[i][j] = (float)(i + j) * 0.001f;
                B[i][j] = (float)(i - j) * 0.002f;
            }
    }

    /* ============================================================
     * Spawn threads for computation
     * ============================================================ */
    pthread_t threads[MAX_THREADS];
    int tid[MAX_THREADS];

    double t0 = get_time_ms();
    for (int i = 0; i < num_threads; i++) {
        tid[i] = i;
        pthread_create(&threads[i], NULL, worker, &tid[i]);
    }
    for (int i = 0; i < num_threads; i++)
        pthread_join(threads[i], NULL);
    double t1 = get_time_ms();

    /* ============================================================
     * Verification Output (based on --verify argument)
     * ============================================================ */
    if (print_count >= 1) printf("Result[0][0] = %.6f\n", C[0][0]);
    if (print_count >= 2) printf("Result[N-1][N-1] = %.6f\n", C[N-1][N-1]);
    if (print_count >= 3) printf("Result[N/2][N/2] = %.6f\n", C[N/2][N/2]);
    if (print_count >= 4) printf("Result[N/4][N/4] = %.6f\n", C[N/4][N/4]);


    printf("Matrix size = %d, Threads = %d\n", N, num_threads);

    //printf("Time = %.3f ms\n", t1 - t0); // Uncomment to print elapsed time

    /* ============================================================
     * Free all allocated memory
     * ============================================================ */
    for (int i = 0; i < N; i++) { free(A[i]); free(B[i]); free(C[i]); }
    free(A); free(B); free(C);
    return 0;
}
