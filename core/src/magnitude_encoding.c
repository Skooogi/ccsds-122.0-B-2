#include "magnitude_encoding.h"
#include "file_io.h"
#include <stdio.h>
#include <stdlib.h>

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

static void split_coding(int32_t* differences, size_t num_differences, uint32_t N, int32_t* first) {

    int32_t gaggle_sum;
    size_t index;
    for(size_t i = 0; i < (num_differences>>4) + 1; ++i) {
        gaggle_sum = 0;
        
        for(size_t j = i == 0 ? 1 : 0; j < 16; ++j) {
            index = i*16+j;
            if(index >= num_differences) {
                break;
            }
            gaggle_sum += differences[index];
        }
        
        size_t J = i == 0 ? 15 : 16;

        size_t k = select_coding(gaggle_sum, J, N);
        size_t code_word_length = log2_32(N);
        if(k < 0){
            file_io_write_bits((1<<code_word_length) - 1, code_word_length);

            if(i == 0){
                file_io_write_bits(*first, N);
            }

            for(size_t j = i == 0 ? 1 : 0; j < 16; ++j) {
                index = i*16+j;
                if(index >= num_differences) {
                    break;
                }
                file_io_write_bits(differences[index], N);
            }
            continue;
        }

        file_io_write_bits(k, code_word_length);
        if(i == 0) {
            file_io_write_bits(*first, N);
        }

        for(size_t j = i == 0 ? 1 : 0; j < 16; ++j) {
            index = i*16+j;
            if(index >= num_differences) {
                break;
            }
            size_t z = (differences[index]>>k);
            file_io_write_bits(0, z);
            file_io_write_bits(1, 1);
        }

        if(k != 0) {
            for(size_t j = i == 0 ? 1 : 0; j < 16; ++j) {
                index = i*16+j;
                if(index >= num_differences) {
                    break;
                }
                file_io_write_bits(differences[index] & ((1 << k) -1), k);
            }
        }
    }
}

void encode_dc_magnitudes(int32_t* dc_coefficients, int32_t num_coeffs, int32_t bitDC, int32_t q) {

    //DC coding
    uint32_t N = max(bitDC - q, 1);

    for(size_t i = 0;  i < num_coeffs; ++i) {
        dc_coefficients[i] = twos_complement(dc_coefficients[i], bitDC);
    }
    
    if(N == 1) {
        for(size_t i = 0;  i < num_coeffs; ++i) {
            file_io_write_bits(dc_coefficients[i]>>q, 1);
        }
        return;
    }

    //First DC coefficient is uncoded
    int32_t differences[num_coeffs];
    int32_t shifted[num_coeffs];
    int32_t mask_N_bits = (1 << N) - 1;
    for(size_t i = 0;  i < num_coeffs; ++i) {
        shifted[i] = dc_coefficients[i] >> q;
        if((shifted[i] & (1 << (N-1))) == 0) {
            continue;
        }
        shifted[i] = -(((shifted[i] ^ mask_N_bits) & mask_N_bits) + 1);
    }

    int32_t last = shifted[0];
    int32_t first = last;

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

void encode_ac_magnitudes(Block* blocks, size_t num_blocks, uint32_t bitAC_max, uint32_t q) {

    uint32_t N = (log2_32(1 + bitAC_max));
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
             
    int32_t differences[num_blocks];

    int32_t last = blocks[0].bitAC;
    int32_t first = last;
    differences[0] = first;
    
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
        differences[i] = res;
    }

    split_coding(differences, num_blocks, N, &first);
}
