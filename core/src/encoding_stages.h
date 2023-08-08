#ifndef ENCODING_STAGES_H
#define ENCODING_STAGES_H

#include "common.h"
#include <stdint.h>
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif

void stage_0(Block* blocks, size_t num_blocks, uint8_t q, uint8_t bitplane);
void stage_1(Block* blocks, size_t num_blocks, uint8_t bitplane);
#ifdef __cplusplus
}
#endif
#endif //ENCODING_STAGES_H
