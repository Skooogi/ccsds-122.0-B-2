#include "encoding_stages.h"
#include "word_mapping.h"
#include <stdlib.h>

void stage_0(Block* blocks, size_t num_blocks, uint8_t q, uint8_t bitplane) {
    //Any remaining DC bits
    for(size_t i = 0; i < num_blocks; ++i) {
        if(3 <= bitplane && bitplane < q) {
            word_mapping_code((blocks[i].dc >> bitplane) & 1, 1, 0, 1);
        }
    }
}

void stage_1(Block* blocks, size_t num_blocks, uint8_t bitplane) {

    for(size_t block_index = 0; block_index < num_blocks; ++block_index) {
        if(blocks[block_index].bitAC < bitplane) {
            continue;
        }

        //Set each coefficient state
        uint64_t new_status_1 = 0;
        uint64_t new_status_2 = 0;

        for(size_t ac_index = 0; ac_index < AC_COEFFICIENTS_PER_BLOCK; ++ac_index) {
            if(subband_lim(ac_index, bitplane)) {
                new_status_1 |= 1 << ac_index;
                new_status_2 |= 1 << ac_index;
            }
            else if((1<<(bitplane+1)) <= abs(blocks[block_index].ac[ac_index])) {
                new_status_1 |= 1 << ac_index;
            }
            else if((1<<bitplane) <= abs(blocks[block_index].ac[ac_index]) && abs(blocks[block_index].ac[ac_index]) < (1<<(bitplane+1))) {
                new_status_2 |= 1 << ac_index;
            }
        }
        block_set_status_with(&blocks[block_index], new_status_1, new_status_2);
        
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
                signs_p |= blocks[block_index].ac[0] < 0 ? 1 : 0;
                size_s += 1;
            }
        }

        if(0 <= p1 && p1 <= 1) {
            types_p <<= 1;
            types_p |= p1;
            size_p += 1;

            if(p1 == 1) {
                signs_p <<= 1;
                signs_p |= blocks[block_index].ac[21] < 0 ? 1 : 0;
                size_s += 1;
            }
        }

        if(0 <= p2 && p2 <= 1) {
            types_p <<= 1;
            types_p |= p2;
            size_p += 1;

            if(p2 == 1) {
                signs_p <<= 1;
                signs_p |= blocks[block_index].ac[42] < 0 ? 1 : 0;
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
