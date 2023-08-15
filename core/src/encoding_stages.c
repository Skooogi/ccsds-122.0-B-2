#include "encoding_stages.h"
#include "word_mapping.h"
#include <stdio.h>
#include <stdlib.h>

void stage_0(Block* blocks, size_t num_blocks, uint8_t q, uint8_t bitplane) {
    //Any remaining DC bits
    for(size_t i = 0; i < num_blocks; ++i) {
        if(3 <= bitplane && bitplane < q) {
            word_mapping_code((blocks[i].dc >> bitplane) & 1, 1, 0, 1);
        }
    }
}

void stage_1(SegmentHeader* headers, Block* blocks, size_t num_blocks, uint8_t bitplane) {

    uint32_t bitAC = headers->header_1.bitAC;

    for(size_t block_index = 0; block_index < num_blocks; ++block_index) {
        if(blocks[block_index].bitAC < bitplane) {
            continue;
        }

        uint64_t new_high_status_bit = 0;
        uint64_t new_low_status_bit = 0;

        for(size_t ac_index = 0; ac_index < AC_COEFFICIENTS_PER_BLOCK; ++ac_index) {
            uint32_t ac_coefficient = blocks[block_index].ac[ac_index] & ~(1<<bitAC);
            if(subband_lim(ac_index, bitplane)) {
                new_high_status_bit |= 1L << ac_index;
                new_low_status_bit |= 1L << ac_index;
            }
            else if((1<<(bitplane+1)) <= ac_coefficient) {
                new_high_status_bit |= 1L << ac_index;
            }
            else if((1<<bitplane) <= ac_coefficient && ac_coefficient < (1<<(bitplane+1))) {
                new_low_status_bit |= 1L << ac_index;
            }
        }
        block_set_status_with(&blocks[block_index], new_high_status_bit, new_low_status_bit);
        
        //types_p and signs_p
        uint8_t types_p = 0;
        uint8_t signs_p = 0;
        uint8_t size_s = 0;
        uint8_t size_p = 0;

        int8_t p0 = block_get_status(&blocks[block_index], 0);
        int8_t p1 = block_get_status(&blocks[block_index], 21);
        int8_t p2 = block_get_status(&blocks[block_index], 42);

        if(0 <= p0 && p0 <= 1) {
            types_p |= p0;
            size_p += 1;

            if(p0 == 1){
                signs_p |= (blocks[block_index].ac[0] >> bitAC) & 1;
                size_s += 1;
            }
        }

        if(0 <= p1 && p1 <= 1) {
            types_p <<= 1;
            types_p |= p1;
            size_p += 1;

            if(p1 == 1) {
                signs_p <<= 1;
                signs_p |= (blocks[block_index].ac[21] >> bitAC) & 1;
                size_s += 1;
            }
        }

        if(0 <= p2 && p2 <= 1) {
            types_p <<= 1;
            types_p |= p2;
            size_p += 1;

            if(p2 == 1) {
                signs_p <<= 1;
                signs_p |= (blocks[block_index].ac[42] >> bitAC) & 1;
                size_s += 1;
            }
        }

        if(size_p > 0) {
            word_mapping_code(types_p, size_p, 0, 0);
            if(size_s > 0) {
                word_mapping_code(signs_p, size_s, 0, 1);
            }
        }
    }
}

void stage_2(SegmentHeader* headers, Block* blocks, size_t num_blocks, uint8_t bitplane) {

    uint32_t bitAC = headers->header_1.bitAC;

    for(size_t block_index = 0; block_index < num_blocks; ++block_index) { 
        if(blocks[block_index].bitAC < bitplane) {
            continue;
        }

        //TRANB
        int8_t bmax = block_get_bmax(&blocks[block_index]);

        if(blocks[block_index].tran.b != 1 && bmax >= 0) {
            blocks[block_index].tran.b = bmax;
            word_mapping_code(blocks[block_index].tran.b, 1, 0, 1);
        }

        //TRAND
        if(blocks[block_index].tran.b != 0 && bmax != -1) {
            uint8_t tran_d = 0;
            uint8_t size = 0;

            uint8_t status_f0 = block_get_dmax(&blocks[block_index],0);
            uint8_t status_f1 = block_get_dmax(&blocks[block_index],1);
            uint8_t status_f2 = block_get_dmax(&blocks[block_index],2);

            uint8_t subband_mask = 0;
            subband_mask |=  block_get_dmax(&blocks[block_index], 0) == -1 ? 4 : 0;
            subband_mask |=  block_get_dmax(&blocks[block_index], 1) == -1 ? 2 : 0;
            subband_mask |=  block_get_dmax(&blocks[block_index], 2) == -1 ? 1 : 0;

            blocks[block_index].tran.d |= subband_mask;

            if((blocks[block_index].tran.d & 4) != 4 && status_f0 >= 0) {
                tran_d |= status_f0;
                blocks[block_index].tran.d |= 4*status_f0;
                size += 1;
            }

            if((blocks[block_index].tran.d & 2) != 2 && status_f1 >= 0) {
                tran_d <<= 1;
                tran_d |= status_f1;
                blocks[block_index].tran.d |= 2*status_f1;
                size += 1;
            }

            if((blocks[block_index].tran.d & 1) != 1 && status_f2 >= 0) {
                tran_d <<= 1;
                tran_d |= status_f2;
                blocks[block_index].tran.d |= status_f2;
                size += 1;
            }

            if(size != 0) {
                word_mapping_code(tran_d, size, size == 3 ? 1 : 0, 0);
            }
        }

        //types_c and signs_c
        for(size_t ci = 0; ci < 3; ++ci) {
            if((blocks[block_index].tran.d >> (2-ci) & 1) != 1) {
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
                        signs_c |= (blocks[block_index].ac[index] >> bitAC) & 1;
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

void stage_3(SegmentHeader* headers, Block* blocks, size_t num_blocks, uint8_t bitplane) {

    uint32_t bitAC = headers->header_1.bitAC;

    for(size_t block_index = 0; block_index < num_blocks; ++block_index) {

        if(blocks[block_index].tran.b == 0 || block_get_bmax(&blocks[block_index]) == -1) {
            continue;
        }

        if(blocks[block_index].bitAC < bitplane) {
            continue;
        }

        //TRANG
        uint8_t size = 0;
        uint8_t tran_g = 0;

        int8_t status_f0 = block_get_gmax(&blocks[block_index],0);
        int8_t status_f1 = block_get_gmax(&blocks[block_index],1);
        int8_t status_f2 = block_get_gmax(&blocks[block_index],2);
        
        uint8_t subband_mask = 0;
        subband_mask |= status_f0 == -1 ? 4 : 0;
        subband_mask |= status_f1 == -1 ? 2 : 0;
        subband_mask |= status_f2 == -1 ? 1 : 0;

        blocks[block_index].tran.g |= subband_mask;

        if((blocks[block_index].tran.d & 4) == 4 && (blocks[block_index].tran.g & 4) == 0) {
            blocks[block_index].tran.g |= 4 * status_f0;
            tran_g |= status_f0;
            size += 1;
		}

        if((blocks[block_index].tran.d & 2) == 2 && (blocks[block_index].tran.g & 2) == 0) {
            blocks[block_index].tran.g |= 2 * status_f1;
            tran_g <<= 1;
            tran_g |= status_f1;
            size += 1;
		}

        if((blocks[block_index].tran.d & 1) == 1 && (blocks[block_index].tran.g & 1) == 0) {
            blocks[block_index].tran.g |= status_f2;
            tran_g <<= 1;
            tran_g |= status_f2;
            size += 1;
		}

        if(size != 0) {
            word_mapping_code(tran_g, size, 0, 0);
        }

        //TRANH
        for(uint8_t hi = 0; hi < 3; ++hi) {
            if((blocks[block_index].tran.g >>(2-hi) & 1) == 0) {
                continue;
            }

            int8_t status_hi0 = block_get_hmax(&blocks[block_index], hi, 0);
            int8_t status_hi1 = block_get_hmax(&blocks[block_index], hi, 1);
            int8_t status_hi2 = block_get_hmax(&blocks[block_index], hi, 2);
            int8_t status_hi3 = block_get_hmax(&blocks[block_index], hi, 3);

            uint8_t subband_mask = 0;
            subband_mask |= status_hi0 == -1 ? 8 : 0;
            subband_mask |= status_hi1 == -1 ? 4 : 0;
            subband_mask |= status_hi2 == -1 ? 2 : 0;
            subband_mask |= status_hi3 == -1 ? 1 : 0;

            blocks[block_index].tran.h[hi] |= subband_mask;

            uint8_t tran_h = 0;
            uint8_t size = 0;

            if((blocks[block_index].tran.h[hi] & 8) == 0 && status_hi0 >= 0) {
                blocks[block_index].tran.h[hi] |= 8 * status_hi0;
                tran_h |= status_hi0;
                size += 1;
            }

            if((blocks[block_index].tran.h[hi] & 4) == 0 && status_hi1 >= 0) {
                blocks[block_index].tran.h[hi] |= 4 * status_hi1;
                tran_h <<= 1;
                tran_h |= status_hi1;
                size += 1;
            }

            if((blocks[block_index].tran.h[hi] & 2) == 0 && status_hi2 >= 0) {
                blocks[block_index].tran.h[hi] |= 2 * status_hi2;
                tran_h <<= 1;
                tran_h |= status_hi2;
                size += 1;
            }

            if((blocks[block_index].tran.h[hi] & 1) == 0 && status_hi3 >= 0) {
                blocks[block_index].tran.h[hi] |= status_hi3;
                tran_h <<= 1;
                tran_h |= status_hi3;
                size += 1;
            }

            if(size != 0) {
                word_mapping_code(tran_h, size, size < 4 ? 0 : 1, 0);
            }
        }

        //types_h and signs_h
        for(uint8_t hi = 0; hi < 3; ++hi) {
            if(((blocks[block_index].tran.g >> (2-hi)) & 1) == 0) {
                continue;
            }

            for(uint8_t hj = 0; hj < 4; ++hj) {

                if(((blocks[block_index].tran.h[hi] >> (3-hj)) & 1) == 0) {
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
                            signs_h |= (blocks[block_index].ac[index+j] >> bitAC) & 1;
                            size_s += 1;
                        }
                    }
                }
                if(size_h > 0) {
                    word_mapping_code(types_h, size_h, size_h < 4 ? 0 : 1, 0);
                    if(size_s > 0) {
                        word_mapping_code(signs_h, size_s, 0, 1);
                    }
                }
            }
        }
    }
}

void stage_4(SegmentHeader* headers, Block* blocks, size_t num_blocks, uint8_t bitplane) {

    for(size_t i = 0; i < num_blocks; ++i) {
        if(blocks[i].bitAC < bitplane) {
            continue;
        }

        for(size_t pi = 0; pi < 3; ++pi) {
            size_t index = pi * 21;
            if(block_get_status(&blocks[i], index) == 2) {
                uint8_t temp = blocks[i].ac[index] >> bitplane & 1;
                word_mapping_code(temp, 1, 0, 1);
            }
        }
        for(size_t ci = 0; ci < 3; ++ci) {
            for(size_t j = 0; j < 4; ++j) {
                size_t index = 1 + ci * 21 + j;
                if(block_get_status(&blocks[i], index) == 2) {
                    uint8_t temp = blocks[i].ac[index] >> bitplane & 1;
                    word_mapping_code(temp, 1, 0, 1);
                }
            }
        }

        for(size_t hi = 0; hi < 3; ++hi) {
            for(size_t hj = 0; hj < 4; ++hj) {
                for(size_t j = 0; j < 4; ++j) {
                    size_t index = 5+hi*21+hj*4+j;
                    if(block_get_status(&blocks[i], index) == 2) {
                        uint8_t temp = blocks[i].ac[index] >> bitplane & 1;
                        word_mapping_code(temp, 1, 0, 1);
                    }
                }
            }
        }
    }
}
