// ============================================================================
// resnet_mt.c  --  Tiny ResNet-like model using a custom thread-pool
// Build: gcc -O2 -static -o resnet_mt resnet_mt.c -lpthread -lm -Wl,-z,noexecstack
// ----------------------------------------------------------------------------
// This program implements a simplified residual CNN forward pass with
// multi-threaded parallelism using a minimal thread-pool and CPU affinity.
// Tasks such as convolution, ReLU, and add are parallelized over channels.
// ============================================================================

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <pthread.h>
#include <stdint.h>
#include <time.h>
#include <sched.h>
#include <unistd.h>

// Compatibility macro for restrict keyword
#ifndef RESTRICT
# if defined(__STDC_VERSION__) && __STDC_VERSION__ >= 199901L
#  define RESTRICT restrict
# else
#  define RESTRICT
# endif
#endif

// ------------------------ Small utilities ------------------------
// Basic ReLU and monotonic clock helper
static inline float relu(float x){ return x>0?x:0.f; }
static uint64_t now_ns(void){ struct timespec ts; clock_gettime(CLOCK_MONOTONIC,&ts); return (uint64_t)ts.tv_sec*1000000000ull + (uint64_t)ts.tv_nsec; }

// ------------------------ Argument struct and parser ------------------------
// Args holds runtime configuration parsed from command line:
//  C = channels, H = height (and width), B = residual blocks,
//  T = threads (thread pool size)
typedef struct {
    int C,H,B,T;
} Args;

static void parse_args(int argc, char** argv, Args* a){
    // default values
    a->C=8; a->H=8; a->B=8; a->T=4;
    for(int i=1;i<argc;i++){
        if(!strcmp(argv[i],"--channels") && i+1<argc) a->C=atoi(argv[++i]);
        else if(!strcmp(argv[i],"--size") && i+1<argc) a->H=atoi(argv[++i]);
        else if(!strcmp(argv[i],"--blocks") && i+1<argc) a->B=atoi(argv[++i]);
        else if(!strcmp(argv[i],"--threads") && i+1<argc) a->T=atoi(argv[++i]);
        else if(!strcmp(argv[i],"--help")){
            printf("Usage: %s [--channels C] [--size H] [--blocks B] [--threads T]\n", argv[0]);
            exit(0);
        }
    }
    // sanitize
    if(a->C<=0)a->C=8; if(a->H<=0)a->H=8; if(a->B<=0)a->B=1; if(a->T<=0)a->T=1;
}

// ------------------------ Deterministic weights helpers ------------------------
// Simple deterministic pseudo-random weight initializer and bias init.
// Using sinf ensures repeatability across runs for debugging/measurement.
static void init_weights(float* w, int n, float scale){ for(int i=0;i<n;i++) w[i]= scale * sinf(0.1f*(float)(i+1)); }
static void init_bias   (float* b, int n, float v){ for(int i=0;i<n;i++) b[i]=v; }

// ============================================================================
// Thread Pool Implementation
// ----------------------------------------------------------------------------
// The thread pool executes range-based tasks in parallel.
// Each task defines a function operating over [begin, end) subranges of N items.
// Threads wait for work on a condition variable, process their subrange,
// then decrement a shared counter when done.
// ============================================================================

// Function pointer for range-based parallel tasks
typedef void (*range_task_fn)(int tid, int nth, int begin, int end, void* ctx);

// Job structure describing one active task
typedef struct {
    int N;                 // number of units to split (range [0..N))
    range_task_fn fn;      // task callback
    void* ctx;             // user context
    int remaining;         // countdown of how many threads haven't finished
    int active;            // flag whether a job is running
    unsigned target_gen;   // generation ID for this job
} Job;

// ThreadPool structure holding synchronization primitives and threads.
typedef struct {
    int nth;               // number of worker threads
    pthread_t* ths;        // thread handles
    pthread_mutex_t m;     // mutex for job activation
    pthread_cond_t cv;     // condition variable to wake workers
    pthread_cond_t cv_done;// condition variable to notify job completion
    Job job;               // current job descriptor
    int stop;              // shutdown flag
    unsigned gen;          // global job generation counter
} ThreadPool;

// Split a range [0..n) into (nth) nearly-equal slices
static void split_1d(int n, int tid, int nth, int* begin, int* end){
    int base=n/nth, rem=n%nth;
    *begin = tid*base + (tid<rem?tid:rem);
    *end   = *begin + base + (tid<rem?1:0);
}

// WorkerArg used to pass pool pointer + thread id to worker_main
typedef struct { ThreadPool* tp; int tid; } WorkerArg;

// ---------------------------------------------------------------------------
// Worker thread main loop
// Each worker waits for jobs, executes its slice, and signals completion.
// ---------------------------------------------------------------------------
static void* worker_main(void* arg){
    WorkerArg* wa=(WorkerArg*)arg;
    ThreadPool* tp=wa->tp;
    int tid=wa->tid;

    // Best-effort CPU affinity: pin worker to tid % num_online_cpus.
    cpu_set_t cs; 
    CPU_ZERO(&cs);
    int ncpu = (int)sysconf(_SC_NPROCESSORS_ONLN); 
    if(ncpu<=0) ncpu=1;
    int target_core = tid % ncpu;
    CPU_SET(target_core, &cs);
    pthread_setaffinity_np(pthread_self(), sizeof(cs), &cs);

    int actual_core = sched_getcpu();
    printf("[Thread %d] running on CPU %d (target=%d)\n", tid, actual_core, target_core);
    fflush(stdout);

    unsigned seen_gen = 0;

    for(;;){
        pthread_mutex_lock(&tp->m);
        while(!tp->stop && (!tp->job.active || tp->job.target_gen == seen_gen))
            pthread_cond_wait(&tp->cv, &tp->m);
        if(tp->stop){ pthread_mutex_unlock(&tp->m); break; }

        seen_gen = tp->job.target_gen;

        // Copy job details under lock, then release lock for execution.
        int N=tp->job.N; 
        range_task_fn fn=tp->job.fn; 
        void* ctx=tp->job.ctx;
        int b,e; 
        split_1d(N, tid, tp->nth, &b, &e);
        pthread_mutex_unlock(&tp->m);

        int did_work = 0;
        // Execute callback for our subrange.
        if(e>b){ fn(tid, tp->nth, b, e, ctx); did_work = 1; }

        // Signal completion: decrement remaining and notify last waiter.
        pthread_mutex_lock(&tp->m);
        if (did_work){
            if(--tp->job.remaining==0){
                tp->job.active=0;
                pthread_cond_broadcast(&tp->cv_done);
            }
        }
        pthread_mutex_unlock(&tp->m);
    }
    return NULL;
}

// Initialize the thread pool with nth worker threads.
static void tp_init(ThreadPool* tp, int nth){
    tp->nth=nth; tp->ths=(pthread_t*)malloc(sizeof(pthread_t)*nth);
    pthread_mutex_init(&tp->m,NULL);
    pthread_cond_init(&tp->cv,NULL);
    pthread_cond_init(&tp->cv_done,NULL);
    tp->job.active=0; tp->stop=0; tp->gen = 0;

    // Spawn worker threads
    for(int i=0;i<nth;i++){
        WorkerArg* wa=(WorkerArg*)malloc(sizeof(WorkerArg));
        wa->tp=tp; wa->tid=i;
        pthread_create(&tp->ths[i],NULL,worker_main,wa);
    }
}

// Count how many threads will receive a non-empty slice
static int count_non_empty_slices(int N, int nth){
    int cnt = 0;
    for(int t=0;t<nth;t++){
        int b,e; split_1d(N, t, nth, &b, &e);
        if(e>b) cnt++;
    }
    return cnt;
}

// Submit a job to the pool (synchronous blocking version)
static void tp_submit(ThreadPool* tp, int N, range_task_fn fn, void* ctx){
    pthread_mutex_lock(&tp->m);
    tp->job.N = N;
    tp->job.fn = fn;
    tp->job.ctx = ctx;
    tp->job.active = 1;
    tp->job.remaining = count_non_empty_slices(N, tp->nth);

    // If no work, skip
    if (tp->job.remaining == 0){
        tp->job.active = 0;
        pthread_mutex_unlock(&tp->m);
        return;
    }
    
    // Advance generation counter and broadcast wakeup
    tp->gen++;
    tp->job.target_gen = tp->gen;
    pthread_cond_broadcast(&tp->cv);

    // Wait for all workers to finish this job
    while(tp->job.active) pthread_cond_wait(&tp->cv_done, &tp->m);
    pthread_mutex_unlock(&tp->m);
}

// Gracefully stop all threads
static void tp_shutdown(ThreadPool* tp){
    pthread_mutex_lock(&tp->m); 
    tp->stop=1; 
    pthread_cond_broadcast(&tp->cv); 
    pthread_mutex_unlock(&tp->m);

    for(int i=0;i<tp->nth;i++) pthread_join(tp->ths[i],NULL);
    pthread_cond_destroy(&tp->cv_done); 
    pthread_cond_destroy(&tp->cv); 
    pthread_mutex_destroy(&tp->m);
    free(tp->ths);
}

// ============================================================================
// Parallel Operators (range-based tasks)
// ============================================================================

// ---------------------------------------------------------------------------
// Convolution 3x3 (same padding)
// Parallelized over output channels.
// Layouts: x=[C,H,W], w=[K,C,3,3], y=[K,H,W]
// ---------------------------------------------------------------------------
typedef struct {
    const float* RESTRICT x; // [C,H,W]
    const float* RESTRICT w; // [K,C,3,3]
    const float* RESTRICT b; // [K] or NULL
    int C,H,W,K;
    float* RESTRICT y;       // [K,H,W]
} ConvArgs;

// conv3x3_range: compute output channels in [ks,ke) (inclusive of ks, exclusive of ke).
// This is the inner computation of a standard "same" convolution with zero padding.
static void conv3x3_range(int tid,int nth,int ks,int ke, void* vctx){
    (void)tid; (void)nth;
    ConvArgs* c=(ConvArgs*)vctx;
    const int C=c->C,H=c->H,W=c->W;
    const float* x=c->x; const float* w=c->w; const float* b=c->b; float* y=c->y;
    for(int k=ks;k<ke;k++){
        for(int i=0;i<H;i++){
            for(int j=0;j<W;j++){
                float sum = b? b[k] : 0.f;
                for(int cc=0; cc<C; cc++){
                    for(int di=-1; di<=1; di++){
                        int ii=i+di;
                        for(int dj=-1; dj<=1; dj++){
                            int jj=j+dj;
                            float xv=0.f;
                            // bounds-checked load for zero padding
                            if((unsigned)ii<(unsigned)H && (unsigned)jj<(unsigned)W)
                                xv = x[(cc*H + ii)*W + jj];
                            float ww = w[ ((k*C + cc)*3 + (di+1))*3 + (dj+1) ];
                            sum += xv*ww;
                        }
                    }
                }
                y[(k*H + i)*W + j] = sum;
            }
        }
    }
}

// conv3x3_same_par: user-facing wrapper that submits conv job splitting over K.
static void conv3x3_same_par(ThreadPool* tp, const float* x,const float* w,const float* b,int C,int H,int W,int K,float* y){
    ConvArgs a={x,w,b,C,H,W,K,y};
    tp_submit(tp, K, conv3x3_range, &a);
}

// Simple element-wise ReLU as a range task. VecArgs contains pointer and total N.
typedef struct { float* a; int N; } VecArgs;
static void relu_range(int tid,int nth,int s,int e, void* vctx){
    (void)tid;(void)nth; VecArgs* a=(VecArgs*)vctx;
    for(int i=s;i<e;i++) a->a[i]=relu(a->a[i]);
}

// Element-wise add: a[i] += b[i] for i in range.
static void add_range(int tid,int nth,int s,int e, void* vctx){
    (void)tid;(void)nth; typedef struct{float* a; const float* b;} Add; Add* p=(Add*)vctx;
    for(int i=s;i<e;i++) p->a[i]+=p->b[i];
}

// Global average pool per-channel accumulator: each channel reduced independently.
typedef struct { const float* x; int C,H,W; float* out; } GAPArgs;
static void gap_range(int tid,int nth,int s,int e, void* vctx){
    (void)tid;(void)nth; GAPArgs* g=(GAPArgs*)vctx;
    const int H=g->H, W=g->W;
    for(int ch=s; ch<e; ch++){
        double acc=0.0;
        const float* base = g->x + ch*H*W;
        for(int i=0;i<H*W;i++) acc += base[i];
        g->out[ch]=(float)(acc/(double)(H*W));
    }
}

// Linear (fully-connected) layer
typedef struct { const float* x; const float* w; const float* b; float* y; int In,Out; } LinArgs;
static void linear_range(int tid,int nth,int s,int e, void* vctx){
    (void)tid;(void)nth; LinArgs* L=(LinArgs*)vctx;
    const int In=L->In; const float* x=L->x; const float* w=L->w; const float* b=L->b; float* y=L->y;
    for(int o=s;o<e;o++){
        double acc=b? (double)b[o] : 0.0;
        const float* wr = w + o*In;
        for(int i=0;i<In;i++) acc += (double)x[i]*(double)wr[i];
        y[o]=(float)acc;
    }
}

// Stable softmax for small vectors
static void softmax_inplace(float* x, int n){
    float m=x[0]; for(int i=1;i<n;i++) if(x[i]>m) m=x[i];
    double s=0.0; for(int i=0;i<n;i++){ x[i]=(float)exp((double)x[i]-m); s+=x[i]; }
    for(int i=0;i<n;i++) x[i]/=(float)s;
}

// ============================================================================
// Residual Block Runner
// ----------------------------------------------------------------------------
// A single ResBlock performs:
//   y = ReLU( conv2( ReLU(conv1(x)) ) + x )
// ============================================================================

typedef struct {
    float* RESTRICT buf0; float* RESTRICT buf1; float* RESTRICT buf2;
    const float* RESTRICT w1; const float* RESTRICT b1;
    const float* RESTRICT w2; const float* RESTRICT b2;
    int C,H,W;
    ThreadPool* tp;
} ResBlock;

static void residual_block_run(ResBlock* rb){
    const int C=rb->C, H=rb->H, W=rb->W;

    // Debug: print first few input values before conv1
    // printf("[Block debug] Input to conv1 (C=%d,H=%d): %.5f %.5f %.5f %.5f\n",
    //        C,H, rb->buf0[0], rb->buf0[1], rb->buf0[2], rb->buf0[3]);

    // 1) conv1 (parallel over output channels)
    conv3x3_same_par(rb->tp, rb->buf0, rb->w1, rb->b1, C,H,W, C, rb->buf1);
    // printf("[Block debug] After conv1 (C=%d,H=%d): %.5f %.5f %.5f %.5f\n",
    //        C,H, rb->buf1[0], rb->buf1[1], rb->buf1[2], rb->buf1[3]);

    // 2) relu (parallel over elements)
    {
        VecArgs vr1; 
        vr1.a = rb->buf1;
        vr1.N = rb->C * rb->H * rb->W;
        tp_submit(rb->tp, vr1.N, relu_range, &vr1);
    }

    // printf("[Block debug] After conv1+relu (C=%d,H=%d): %.5f %.5f %.5f %.5f\n",
    //    C,H, rb->buf1[0], rb->buf1[1], rb->buf1[2], rb->buf1[3]);

    // 3) Second convolution
    conv3x3_same_par(rb->tp, rb->buf1, rb->w2, rb->b2, C,H,W, C, rb->buf2);
    // printf("[Block debug] After conv2 (C=%d): %.5f %.5f %.5f %.5f\n",
    //        C, rb->buf2[0], rb->buf2[1], rb->buf2[2], rb->buf2[3]);

    // 4) add skip connection: buf1 += buf0 (parallel)
    typedef struct{float* a; const float* b;} Add; 
    Add add={rb->buf2, rb->buf0}; tp_submit(rb->tp, C*H*W, add_range, &add);

    // 5) final relu
    {
        VecArgs vr2; 
        vr2.a = rb->buf2;
        vr2.N = rb->C * rb->H * rb->W;
        tp_submit(rb->tp, vr2.N, relu_range, &vr2);
    }

    // printf("[Block debug] After add+relu (final output): %.5f %.5f %.5f %.5f\n",
    //        rb->buf2[0], rb->buf2[1], rb->buf2[2], rb->buf2[3]);

    // 6) copy output back into buf0 for the next block
    memcpy(rb->buf0, rb->buf2, sizeof(float)*C*H*W);
}

// ------------------------ Main entry point ------------------------
int main(int argc, char** argv){
    Args a; parse_args(argc, argv, &a);
    const int C=a.C, H=a.H, W=a.H, B=a.B, T=a.T;
    const int CHW = C*H*W;

    printf("Tiny ResNet-like MT (pool): C=%d H=W=%d blocks=%d threads=%d\n", C,H,B,T);

    // Deterministic random seed for reproducibility
    unsigned int seed = 42;
    srand(seed);

    // Allocate working buffers for feature maps (buf0 is "current", buf1 is temporary)
    float* buf0 = (float*)calloc((size_t)CHW, sizeof(float));
    float* buf1 = (float*)calloc((size_t)CHW, sizeof(float));
    float* buf2 = (float*)calloc((size_t)CHW, sizeof(float));

    if(!buf0){ perror("calloc buf0"); exit(1); }
    if(!buf1){ perror("calloc buf1"); exit(1); }
    if(!buf2){ perror("calloc buf2"); exit(1); }

    // Initialize input pattern on channel 0 across spatial dims (simple deterministic pattern)
    // for(int i=0;i<H;i++) for(int j=0;j<W;j++) buf0[i*W+j] = (float)((i+j)%5)/5.0f;
    for (int c = 0; c < C; c++) {
        for (int i = 0; i < H; i++) {
            for (int j = 0; j < W; j++) {
                buf0[(c * H + i) * W + j] = ((float)rand() / (float)RAND_MAX) * 2.0f - 1.0f;  // [-1, 1)
            }
        }
    }
    // Debug: print first few values of channels 0, 1, 2
    // printf("Sample input values (channels 0~2):\n");
    // for(int c=0; c<3 && c<C; c++){
    //     printf("Channel %d:\n", c);
    //     for(int i=0; i<3 && i<H; i++){
    //         for(int j=0; j<3 && j<W; j++){
    //             printf("%.3f ", buf0[(c*H + i)*W + j]);
    //         }
    //         printf("\n");
    //     }
    //     printf("\n");
    // }

    // Allocate weights for each residual block (w1,b1 and w2,b2 per block)
    const int wsize = C*C*3*3;
    float** W1=(float**)malloc(sizeof(float*)*B);
    float** W2=(float**)malloc(sizeof(float*)*B);
    float** B1=(float**)malloc(sizeof(float*)*B);
    float** B2=(float**)malloc(sizeof(float*)*B);
    for(int b=0;b<B;b++){
        W1[b]=(float*)malloc(sizeof(float)*wsize);
        W2[b]=(float*)malloc(sizeof(float)*wsize);
        B1[b]=(float*)malloc(sizeof(float)*C);
        B2[b]=(float*)malloc(sizeof(float)*C);
        // Initialize weights/biases slightly differently per block so they are not identical
        init_weights(W1[b], wsize, 0.05f + 0.001f*(float)b);
        init_weights(W2[b], wsize, 0.05f + 0.001f*(float)(B-b));
        init_bias(B1[b], C, 0.01f);
        init_bias(B2[b], C, 0.00f);
    }

    // Classification head (GAP + Linear + Softmax)
    float* gap=(float*)malloc(sizeof(float)*C);
    float* fc_w=(float*)malloc(sizeof(float)* (2*C));
    float  fc_b[2]; init_weights(fc_w, 2*C, 0.1f); init_bias(fc_b, 2, 0.0f);

    // Initialize thread pool with T worker threads
    ThreadPool tp; tp_init(&tp, T);

    // Forward pass through residual blocks
    for(int b=0;b<B;b++){
        // printf("=== Running Block %d ===\n", b);
        ResBlock rb = {buf0, buf1, buf2, W1[b], B1[b], W2[b], B2[b], C, H, W, &tp};
        residual_block_run(&rb);
    }

    // Global Average Pool -> Linear -> Softmax
    GAPArgs g={buf0,C,H,W,gap}; 
    tp_submit(&tp, C, gap_range, &g);
    float logits[2];
    LinArgs L={gap, fc_w, fc_b, logits, C, 2}; 
    tp_submit(&tp, 2, linear_range, &L);
    softmax_inplace(logits, 2);

    printf("Output probs: [%.6f, %.6f], pred=%d\n", logits[0], logits[1], (logits[0]>logits[1])?0:1);

    float* final_out=(B%2==0)?buf0:buf1;
    double sum=0.0; for(size_t i=0;i<CHW;i++) sum+=final_out[i];
    printf("Output checksum: %.6f\n",sum);

    // Cleanup resources
    tp_shutdown(&tp);
    for(int b=0;b<B;b++){ free(W1[b]); free(W2[b]); free(B1[b]); free(B2[b]); }
    free(W1); free(W2); free(B1); free(B2);
    free(buf0); free(buf1); free(buf2); free(gap); free(fc_w);
    return 0;
}
