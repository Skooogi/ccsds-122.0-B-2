#include "bitplane_encoder.h"
#include "block_transform.h"
#include "common.h"
#include "encoding_stages.h"
#include "file_io.h"
#include "magnitude_encoding.h"
#include "word_mapping.h"
#include <stdlib.h>
#include <string.h>

static uint8_t calculate_q_value(uint32_t bitDC_max, uint32_t bitAC_max);

void bitplane_encoder_encode(int32_t* data, SegmentHeader* headers) {

    size_t num_blocks = headers->header_3.segment_size;
    int32_t bitDC_max = 1;
    int32_t bitAC_max = 0;
    int32_t bitDC = 1;
    int32_t bitAC = 0;

    int32_t dc_coefficients[num_blocks];

    Block blocks[num_blocks];
    block_transfrom_pack((Block*)&blocks, num_blocks, data, headers->header_4.image_width);

    for(size_t block_index = 0; block_index < num_blocks; ++block_index) {

        bitDC = blocks[block_index].dc;
        dc_coefficients[block_index] = bitDC;
        printf("%i ", dc_coefficients[block_index]);
        if(bitDC < 0) {
            bitDC_max = max(bitDC_max, 1 + (log2_32(abs(bitDC))));
        }

        else {
            bitDC_max = max(bitDC_max, 1 + (log2_32(bitDC+1)));
        }

        bitAC = 0;
        for(size_t ac_index = 0; ac_index < AC_COEFFICIENTS_PER_BLOCK; ++ac_index) {
            bitAC = max(bitAC, abs(blocks[block_index].ac[ac_index]));
        }
        bitAC = log2_32(bitAC + 1);
        blocks[block_index].bitAC = bitAC;
        bitAC_max = max(bitAC_max, bitAC);
    }

    uint8_t q = calculate_q_value(bitDC_max, bitAC_max);

    printf("max bitDC %u, bitAC_max %u, q %u\n", bitDC_max, bitAC_max, q);
    headers->header_1.bitDC = bitDC_max;
    headers->header_1.bitAC = bitAC_max;
    segment_header_write_data(headers);

    encode_dc_magnitudes(dc_coefficients, num_blocks, bitDC_max, q);
    encode_ac_magnitudes((Block*)&blocks, num_blocks, bitAC_max, q);

    for(int8_t bitplane = bitAC_max - 1; bitplane > -1; --bitplane) {
        for(size_t stage = 0; stage < 3; ++stage) {
            for(size_t gaggle = 0; gaggle < num_blocks; gaggle+=16) {

                reset_block_string();

                if(stage == 0) {
                    stage_0(blocks, num_blocks, q, bitplane);
                }
                else if(stage == 1) {
                    stage_1(blocks, num_blocks, bitplane);
                }

                write_block_string();
            }

        }
    }
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
