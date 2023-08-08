#ifndef WORD_MAPPING_H
#define WORD_MAPPING_H

#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

void word_mapping_code(uint8_t word, uint8_t word_length, uint8_t symbol_option, uint8_t uncoded);
void write_block_string();
void reset_block_string();

#ifdef __cplusplus
}
#endif
#endif //WORD_MAPPING_H
