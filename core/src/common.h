#ifndef COMMON_H
#define COMMON_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#ifdef __cplusplus
extern "C" {
#endif

#define AC_COEFFICIENTS_PER_BLOCK 63
#define BLOCKS_PER_GAGGLE 16

typedef struct Block {
    unsigned bitAC  : 5;
    int32_t dc;
    int32_t ac[AC_COEFFICIENTS_PER_BLOCK]; 
    uint64_t high_status_bit;
    uint64_t low_status_bit;
} Block;

typedef struct MappedWord {
    unsigned word : 4;
    unsigned length : 2;
    unsigned symbol_option : 1;
    unsigned uncoded : 1;
    signed mapped_symbol : 8;
} MappedWord;

typedef struct BlockString {
    uint8_t code_option_bit_2;
    uint8_t code_option_bit_3;
    uint8_t code_option_bit_4;
    MappedWord mapped_words[1024];
    uint16_t index;
} BlockString;

//Block operations
bool subband_lim(uint8_t ac_index, uint8_t bitplane);
void block_set_status_with(Block* block, uint64_t high_status_bit, uint8_t low_status_bit);
void block_set_status(Block* block, uint8_t ac_index, int8_t value);
uint8_t block_get_status(Block* block, uint8_t ac_index);
int8_t block_get_bmax(Block* block, uint8_t ac_index);
int8_t block_get_dmax(Block* block, uint8_t family);
int8_t block_get_gmax(Block* block, uint8_t family);
int8_t block_get_hmax(Block* block, uint8_t family, uint8_t quadrant);

//Math operations
inline int32_t max(int32_t a, int32_t b) {  return (a > b) ? a : b; }
inline int32_t min(int32_t a, int32_t b) {  return (a < b) ? a : b; }
uint32_t log2_32 (uint32_t value);
uint32_t twos_complement(int32_t value, size_t num_bits);

#ifdef __cplusplus
}
#endif
#endif //COMMON_H
