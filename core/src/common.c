#include "common.h"
#include <stdio.h>

uint32_t log2_32 (uint32_t value) {
    uint32_t result = 0;
    while(value >>= 1) result ++;
    return result;
}

uint32_t log2_32_ceil (uint32_t value) {
    uint32_t result = 0;
    while(value > 1<<result) result ++;
    return result;
}

uint32_t twos_complement(int32_t value, size_t num_bits) {
    if(value & (1 << num_bits)) {
        return (~(value) + 1) & ((1<<num_bits)-1);
    }
    return value;
}

bool subband_lim(uint8_t ac_index, uint8_t bitplane) {

    static uint64_t sub_map[3] = {
        0b1111111111111111111111111111111111111111111111100000000000000000,
        0b1111100000000000000001111100000000000000001000000000000000000000,
        0b1000000000000000000001000000000000000000000000000000000000000000
    };

    // Checks whether or not ac coefficient scaling means bitplane is necessarily 0.
    // If it is, it is not encoded.
    // Figure 3-4
    if(bitplane > 2) {
        return false;
    }

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
static uint8_t state_map_inv_1[4] = { 0,0,1,1 };
static uint8_t state_map_inv_2[4] = { 0,1,0,1 };
static uint64_t b_mask = 0x7ffffbffffdffffe;
static uint64_t d_mask = 0x1ffffe;
static uint64_t g_mask = 0x1fffe0;
static uint64_t h_mask = 0x1e0;

//Set the whole block status at a time.
void block_set_status_with(Block* block, uint64_t high_status_bit, uint64_t low_status_bit) {
    block->high_status_bit = high_status_bit;
    block->low_status_bit = low_status_bit;
}

//Set a single ac status.
void block_set_status(Block* block, uint8_t ac_index, int8_t value) {
    block->high_status_bit = (block->high_status_bit & ~(1LL << ac_index)) | (state_map_inv_1[value] << ac_index);
    block->low_status_bit = (block->low_status_bit & ~(1LL << ac_index)) | (state_map_inv_2[value] << ac_index);
}

//Transforms the status bits back to a value.
int8_t block_get_status(Block* block, uint8_t ac_index) {
    return state_map[((block->high_status_bit >> ac_index) & 1) * 2 + ((block->low_status_bit >> ac_index) & 1)];
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
    return (filtered >> 21*family & d_mask) > 0;
}

//Status of the grandchildren of a single family.
uint8_t block_get_gmax(Block* block, uint8_t family) {
    uint64_t filtered = (~block->high_status_bit & block->low_status_bit);
    return (filtered >> 21*family & g_mask) > 0;
}

//Status of one quadrant of grandchildren of a single family. 
uint8_t block_get_hmax(Block* block, uint8_t family, uint8_t quadrant) {
    uint64_t filtered = (~block->high_status_bit & block->low_status_bit);
    return (filtered >> (21*family + quadrant * 4) & h_mask) > 0;
}
