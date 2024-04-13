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

#define BLOCKS_PER_SEGMENT 32

extern inline int32_t max(int32_t a, int32_t b);
extern inline int32_t min(int32_t a, int32_t b);
static uint8_t calculate_q_value(uint32_t bitDC_max, uint32_t bitAC_max);
static void initialize_internal_data(Block* blocks, int32_t* dc_coefficients, SegmentHeader* headers);

void bitplane_encoder_encode(int16_t* data, SegmentHeader* headers) {

    size_t num_blocks_total = headers->header_3.segment_size;
    size_t num_blocks = min(BLOCKS_PER_SEGMENT, num_blocks_total);
    size_t num_segments = num_blocks_total / num_blocks + (num_blocks_total % num_blocks != 0);
    size_t num_gaggles = num_blocks / BLOCKS_PER_GAGGLE + (num_blocks % BLOCKS_PER_GAGGLE != 0);

    int32_t* dc_coefficients = calloc(num_blocks_total, sizeof(int32_t));
    Block* blocks = calloc(num_blocks_total, sizeof(Block));
    BlockString* block_strings = calloc(num_gaggles, sizeof(BlockString));
    
    block_transform_pack(blocks, num_blocks_total, data, headers->header_4.image_width);
    free(data);
    
    for(uint32_t segment_index = 0; segment_index < num_segments; ++segment_index) {
        if(get_bits_written() % 8) {
            file_io_write_bits(0, 8 - (get_bits_written() % 8));
        }
        size_t block_offset = segment_index * num_blocks;
        size_t segment_size = block_offset + num_blocks < num_blocks_total ? num_blocks : num_blocks_total - block_offset;
        if(segment_size < num_blocks) {
            num_gaggles = segment_size / BLOCKS_PER_GAGGLE + (segment_size % BLOCKS_PER_GAGGLE != 0);
        }

        headers->header_1.first_segment = segment_index == 0 ? 1 : 0;
        headers->header_1.last_segment = segment_index == num_segments-1 ? 1 : 0;
        headers->header_1.num_segments = segment_index;
        headers->header_3.segment_size = segment_size; //Encode correct segment size
        initialize_internal_data(blocks+block_offset, dc_coefficients+block_offset, headers);
        int32_t bitDC_max = headers->header_1.bitDC;
        int32_t bitAC_max = headers->header_1.bitAC;
        uint8_t q = calculate_q_value(bitDC_max, bitAC_max);
        
        //Write header for current segment
        uint32_t start = get_bits_written();
        segment_header_write_data(headers);

        //Magnitude encoding start
        start = get_bits_written();
        encode_dc_magnitudes(dc_coefficients + block_offset, segment_size, bitDC_max, q);

        //Make sure user parameters limit the used stages
        uint8_t end_stage = headers->header_2.stage_stop;
        uint8_t end_bitplane = headers->header_2.bitplane_stop;

        //Encode shifted out DC bits
        if(q > bitAC_max) {
            uint8_t limit = bitAC_max > 2 ? q - bitAC_max : q - 2;

            for(int8_t offset = 0; offset < limit; ++offset) {
                for(size_t block_index = 0; block_index < segment_size; ++block_index) {
                    file_io_write_bits((dc_coefficients[block_offset + block_index] >> (q - offset)) & 1, 1);
                }
            }
        }

        encode_ac_magnitudes(blocks + block_offset, segment_size, bitAC_max, q);
        //Magnitude encoding

        uint32_t max_index_1 = 0;
        uint32_t max_index_2 = 0;
        uint32_t max_index_3 = 0;
        for(int8_t bitplane = bitAC_max - 1; bitplane >= end_bitplane; --bitplane) {
            stage_0(blocks + block_offset, segment_size, q, bitplane);
            if(headers->header_2.dc_stop == 1) {
                continue;
            }

            //Reset all block strings
            memset(block_strings, 0, num_gaggles*sizeof(BlockString));
            uint32_t start = get_bits_written();
            for(size_t stage = 0; stage <= end_stage; ++stage) {
                for(size_t gaggle = 0; gaggle < num_gaggles; ++gaggle) {
                    if(stage == 3) {
                        continue;
                    }
                    block_strings[gaggle].stage = stage;
                    set_block_string(&block_strings[gaggle]);

                    size_t blocks_in_gaggle = gaggle * 16 + 16 < num_blocks ? 16 : segment_size - gaggle*16;
                    if(blocks_in_gaggle > segment_size) {
                        blocks_in_gaggle = segment_size;
                    }

                    if(stage == 0) {
                        stage_1(headers, blocks+block_offset+gaggle*16, blocks_in_gaggle, bitplane);
                    }
                    else if(stage == 1) {
                        stage_2(headers, blocks+block_offset+gaggle*16, blocks_in_gaggle, bitplane);
                    }
                    else if(stage == 2) {
                        stage_3(headers, blocks+block_offset+gaggle*16, blocks_in_gaggle, bitplane);
                    }
                }
            }

            //Write stages to file in order given in figure 4-2
            for(size_t stage = 0; stage <= end_stage; ++stage) {
                if(stage == 3) {
                    break;
                }
                for(size_t gaggle = 0; gaggle < num_gaggles; ++gaggle) {
                    max_index_1 = max(max_index_1, block_strings[gaggle].index[0]);
                    max_index_2 = max(max_index_2, block_strings[gaggle].index[1]);
                    max_index_3 = max(max_index_3, block_strings[gaggle].index[2]);

                    block_strings[gaggle].stage = stage;
                    set_block_string(&block_strings[gaggle]);
                    write_block_string();
                }
            }

            if(end_stage == 3) {
                stage_4(headers, blocks+block_offset, segment_size, bitplane);
            }

        }
    }

    //printf("%lu %lu %lu\n", max_index_1, max_index_2, max_index_3);
    free(dc_coefficients);
    free(blocks);
    free(block_strings);
}

static void initialize_internal_data(Block* blocks, int32_t* dc_coefficients, SegmentHeader* headers) {

    int32_t bitDC_max = 1;
    int32_t bitAC_max = 0;
    int32_t bitAC = 0;
    size_t num_blocks = headers->header_3.segment_size;

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
