// Original copyright: Aalto University
// Modifications copyright: Huld Ltd.
// Project: EnVisS ASW (for Comet Interceptor mission)

#include "common.h"

uint32_t log2_32 (uint32_t value) {
    uint32_t result = 0;
    while(value >>= 1) result ++;
    return result;
}

uint32_t log2_32_ceil (uint32_t value) {
    uint32_t result = 0;
    while(value > (uint32_t) (1<<result)) result ++;
    return result;
}

uint32_t twos_complement(int32_t value, size_t num_bits) {
    if(value & (1 << num_bits)) {
        return (uint32_t) ((~(value) + 1) & ((1<<num_bits)-1));
    }
    return (uint32_t) value;
}

bool subband_lim(uint8_t ac_index, uint8_t bitplane) {

    static uint64_t sub_map[3] = {
        0b1111111111111111111111111111111111111111111111100000000000000000ULL,
        0b1111111111100000000000000000000000000000000000000000000000000000ULL,
        0b1100000000000000000000000000000000000000000000000000000000000000ULL
    };

    return sub_map[bitplane] >> (63 - ac_index) & 1;
}

/*
 * BLOCK OPERATIONS
 *
 * Block saves the state -1...2 of each coefficient in two 64b values.
 * One is for high bits and one for low bits.
 * For each 64b the coefficient state is mapped from the least significant bit as follows:
 * 1 x Parent
 * 4 x Children
 * 16 x Grandchildren
 *
 * (MSB) HHHH HHHH HHHH HHHH CCCC P (LSB)
 *
 * This is then repeated for each family F0,F1 and F2.
 * The whole state of the block is saved as:
 * uint64_t high_status_bit = (MSB) HHHH HHHH HHHH HHHH CCCC P HHHH HHHH HHHH HHHH CCCC P HHHH HHHH HHHH HHHH CCCC P (MSB)
 * uint64_t low _status_bit = (MSB) HHHH HHHH HHHH HHHH CCCC P HHHH HHHH HHHH HHHH CCCC P HHHH HHHH HHHH HHHH CCCC P (MSB)
 *                                                           ^                          ^                          ^
 * ac index                                                  42                         21                         0
*/

static int8_t state_map[4] = { 0,1,2,-1 };

static uint64_t b_mask =  0b0000111111111111111111111111111111111111111111111111111111111111ULL;
static uint64_t c_mask =  0b0000111100000000000000000000000000000000000000000000000000000000ULL;
static uint64_t g_mask =  0b0000000000000000111111111111111100000000000000000000000000000000ULL;
static uint64_t h_mask =  0b0000000000000000111100000000000000000000000000000000000000000000ULL;
//Set the whole block status at a time.
void block_set_status_with(Block* block, uint64_t high_status_bit, uint64_t low_status_bit) {
    block->high_status_bit = high_status_bit;
    block->low_status_bit = low_status_bit;
}

//Transforms the status bits back to a value.
int8_t block_get_status(Block* block, uint8_t ac_index) {
    return state_map[((block->high_status_bit >> (62-ac_index)) & 1) * 2 + ((block->low_status_bit >> (62-ac_index)) & 1)];
}

//All get_*max functions return:
//0 when all ac coefficients are 0.
//1 when even one ac coefficient is 1.
//(Figure 4-1)

//Status of whole block.
uint8_t block_get_bmax(Block* block) {
    uint64_t filtered = (~block->high_status_bit & block->low_status_bit) & b_mask;
    return (filtered > 0);
}

//Status of descendants of a single family. Descendants = Children + Grandchildren.
uint8_t block_get_dmax(Block* block, uint8_t family) {
    uint64_t filtered = (~block->high_status_bit & block->low_status_bit);
    return (filtered & ( (c_mask >> (4*family)) | ((g_mask) >> 16*family)) ) > 0;
}

//Status of the grandchildren of a single family.
uint8_t block_get_gmax(Block* block, uint8_t family) {
    uint64_t filtered = (~block->high_status_bit & block->low_status_bit);
    return (filtered & (g_mask >> (16*family))) > 0;
}

//Status of one quadrant of grandchildren of a single family.
uint8_t block_get_hmax(Block* block, uint8_t family, uint8_t quadrant) {
    uint64_t filtered = (~block->high_status_bit & block->low_status_bit);
    return (filtered & (h_mask >> (16*family + quadrant*4))) > 0;
}
