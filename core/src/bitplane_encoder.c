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
static void initialize_segment_data(SegmentData* segment_data);
static void initialize_segment_header(SegmentData* segment_data, uint32_t segment_index, size_t num_segments, size_t num_blocks_total);
static void encode_shifted_dc_bits(SegmentData* segment_data);
static void encode_stages(SegmentData* segment_data);

void bitplane_encoder_encode(int16_t* data, SegmentHeader* headers) {

    size_t num_blocks_total = headers->header_3.segment_size;
    size_t num_blocks = min(BLOCKS_PER_SEGMENT, num_blocks_total);
    size_t num_gaggles = num_blocks / BLOCKS_PER_GAGGLE + (num_blocks % BLOCKS_PER_GAGGLE != 0);
    size_t num_segments = num_blocks_total / num_blocks + (num_blocks_total % num_blocks != 0);

    int32_t* dc_coefficients = calloc(num_blocks_total, sizeof(int32_t));
    Block* blocks = calloc(num_blocks_total, sizeof(Block));
    BlockString* block_strings = calloc(num_gaggles, sizeof(BlockString));
    
    //Data is transferred from the transformed image to a array of blocks.
    //Both are allocated simultaneously effectively doubling the required memory for an image.
    //(With clever indexing this should be possible to do per segment or even in place.)
    block_transform_pack(blocks, dc_coefficients, num_blocks_total, data, headers->header_4.image_width);
    free(data);

    //SegmentData holds internal state and data for a segment.
    //This struct is reused for all segments overwriting the previous data.
    SegmentData segment_data = {};
    segment_data.block_strings = block_strings;
    segment_data.blocks = blocks;
    segment_data.dc_coefficients = dc_coefficients;
    segment_data.headers = headers;
    
    for(uint32_t segment_index = 0; segment_index < num_segments; ++segment_index) {

        //Every segment must be padded to code word size (in this case 8).
        if(get_bits_written() % 8) {
            file_io_write_bits(0, 8 - (get_bits_written() % 8));
        }

        //Initializes offsets and checks for bounds.
        initialize_segment_header(&segment_data, segment_index, num_segments, num_blocks_total);

        //Calculates bitdepths and q value for the segment.
        initialize_segment_data(&segment_data);

        //Writes header for current segment
        segment_header_write_data(headers);

        //Magnitude encoding
        encode_dc_magnitudes(&segment_data);
        encode_shifted_dc_bits(&segment_data);
        encode_ac_magnitudes(&segment_data);

        //All stages are encoded for each bitplane as in Figure 4-2
        for(int8_t bitplane = headers->header_1.bitACMax - 1; bitplane >= headers->header_2.bitplane_stop; --bitplane) {

            segment_data.bitplane = bitplane;

            stage_0(&segment_data);

            if(headers->header_2.dc_stop == 1) {
                continue;
            }

            encode_stages(&segment_data);
        }
    }

    free(dc_coefficients);
    free(blocks);
    free(block_strings);
}

static void initialize_segment_data(SegmentData* segment_data) {

    size_t num_blocks = segment_data->headers->header_3.segment_size;
    int32_t* dc_coefficients = segment_data->dc_coefficients + segment_data->block_offset;
    Block* blocks = segment_data->blocks + segment_data->block_offset;

    int32_t bitDC_max = 1;
    int32_t bitAC_max = 0;
    int32_t bitAC = 0;

    //Calculate bitACMax and bitDCMax for this segment. (4.1)
    for(size_t block_index = 0; block_index < num_blocks; ++block_index) {

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

    for(size_t block_index = 0; block_index < num_blocks; ++block_index) {
        blocks[block_index].tran.packed = 0; 
        dc_coefficients[block_index] &= (1<<bitDC_max) - 1;

        //Transform ac coefficients to sign-magnitude representation
        for(size_t ac_index = 0; ac_index < AC_COEFFICIENTS_PER_BLOCK; ++ac_index) {
            int32_t ac_coefficient = blocks[block_index].ac[ac_index];

            blocks[block_index].ac[ac_index] = twos_complement(ac_coefficient, bitAC_max);
            blocks[block_index].ac[ac_index] |= ac_coefficient < 0 ? (1 << bitAC_max) : 0;
        }
    }

    segment_data->q = calculate_q_value(bitDC_max, bitAC_max);
    segment_data->headers->header_1.bitDCMax = bitDC_max;
    segment_data->headers->header_1.bitACMax = bitAC_max;
}

static void initialize_segment_header(SegmentData* segment_data, uint32_t segment_index, size_t num_segments, size_t num_blocks_total) {
    //Helpers for accessing "segment size" elements starting at "block offset".
    //Last segments with differing length, when num_blocks_total % segment_size != 0, are accounted for.

    size_t num_blocks = min(BLOCKS_PER_SEGMENT, num_blocks_total);
    size_t num_gaggles = num_blocks / BLOCKS_PER_GAGGLE + (num_blocks % BLOCKS_PER_GAGGLE != 0);

    segment_data->block_offset = segment_index * num_blocks;

    //Check indexing bounds for segment size.
    segment_data->headers->header_3.segment_size = num_blocks;
    if(segment_data->block_offset + num_blocks >= num_blocks_total) {
        segment_data->headers->header_3.segment_size = num_blocks_total - segment_data->block_offset;
    }

    //Check indexing bounds for the number of gaggles.
    segment_data->num_gaggles = num_gaggles;
    if(segment_data->headers->header_3.segment_size < num_blocks) {
        segment_data->num_gaggles = segment_data->headers->header_3.segment_size / BLOCKS_PER_GAGGLE; 
        segment_data->num_gaggles += (segment_data->headers->header_3.segment_size % BLOCKS_PER_GAGGLE != 0);
    }

    segment_data->headers->header_1.first_segment = segment_index == 0 ? 1 : 0;
    segment_data->headers->header_1.last_segment = segment_index == num_segments-1 ? 1 : 0;
    segment_data->headers->header_1.segment_index = segment_index;
}

static uint8_t calculate_q_value(uint32_t bitDC_max, uint32_t bitAC_max) {
    
    //Calculates q as shown in figure 4-8.
    //q is always at least LL3 = 3.

    //Dynamic range is small -> no quantization.
    if(bitDC_max <= 3) {
        return max(0, 3);
    }

    //Dynamic range of DC is almost half the dynamic range of AC.
    //3 MSB are quantized.
    if(bitDC_max - (1 + (bitAC_max>>1)) <= 1 && bitDC_max > 3) {
        return max(bitDC_max - 3, 3);
    }

    //Dynamic range of DC is much larger than half the dynamic range of AC.
    //10 MSB are quantized.
    if(bitDC_max - (1 + (bitAC_max>>1)) > 10 && bitDC_max > 3) {
        return max(bitDC_max - 10, 3);
    }

    //Dynamic range of DC is somewhat larger than half the dynamic range of AC.
    //DC > AC/2 bits are quantized.
    return max(1 + (bitAC_max>>1), 3);
} 

static void encode_shifted_dc_bits(SegmentData* segment_data) {

    uint8_t q = segment_data->q;
    uint8_t bitACMax = segment_data->headers->header_1.bitACMax;
    int32_t* dc_coefficients = segment_data->dc_coefficients + segment_data->block_offset;
    size_t segment_size = segment_data->headers->header_3.segment_size;

    uint8_t bitshift_LL3 = 3;
    if(segment_data->headers->header_4.custom_weights) {
        bitshift_LL3 = segment_data->headers->header_4.custom_weight_LL_3;
    }

    if(q <= max(bitACMax, bitshift_LL3)) {
        return;
    }
    
    //q is atleast 3 and limit must be non-negative.
    uint8_t limit = bitACMax > 2 ? q - bitACMax : q - 2;

    //Encodes bitplanes that are larger than q
    for(int8_t offset = 0; offset < limit; ++offset) {
        for(size_t block_index = 0; block_index < segment_size; ++block_index) {
            file_io_write_bits((dc_coefficients[block_index] >> (q - offset)) & 1, 1);
        }
    }
}

static void encode_stages(SegmentData* segment_data) {

    BlockString* block_strings = segment_data->block_strings;
    uint8_t end_stage = segment_data->headers->header_2.stage_stop;
    size_t num_gaggles = segment_data->num_gaggles;
    size_t num_blocks = segment_data->headers->header_3.segment_size;

    //Reset all block strings for reuse.
    memset(segment_data->block_strings, 0, num_gaggles*sizeof(BlockString));

    //Every word generated in this loop gets stored in the corresponding block string for each gaggle.
    //This is mandatory to calculate optimal code words (4.5.3.3.3.).
    //Required memory scales with segment size.
    //Larger segments have more gaggles and thus require more memory.
    for(size_t stage = 0; stage <= end_stage; ++stage) {
        for(size_t gaggle = 0; gaggle < num_gaggles; ++gaggle) {
            if(stage == 3) {
                continue;
            }

            //Each BlockString is separated for stages 1-3.
            block_strings[gaggle].stage = stage;
            set_block_string(&block_strings[gaggle]);

            //Makes sure indexing does not read more blocks than are allocated.
            size_t blocks_in_gaggle = 16;
            if(gaggle * BLOCKS_PER_GAGGLE + BLOCKS_PER_GAGGLE >= num_blocks) {
                blocks_in_gaggle = segment_data->headers->header_3.segment_size - gaggle * BLOCKS_PER_GAGGLE;
            }

            //Makes sure the last gaggle is not larger than the current segment.
            //Only happens if segment consists of less than 16 blocks.
            if(blocks_in_gaggle > segment_data->headers->header_3.segment_size) {
                blocks_in_gaggle = segment_data->headers->header_3.segment_size;
            }

            size_t gaggle_offset = gaggle * BLOCKS_PER_GAGGLE;
            if(stage == 0) {
                stage_1(segment_data, gaggle_offset, blocks_in_gaggle);
            }
            else if(stage == 1) {
                stage_2(segment_data, gaggle_offset, blocks_in_gaggle);
            }
            else if(stage == 2) {
                stage_3(segment_data, gaggle_offset, blocks_in_gaggle);
            }
        }
    }

    //Write stages to file in order given in figure 4-2
    for(size_t stage = 0; stage <= end_stage; ++stage) {
        if(stage == 3) {
            break;
        }

        for(size_t gaggle = 0; gaggle < num_gaggles; ++gaggle) {
            block_strings[gaggle].stage = stage;
            set_block_string(&block_strings[gaggle]);
            write_block_string();
        }
    }

    //Stage 4 consists of single bits, and like Stage 0, is not dependent on code options.
    if(end_stage == 3) {
        stage_4(segment_data);
    }
}
