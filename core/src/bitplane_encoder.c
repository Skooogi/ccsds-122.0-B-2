#include "bitplane_encoder.h"
#include "block_transform.h"
#include "common.h"
#include "encoding_stages.h"
#include "file_io.h"
#include "magnitude_encoding.h"
#include "segment_header.h"
#include "word_mapping.h"
#include <stdlib.h>
#include <string.h>

static uint8_t calculate_q_value(uint32_t bitDC_max, uint32_t bitAC_max);

void bitplane_encoder_encode(int16_t* data, SegmentHeader* headers) {

    size_t num_blocks = headers->header_3.segment_size;
    int32_t bitDC_max = 1;
    int32_t bitAC_max = 0;
    int32_t bitAC = 0;

    int32_t* dc_coefficients = calloc(num_blocks, sizeof(int32_t));
    Block* blocks = calloc(num_blocks, sizeof(Block));

    block_transform_pack(blocks, num_blocks, data, headers->header_4.image_width);
    for(size_t block_index = 0; block_index < num_blocks; ++block_index) {

        dc_coefficients[block_index] = blocks[block_index].dc;
        int32_t current_dc = (dc_coefficients[block_index]);
        if(current_dc < 0) {
            bitDC_max = max(bitDC_max, 1 + (log2_32_ceil(abs(current_dc))));
        }

        else {
            bitDC_max = max(bitDC_max, 1 + (log2_32_ceil(current_dc+1)));
        }

        int32_t max_AC = 0;
        for(size_t ac_index = 0; ac_index < AC_COEFFICIENTS_PER_BLOCK; ++ac_index) {
            max_AC = max(max_AC, abs(blocks[block_index].ac[ac_index]));
        }
        bitAC = log2_32_ceil(max_AC + 1);
        blocks[block_index].bitAC = bitAC;
        bitAC_max = max(bitAC_max, bitAC);
    }
    uint8_t q = calculate_q_value(bitDC_max, bitAC_max);
    printf("max bitDC %u, bitAC_max %u, q %u\n", bitDC_max, bitAC_max, q);

    //Transform ac coefficients to sign-magnitude representation
    for(size_t block_index = 0; block_index < num_blocks; ++block_index) {
        blocks[block_index].tran.packed = 0; 
        blocks[block_index].dc &= (1<<bitDC_max) - 1;
        for(size_t ac_index = 0; ac_index < AC_COEFFICIENTS_PER_BLOCK; ++ac_index) {
            int32_t ac_coefficient = blocks[block_index].ac[ac_index];

            blocks[block_index].ac[ac_index] = twos_complement(ac_coefficient, bitAC_max);
            blocks[block_index].ac[ac_index] |= ac_coefficient < 0 ? (1 << bitAC_max) : 0;
        }
    }

    headers->header_1.bitDC = bitDC_max;
    headers->header_1.bitAC = bitAC_max;

    segment_header_write_data(headers);
    encode_dc_magnitudes(dc_coefficients, num_blocks, bitDC_max, q);

    //Make sure user parameters limit the used stages
    uint8_t end_stage = headers->header_2.stage_stop;
    int8_t end_bitplane = headers->header_2.bitplane_stop;
    //Decode shifted out DC bits
    if(q > bitAC_max) {
        uint8_t limit = 0;
        if(bitAC_max > 2) {
            limit = q - bitAC_max;
        }
        else {
            limit = q - 2;
        }

        for(int8_t offset = 0; offset < limit; ++offset) {
            for(size_t block_index = 0; block_index < num_blocks; ++block_index) {
                file_io_write_bits((dc_coefficients[block_index] >> (q - offset)) & 1, 1);
            }
        }
    }

    encode_ac_magnitudes(blocks, num_blocks, bitAC_max, q);

    for(int8_t bitplane = bitAC_max - 1; bitplane >= end_bitplane; --bitplane) {
        stage_0(blocks, num_blocks, q, bitplane);
        if(headers->header_2.dc_stop == 1) {
            continue;
        }
        for(size_t gaggle = 0; gaggle < num_blocks; gaggle+=16) {
            reset_block_string();
            
            uint32_t start = get_bits_written();
            for(size_t stage = 0; stage <= end_stage; ++stage) {

                size_t blocks_in_gaggle = gaggle + 16 < num_blocks ? 16 : num_blocks - gaggle;
                uint32_t start_bits = get_bitstring_length();

                if(stage == 0) {
                    stage_1(headers, blocks+gaggle, blocks_in_gaggle, bitplane);
                }
                else if(stage == 1) {
                    stage_2(headers, blocks+gaggle, blocks_in_gaggle, bitplane);
                }
                else if(stage == 2) {
                    stage_3(headers, blocks+gaggle, blocks_in_gaggle, bitplane);
                }

                printf("Written in stage (%u): %u\n", stage + 1, get_bitstring_length() - start_bits);
            }
            write_block_string();
            printf("%u) Written in gaggle: %u\n", bitplane, get_bits_written() - start);
        }

        if(end_stage == 3) {
            stage_4(headers, blocks, num_blocks, bitplane);
        }
    }
    free(dc_coefficients);
    free(blocks);
}

static uint8_t calculate_q_value(uint32_t bitDC_max, uint32_t bitAC_max) {
    
    uint8_t q_prime = 0;
    if(bitDC_max <= 3) {
        q_prime = 0;
    }
    else if(bitDC_max - (1 + (bitAC_max>>1)) <= 1 && bitDC_max > 3) {
        q_prime = bitDC_max - 3;
    }
    else if(bitDC_max - (1 + (bitAC_max>>1)) > 10 && bitDC_max > 3) {
        q_prime = bitDC_max - 10;
    }
    else {
        q_prime = 1 + (bitAC_max>>1);
    }
    return max(q_prime, 3);
} 
