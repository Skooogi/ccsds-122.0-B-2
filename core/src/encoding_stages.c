#include "encoding_stages.h"
#include "common.h"
#include "file_io.h"
#include "word_mapping.h"
#include <stdio.h>

static void set_block_status(Block* block, uint8_t bitACMax, uint8_t bitplane);

void stage_0(SegmentData* segment_data) {

    int32_t* dc_coefficients = segment_data->dc_coefficients + segment_data->block_offset;
    size_t num_blocks = segment_data->headers->header_3.segment_size;
    uint8_t q = segment_data->q;
    uint8_t bitplane = segment_data->bitplane;

    if(3 > bitplane || bitplane >= q) {
        return;
    }

    //Encodes any remaining DC bits q > bitplane > 3
    for(size_t i = 0; i < num_blocks; ++i) {
        file_io_write_bits((dc_coefficients[i] >> bitplane) & 1, 1); 
    }
}

void stage_1(SegmentData* segment_data, size_t gaggle_offset, size_t gaggle_size) {

    uint8_t bitACMax = segment_data->headers->header_1.bitACMax;
    uint8_t bitplane = segment_data->bitplane;
    Block* blocks = segment_data->blocks + segment_data->block_offset + gaggle_offset;

    //Encodes all types[P] and corresponding signs for each block sequentally.
    //(4.5.3.1.8)
    for(size_t block_index = 0; block_index < gaggle_size; ++block_index) {
        if(blocks[block_index].bitAC <= bitplane) {
            continue;
        }

        set_block_status(&blocks[block_index], bitACMax, bitplane);
        
        //types_p and signs_p
        uint8_t types_p = 0;
        uint8_t signs_p = 0;
        uint8_t size_s = 0;
        uint8_t size_p = 0;

        for(uint8_t family = 0; family < 3; ++family) {

            //Each family has 21 ac coefficients with p as the first one.
            int8_t p = block_get_status(&blocks[block_index], family*21);
            if(family < 2 && (bitplane <= 2 || p < 0 || p > 1)) {
                continue;
            }
            if(family == 2 && (bitplane <= 1 || p < 0 || p > 1)) {
                continue;
            }

            types_p <<= 1;
            types_p |= p;
            size_p++;

            //If the ac coefficient is hit, save the sign.
            if(p) {
                signs_p <<= 1;
                signs_p |= (blocks[block_index].ac[family*21] >> bitACMax) & 1;
                size_s++;
            }
        }

        //Save generated words to block string.
        if(size_p > 0) {
            word_mapping_code(types_p, size_p, 0, 0);
            if(size_s > 0) {
                word_mapping_code(signs_p, size_s, 0, 1);
            }
        }
    }
}

void stage_2(SegmentData* segment_data, size_t gaggle_offset, size_t gaggle_size) {

    uint32_t bitACMax = segment_data->headers->header_1.bitACMax;
    uint8_t bitplane = segment_data->bitplane;
    Block* blocks = segment_data->blocks + segment_data->block_offset + gaggle_offset;

    //Encodes all types[C] and corresponding signs for each block sequentally.
    //(4.5.3.1.8)
    for(size_t block_index = 0; block_index < gaggle_size; ++block_index) { 
        if(blocks[block_index].bitAC <= bitplane) {
            continue;
        }

        //TRANB
        uint8_t bmax = block_get_bmax(&blocks[block_index]);

        if(blocks[block_index].tran.b != 1) {
            blocks[block_index].tran.b = bmax;
            word_mapping_code(blocks[block_index].tran.b, 1, 0, 1);
        }

        //All coefficients in the block are 0 and only TRANB is encoded.
        if(blocks[block_index].tran.b == 0) {
            continue;
        }

        //TRAND
        uint8_t tran_d = 0;
        uint8_t size = 0;

        for(uint8_t family = 0; family < 3; ++family) {

            uint8_t status = block_get_dmax(&blocks[block_index], family);
            if(family < 2 && (bitplane == 0 || (blocks[block_index].tran.d & (1 << (2-family))))) {
                continue;
            }
            if(family == 2 && (blocks[block_index].tran.d & (1 << (2-family)))) {
                continue;
            }

            tran_d <<= 1;
            tran_d |= status;
            size++;

            blocks[block_index].tran.d |= status << (2-family);
        }

        if(size != 0) {
            //Symbol option is 1 only when TRAND is 3b long.
            word_mapping_code(tran_d, size, size == 3 ? 1 : 0, 0);
        }

        //types_c and signs_c
        for(size_t ci = 0; ci < 3; ++ci) {
            if((ci == 0 && bitplane <= 1) || (ci == 1 && bitplane <= 1) || (ci == 2 && bitplane <= 0)) {
                continue;
            }
            if(!(blocks[block_index].tran.d & (1 << (2-ci)))) {
                continue;
            }

            uint8_t types_c = 0;
            uint8_t signs_c = 0;
            uint8_t size_s = 0;
            uint8_t size_c = 0;

            for(size_t cj = 0; cj < 4; ++cj) {
                size_t index = 1+ci*21+cj;
                int8_t status = block_get_status(&blocks[block_index], index);
                if(0 <= status && status <= 1) {
                    types_c <<= 1;
                    size_c += 1;
                    types_c |= status;
                    if(types_c & 1) {
                        signs_c <<= 1;
                        size_s += 1;
                        signs_c |= (blocks[block_index].ac[index] >> bitACMax) & 1;
                    }
                }
            }
            if(size_c != 0) {
                word_mapping_code(types_c, size_c, 0, 0);
                if(size_s != 0) {
                    word_mapping_code(signs_c, size_s, 0, 1);
                }
            }
        }
    }
}

void stage_3(SegmentData* segment_data, size_t gaggle_offset, size_t gaggle_size) {

    uint32_t bitACMax = segment_data->headers->header_1.bitACMax;
    uint8_t bitplane = segment_data->bitplane;
    Block* blocks = segment_data->blocks + segment_data->block_offset + gaggle_offset;

    for(size_t block_index = 0; block_index < gaggle_size; ++block_index) { 

        if(blocks[block_index].tran.b == 0) {
            continue;
        }

        if(blocks[block_index].bitAC <= bitplane) {
            continue;
        }

        //TRANG
        uint8_t size = 0;
        uint8_t tran_g = 0;

        for(uint8_t family = 0; family < 3; ++family) {

            uint8_t tran_d_hit = (blocks[block_index].tran.d & (1 << (2-family)));
            uint8_t tran_g_hit = (blocks[block_index].tran.g & (1 << (2-family)));

            uint8_t status = block_get_gmax(&blocks[block_index], family);
            if(family < 2 && (bitplane == 0 || !tran_d_hit || tran_g_hit)) {
                continue;
            }
            if(family == 2 && (!tran_d_hit || tran_g_hit)) {
                continue;
            }

            tran_g <<= 1;
            tran_g |= status;
            size++;

            blocks[block_index].tran.g |= status << (2-family);
        }

        if(size != 0) {
            word_mapping_code(tran_g, size, 0, 0);
        }

        //TRANH
        for(uint8_t hi = 0; hi < 3; ++hi) {

            if(!(blocks[block_index].tran.g & (1 << (2-hi)))) {
                continue;
            }
            if(hi < 2 && bitplane <= 0) {
                continue;
            }

            uint8_t tran_h = 0;
            uint8_t size = 0;
            for(uint8_t quadrant = 0; quadrant < 4; ++quadrant) {

                uint8_t tran_h_hit = (blocks[block_index].tran.h[hi] & (1 << (3-quadrant)));

                uint8_t status = block_get_hmax(&blocks[block_index], hi, quadrant);
                if(tran_h_hit) {
                    continue;
                }

                tran_h <<= 1;
                tran_h |= status;
                size++;

                blocks[block_index].tran.h[hi] |= status << (3-quadrant);
            }


            if(size != 0) {
                word_mapping_code(tran_h, size, size < 4 ? 0 : 1, 0);
            }
        }

        //types_h and signs_h
        for(uint8_t hi = 0; hi < 3; ++hi) {
            if(!(blocks[block_index].tran.g & (1 << (2-hi)))) {
                continue;
            }

            if(hi < 2 && bitplane <= 0) {
                continue;
            }

            for(uint8_t hj = 0; hj < 4; ++hj) {

                if(!(blocks[block_index].tran.h[hi] & (1 << (3-hj)))) {
                    continue;
                }
                
                uint8_t size_h = 0;
                uint8_t size_s = 0;
                uint8_t types_h = 0;
                uint8_t signs_h = 0;
                uint8_t index = hi*21+5+hj*4;

                for(uint8_t j = 0; j < 4; ++j) {
                    int8_t status = block_get_status(&blocks[block_index], index+j);
                    if(0 <= status && status <= 1) {
                        types_h <<= 1;
                        types_h |= ((blocks[block_index].ac[index+j] >> bitplane) & 1);
                        size_h += 1;
                        if(types_h & 1) {
                            signs_h <<= 1;
                            signs_h |= (blocks[block_index].ac[index+j] >> bitACMax) & 1;
                            size_s += 1;
                        }
                    }
                }
                if(size_h > 0) {
                    //Symbol option is 1 when types[H] is 4b long.
                    word_mapping_code(types_h, size_h, size_h == 4 ? 1 : 0, 0);
                    if(size_s > 0) {
                        word_mapping_code(signs_h, size_s, 0, 1);
                    }
                }
            }
        }
    }
}

void stage_4(SegmentData* segment_data) {

    uint8_t bitplane = segment_data->bitplane;
    Block* blocks = segment_data->blocks + segment_data->block_offset;

    for(size_t i = 0; i < segment_data->headers->header_3.segment_size; ++i) {
        if(blocks[i].bitAC <= bitplane) {
            continue;
        }

        //Bits for P coefficient.
        for(size_t pi = 0; pi < 3; ++pi) {
            size_t index = pi * 21;
            if(block_get_status(&blocks[i], index) == 2) {
                uint8_t temp = blocks[i].ac[index] >> bitplane & 1;
                file_io_write_bits(temp, 1);
            }
        }
        
        //Bits for C coefficients.
        for(size_t ci = 0; ci < 3; ++ci) {
            for(size_t j = 0; j < 4; ++j) {
                size_t index = 1 + ci * 21 + j;
                if(block_get_status(&blocks[i], index) == 2) {
                    uint8_t temp = blocks[i].ac[index] >> bitplane & 1;
                    file_io_write_bits(temp, 1);
                }
            }
        }

        //Bits for H coefficients.
        for(size_t hi = 0; hi < 3; ++hi) {
            for(size_t hj = 0; hj < 4; ++hj) {
                for(size_t j = 0; j < 4; ++j) {
                    size_t index = 5+hi*21+hj*4+j;
                    if(block_get_status(&blocks[i], index) == 2) {
                        uint8_t temp = blocks[i].ac[index] >> bitplane & 1;
                        file_io_write_bits(temp, 1);
                    }
                }
            }
        }
    }
}

static void set_block_status(Block* block, uint8_t bitACMax, uint8_t bitplane) {

        uint64_t new_high_status_bit = 0;
        uint64_t new_low_status_bit = 0;

        for(size_t ac_index = 0; ac_index < AC_COEFFICIENTS_PER_BLOCK; ++ac_index) {
            uint32_t ac_coefficient = block->ac[ac_index] & ~(1<<bitACMax);
            if(subband_lim(ac_index, bitplane)) {
                new_high_status_bit |= 1ll << ac_index;
                new_low_status_bit |= 1ll << ac_index;
            }
            else if((1<<(bitplane+1)) <= ac_coefficient) {
                new_high_status_bit |= 1ll << ac_index;
            }
            else if((1<<(bitplane)) <= ac_coefficient && ac_coefficient < (1<<(bitplane+1))) {
                new_low_status_bit |= 1ll << ac_index;
            }
        }
        block_set_status_with(block, new_high_status_bit, new_low_status_bit);
}
