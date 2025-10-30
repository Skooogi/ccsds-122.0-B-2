// Original copyright: Aalto University
// Modifications copyright: Huld Ltd.
// Project: EnVisS ASW (for Comet Interceptor mission)

#include "magnitude_encoding.h"
#include "common.h"
#include "file_io.h"
#include <stdio.h>
#include <stdlib.h>
#include "asw_types.h"


static int32_t *differences_buf;

static int32_t *shifted_buf;

static int32_t select_coding(int32_t gaggle_sum, size_t J, size_t N);
static void split_coding(int32_t* differences, size_t num_differences, uint32_t N, int32_t* first);

void magnitude_encoding_set_buffers(int32_t *differences_addr, int32_t *shifted_addr)
{
    differences_buf = differences_addr;
    shifted_buf = shifted_addr;
}

void encode_dc_magnitudes(SegmentData* segment_data) {

    int32_t* dc_coefficients = segment_data->dc_coefficients + segment_data->block_offset;
    int32_t num_coeffs = segment_data->headers->header_3.segment_size;
    int32_t bitDC = segment_data->headers->header_1.bitDCMax;
    int32_t q = segment_data->q;

    //DC coding
    uint32_t N = (uint32_t) max(bitDC - q, 1);

    if(N == 1) {
        for(size_t i = 0;  i < (size_t) num_coeffs; ++i) {
            file_io_write_bits((uint64_t) (dc_coefficients[i]>>q), 1);
        }
        return;
    }

    //First DC coefficient is uncoded
    int32_t mask_N_bits = (1 << N) - 1;
    for(size_t i = 0;  i < (size_t) num_coeffs; ++i) {
        shifted_buf[i] = (dc_coefficients[i] >> q) & ((1<<20) - 1);
        if((shifted_buf[i] & (1 << (N-1))) == 0) {
            continue;
        }
        shifted_buf[i] = -(((shifted_buf[i] ^ mask_N_bits) & mask_N_bits) + 1);
    }

    int32_t last = shifted_buf[0];
    int32_t first = last;

    //Rest of the DC coefficients
    //4.3.2.4
    int32_t sigma, theta, res;
    for(size_t i = 1;  i < (size_t) num_coeffs; ++i) {

        sigma = shifted_buf[i] - last;
        theta = min(last + (1<<(N-1)), (1<<(N-1)) - 1 - last);
        last = shifted_buf[i];
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

        differences_buf[i] = res;
    }

    split_coding(differences_buf, (size_t) num_coeffs, N, &first);
}

void encode_ac_magnitudes(SegmentData* segment_data) {
    Block* blocks = segment_data->blocks + segment_data->block_offset;
    size_t num_blocks = segment_data->headers->header_3.segment_size;
    uint32_t bitAC_max = segment_data->headers->header_1.bitACMax;

    uint32_t N = log2_32_ceil(1 + bitAC_max);
    if(N == 0) {
        return;
    }

    if(N == 1) {
        //Coefficients are 1 bit long and no further coding is required
        for(size_t i = 1; i < num_blocks; ++i) {
            file_io_write_bits(blocks[i].bitAC, 1);
        }
        return;
    }

    int32_t last = blocks[0].bitAC;
    int32_t first = last;
    differences_buf[0] = first;

    //Rest of the AC coefficients
    //4.3.2.4
    int32_t sigma, theta, res;
    for(size_t i = 1; i < num_blocks; ++i) {
        sigma = (blocks[i].bitAC) - last;
        theta = min(last, (1<<N) - 1 - last);
        last = (blocks[i].bitAC);
        res = 0;

        if(sigma >= 0 && sigma <= theta) {
            res = sigma<<1;
        }
        else if(sigma < 0 && sigma >= -theta) {
            res = (abs(sigma)<<1) - 1;
        }
        else{
            res = theta + abs(sigma);
        }
        differences_buf[i] = res;
    }

    split_coding(differences_buf, num_blocks, N, &first);
}

static int32_t select_coding(int32_t gaggle_sum, size_t J, size_t N) {
    //Heuristic way of selecting coding option k as in figure 4-10
    if( (size_t) (64*gaggle_sum) >= (23 * J * (size_t) (1<<N))) {
        return -1;
    }

    else if(207 * J > (size_t) (128 * gaggle_sum)) {
        return 0;
    }

    else if((int64_t)(J*(size_t) (1<<(N+5))) <= (int64_t)((size_t) (128 * gaggle_sum) + 49 * J)) {
        return (int32_t) (N-2);
    }

    int32_t k = 0;
    while((int64_t)(J * (size_t) (1<<(k+7))) <= (int64_t)((size_t) (128 * gaggle_sum) + 49 * J)) {
        k += 1;
    }

    return k-1;
}

static void split_coding(int32_t* differences, size_t num_differences, uint32_t N, int32_t* first) {

    int32_t gaggle_sum;
    size_t index;

    uint8_t gaggle_has_remainder = num_differences % 16 ? 1 : 0;
    for(size_t i = 0; i < (num_differences>>4) + gaggle_has_remainder; ++i) {
        gaggle_sum = 0;

        for(size_t j = i == 0 ? 1 : 0; j < 16; ++j) {
            index = i*16+j;
            if(index >= num_differences) {
                break;
            }
            gaggle_sum += differences[index];
        }

        size_t J = i == 0 ? 15 : 16;

        int32_t k = select_coding(gaggle_sum, J, N);
        size_t code_word_length = log2_32_ceil(N);
        if(k < 0){
            file_io_write_bits((uint64_t) ((1<<code_word_length) - 1), code_word_length);

            if(i == 0){
                file_io_write_bits((uint64_t) (*first), N);
            }

            for(size_t j = i == 0 ? 1 : 0; j < 16; ++j) {
                index = i*16+j;
                if(index >= num_differences) {
                    break;
                }
                file_io_write_bits((uint64_t) (differences[index]), N);
            }
            continue;
        }

        file_io_write_bits((uint64_t) k, code_word_length);
        if(i == 0) {
            file_io_write_bits((uint64_t) (*first), N);
        }

        for(size_t j = i == 0 ? 1 : 0; j < 16; ++j) {
            index = i*16+j;
            if(index >= num_differences) {
                break;
            }
            size_t z = (size_t) (differences[index]>>k);
            file_io_write_bits(0, z);
            file_io_write_bits(1, 1);
        }

        if(k != 0) {
            for(size_t j = i == 0 ? 1 : 0; j < 16; ++j) {
                index = i*16+j;
                if(index >= num_differences) {
                    break;
                }
                file_io_write_bits((uint64_t) (differences[index] & ((1 << k) -1)), (size_t) k);
            }
        }
    }
}
