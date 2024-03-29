#ifndef WORD_MAPPING_H
#define WORD_MAPPING_H

#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

struct BlockString;

void word_mapping_code(uint8_t word, uint8_t word_length, uint8_t symbol_option, uint8_t uncoded);
void set_block_string(BlockString* new_block_string);
void write_block_string(void);
void reset_block_string(void);
void block_string_initialize(void);
void block_string_free(void);
uint32_t get_bitstring_length();

#ifdef __cplusplus
}
#endif
#endif //WORD_MAPPING_H
