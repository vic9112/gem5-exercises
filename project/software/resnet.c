#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

// A tiny, self-contained ResNet-like demo in one C file
// Input: single 1x8x8 image (1 channel) -> 2 residual blocks (C=8) -> global avg pool -> 2-class softmax
// All weights are deterministic constants so it runs without loading files.

static inline float relu(float x){ return x>0?x:0; }

void conv3x3_same(const float *x, const float *w, const float *b,
                  int C, int H, int W, // C input channels
                  int K,               // K output channels
                  float *y){
    // zero padding 1 on H,W
    for(int k=0;k<K;k++){
        for(int i=0;i<H;i++){
            for(int j=0;j<W;j++){
                float sum = b? b[k] : 0.f;
                for(int c=0;c<C;c++){
                    for(int di=-1; di<=1; di++){
                        for(int dj=-1; dj<=1; dj++){
                            int ii = i+di; int jj = j+dj;
                            float xv = 0.f;
                            if(0<=ii && ii<H && 0<=jj && jj<W){
                                xv = x[(c*H + ii)*W + jj];
                            }
                            float ww = w[ ((k*C + c)*3 + (di+1))*3 + (dj+1) ];
                            sum += xv * ww;
                        }
                    }
                }
                y[(k*H + i)*W + j] = sum;
            }
        }
    }
}

void add_inplace(float *a, const float *b, int n){ for(int i=0;i<n;i++) a[i]+=b[i]; }
void relu_inplace(float *a, int n){ for(int i=0;i<n;i++) a[i]=relu(a[i]); }

// Create deterministic pseudo weights
void init_weights(float *w, int n, float scale){ for(int i=0;i<n;i++) w[i]= scale * sinf(0.1f*(float)(i+1)); }
void init_bias(float *b, int n, float v){ for(int i=0;i<n;i++) b[i]=v; }

// A simple residual block: y = ReLU( Conv(ReLU(Conv(x))) + x )
void residual_block(float *buf0, float *buf1, int C, int H, int W,
                    float *w1, float *b1, float *w2, float *b2){
    // conv1
    conv3x3_same(buf0, w1, b1, C,H,W, C, buf1);
    relu_inplace(buf1, C*H*W);
    // conv2
    conv3x3_same(buf1, w2, b2, C,H,W, C, buf1);
    // add skip
    add_inplace(buf1, buf0, C*H*W);
    // relu
    relu_inplace(buf1, C*H*W);
    // copy back
    memcpy(buf0, buf1, sizeof(float)*C*H*W);
}

void global_avg_pool(const float *x, int C, int H, int W, float *out){
    for(int c=0;c<C;c++){
        double acc=0.0; // reduce FP error a bit
        for(int i=0;i<H;i++) for(int j=0;j<W;j++) acc += x[(c*H + i)*W + j];
        out[c] = (float)(acc / (H*W));
    }
}

void linear(const float *x, const float *w, const float *b, int in, int out, float *y){
    for(int o=0;o<out;o++){
        double acc=b?b[o]:0.0;
        for(int i=0;i<in;i++) acc += (double)x[i]*(double)w[o*in+i];
        y[o]=(float)acc;
    }
}

void softmax_inplace(float *x, int n){
    float m=x[0]; for(int i=1;i<n;i++) if(x[i]>m) m=x[i];
    double s=0.0; for(int i=0;i<n;i++){ x[i]=expf(x[i]-m); s+=x[i]; }
    for(int i=0;i<n;i++) x[i]/=(float)s;
}

int main(){
    const int C=8, H=8, W=8; // tiny spatial size for speed
    float *buf0 = (float*)calloc(C*H*W, sizeof(float));
    float *buf1 = (float*)calloc(C*H*W, sizeof(float));

    // Init input with a simple pattern
    for(int i=0;i<H;i++) for(int j=0;j<W;j++) buf0[i*W+j] = (float)( (i+j)%5 )/5.0f;

    // Allocate and init weights
    int wsize = C*C*3*3;
    float *w1 = (float*)malloc(sizeof(float)*wsize);
    float *w2 = (float*)malloc(sizeof(float)*wsize);
    float *b1 = (float*)malloc(sizeof(float)*C);
    float *b2 = (float*)malloc(sizeof(float)*C);
    init_weights(w1, wsize, 0.05f); init_bias(b1, C, 0.01f);
    init_weights(w2, wsize, 0.05f); init_bias(b2, C, 0.00f);

    // Two residual blocks
    residual_block(buf0, buf1, C,H,W, w1,b1, w2,b2);
    residual_block(buf0, buf1, C,H,W, w1,b1, w2,b2);

    // Head: GAP -> FC( C -> 2 ) -> softmax
    float gap[8];
    global_avg_pool(buf0,C,H,W,gap);

    float fc_w[2*C]; float fc_b[2];
    init_weights(fc_w, 2*C, 0.1f); init_bias(fc_b, 2, 0.0f);

    float logits[2];
    linear(gap, fc_w, fc_b, C, 2, logits);
    softmax_inplace(logits, 2);

    printf("Tiny ResNet-like demo. Output probs: [%.6f, %.6f]\\n", logits[0], logits[1]);

    int pred = (logits[0] > logits[1]) ? 0 : 1;
    printf("Predicted class: %d\\n", pred);

    // cleanup
    free(buf0); free(buf1); free(w1); free(w2); free(b1); free(b2);
    return 0;
}
