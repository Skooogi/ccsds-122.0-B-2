#include "bitplane_encoder.h"
#include "file_io.h"
#include <stdlib.h>
#include <string.h>

static void fill_blocks();
static void calculate_bitdepths();
static void calculate_q_value();

#define COEFFICIENTS_PER_BLOCK 64
#define BLOCKS_PER_GAGGLE 16

static inline int32_t max(int32_t a, int32_t b) {  return (a > b) ? a : b; }
static inline int32_t min(int32_t a, int32_t b) {  return (a < b) ? a : b; }

static uint32_t log2_32 (uint32_t value) {

    /*
    static const uint32_t tab32[32] = {
        0,  9,  1, 10, 13, 21,  2, 29,
        11, 14, 16, 18, 22, 25,  3, 30,
        8, 12, 20, 28, 15, 17, 24,  7,
        19, 27, 23,  6, 26,  5,  4, 31
    };

    value |= value >> 1;
    value |= value >> 2;
    value |= value >> 4;
    value |= value >> 8;
    value |= value >> 16;
    return tab32[(uint32_t)(value*0x07C4ACDD) >> 27];
    */

    uint32_t result = 0;
    while(value > 1<<result) result++;
    return result;
}

typedef struct Block{

    unsigned bitAC  : 5;
    int32_t dc;
    int32_t* ac; 

} Block;

static void encode_dc_magnitudes(int32_t* dc_coefficients, int32_t num_coeffs, int32_t bitDC, int32_t q);

void bitplane_encoder_encode(int32_t* data, SegmentHeader* headers) {

    size_t num_blocks = headers->header_3.segment_size;
    size_t image_width = headers->header_4.image_width;
    size_t block_width = num_blocks / (image_width>>3);

    Block* blocks = malloc(num_blocks * sizeof(Block));
    memset(blocks, 0 , num_blocks * sizeof(Block));
    
    int32_t bitDC_max = 1;
    int32_t bitAC_max = 0;

    int32_t bitDC = 1;
    int32_t bitAC = 0;

    for(size_t block_index = 0; block_index < num_blocks; ++block_index) {

        size_t index_offset = (block_index / block_width) * image_width + block_index % block_width;
        bitDC = data[index_offset];
        if(bitDC < 0) {
            bitDC_max = max(bitDC_max, 1 + (log2_32(abs(bitDC))));
        }

        else {
            bitDC_max = max(bitDC_max, 1 + (log2_32(bitDC+1)));
        }

        for(size_t ac_index = 1; ac_index < COEFFICIENTS_PER_BLOCK; ++ ac_index) {
            bitAC = max(bitAC, abs(data[index_offset + ac_index]));
        }

        bitAC = log2_32(bitAC + 1);
        bitAC_max = max(bitAC_max, bitAC);
    }

    printf("max bitDC %u, bitACGlobal %u\n", bitDC_max, bitAC_max);
    headers->header_1.bitDC = bitDC_max;
    headers->header_1.bitAC = bitAC_max;
    segment_header_write_data(headers);
}

static int8_t select_coding(int32_t gaggle_sum, size_t J, size_t N) {
    //Heuristic way of selecting coding option k as in figure 4-10

    if(64*gaggle_sum > 23 * J * (1<<N)) {
        return -1;
    }

    else if(207 * J > 128 * gaggle_sum) {
        return 0;
    }

    else if(J*(1<<(N+5)) <= 128 * gaggle_sum + 49 * J) {
        return N-2;
    }

    uint8_t k = 1;
    while(J * (1<<(k+7)) <= 128 * gaggle_sum + 49) {
        k += 1;
    }

    return k;
}

static void split_coding(uint32_t* differences, size_t num_differences, uint32_t N, uint32_t* first) {

    uint32_t gaggle_sum = 0;
    for(size_t i = 0; i < min(BLOCKS_PER_GAGGLE, num_differences); ++i) {
        gaggle_sum += differences[i]; 
    }

    int8_t k = select_coding(gaggle_sum, num_differences, N);
    uint8_t code_word_length = log2_32(N);
    if(k < 0) {
        file_io_write_bits((1<<code_word_length) - 1, code_word_length);

        if(first) {
            file_io_write_bits(*first, N);
        }

        for(size_t i = 0; i < min(BLOCKS_PER_GAGGLE, num_differences); ++i) {
            file_io_write_bits(differences[i], N);
        }

        return;
    }

    file_io_write_bits(k, code_word_length);
    if(first){
        file_io_write_bits(*first, N);
    }

    for(size_t i = 0; i < min(BLOCKS_PER_GAGGLE, num_differences); ++i) {
        int32_t z = differences[i]/(1<<k);
        file_io_write_bits(0, z);
        file_io_write_bits(1, 1);
    }
    if(k){
        for(size_t i = 0; i < min(BLOCKS_PER_GAGGLE, num_differences); ++i) {
            file_io_write_bits(differences[i] & ((1 << k) -1), k);
        }
    }
}

static uint32_t twos_complement(int32_t value, size_t num_bits) {
    if(value & 1 << (num_bits - 1)) {
        return ~(value ^ 1 << (num_bits-1)) + 1 & (1<<(num_bits - 1));
    }
    return value;
}

static void encode_dc_magnitudes(int32_t* dc_coefficients, int32_t num_coeffs, int32_t bitDC, int32_t q) {

    //DC coding
    uint32_t N = max(bitDC - q, 1);

    for(size_t i = 0;  i < num_coeffs; ++i) {
        dc_coefficients[i] = twos_complement(dc_coefficients[i], bitDC);
        printf("%u ", dc_coefficients[i]);
    }
    
    if(N == 1) {
        for(size_t i = 0;  i < num_coeffs; ++i) {
            file_io_write_bits(dc_coefficients[i]>>q, 1);
        }

        return;
    }

    //First DC coefficient is uncoded
    uint32_t differences[num_coeffs];
    uint32_t shifted[num_coeffs];
    uint32_t mask_N_bits = (1 << N) - 1;
    for(size_t i = 0;  i < num_coeffs; ++i) {
        shifted[i] = dc_coefficients[i] >> q;
        if((shifted[i] & (1 << (N-1))) == 0) {
            continue;
        }
        shifted[i] = -(((shifted[i] ^ mask_N_bits) & mask_N_bits) + 1);
    }

    uint32_t last = shifted[0];
    uint32_t first = last;

    //Rest of the DC coefficients
    //4.3.2.4
    int32_t sigma, theta, res;
    for(size_t i = 1;  i < num_coeffs; ++i) {

        sigma = shifted[i] - last;
        theta = min(last + (1<<(N-1)), (1<<(N-1)) - 1 - last);
        last = shifted[i];
        res = 0;

        if(sigma >= 0 && sigma <= theta) {
            res = 2*sigma;
        }
        else if(sigma < 0 && sigma >= -theta) {
            res = -2*sigma-1;
        }
        else {
            res = theta + abs(sigma);
        }
        
        differences[i] = res;
    }

    split_coding(differences, num_coeffs, N, &first);
}
