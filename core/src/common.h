#ifndef COMMON_H
#define COMMON_H

#include "segment_header.h"
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#ifdef __cplusplus
extern "C" {
#endif

#define AC_COEFFICIENTS_PER_BLOCK 63
#define BLOCKS_PER_GAGGLE 16
#define BLOCKS_PER_SEGMENT 32

#define MAPPED_WORDS_PER_STAGE 512

typedef union Tran {
    struct {
        unsigned b  : 1;
        unsigned d  : 4;
        unsigned g  : 3;
        uint8_t h[3];
    };
    uint32_t packed;
} Tran;

typedef struct Block {
    uint8_t bitAC;
    Tran tran;
    int32_t ac[AC_COEFFICIENTS_PER_BLOCK]; 
    union {
        uint64_t high_status_bit;
        uint8_t high_statuses[8];
    };
    union {
        uint64_t low_status_bit;
        uint8_t low_statuses[8];
    };
} Block;

typedef struct MappedWord {
    unsigned length : 2;
    unsigned symbol_option : 1;
    unsigned uncoded : 1;
    unsigned mapped_symbol : 4;
} MappedWord;

//Exists for each gaggle. Reset every bitplane.
typedef struct BlockString {
    uint8_t written_code_options;
    uint8_t stage; //Only for stages 1 - 3
    MappedWord mapped_words[3][MAPPED_WORDS_PER_STAGE]; //Mapped words per stage 1-3
    uint32_t index[3];
    uint32_t string_length_2_bit[2];
    uint32_t string_length_3_bit[3];
    uint32_t string_length_4_bit[4];
} BlockString;

//Is reused and overwritten for each segment.
typedef struct SegmentData {

    size_t block_offset;
    size_t num_gaggles;
    uint8_t q;
    uint8_t bitplane;

    SegmentHeader* headers;
    int32_t* dc_coefficients;
    Block* blocks;
    BlockString* block_strings;

} SegmentData;

//Block operations
bool subband_lim(uint8_t ac_index, uint8_t bitplane);
void block_set_status_with(Block* block, uint64_t high_status_bit, uint64_t low_status_bit);
void block_set_status(Block* block, uint8_t ac_index, int8_t value);
int8_t block_get_status(Block* block, uint8_t ac_index);
uint8_t block_get_bmax(Block* block);
uint8_t block_get_dmax(Block* block, uint8_t family);
uint8_t block_get_gmax(Block* block, uint8_t family);
uint8_t block_get_hmax(Block* block, uint8_t family, uint8_t quadrant);

//Math operations
static inline int32_t max(int32_t a, int32_t b) {  return (a > b) ? a : b; }
static inline int32_t min(int32_t a, int32_t b) {  return (a < b) ? a : b; }
uint32_t log2_32(uint32_t value);
uint32_t log2_32_ceil(uint32_t value);
uint32_t twos_complement(int32_t value, size_t num_bits);

#ifdef __cplusplus
}
#endif
#endif //COMMON_H
