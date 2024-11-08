#ifndef BLOCK_TRANSFORM_H
#define BLOCK_TRANSFORM_H

#include "common.h"
#include <stdint.h>
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif

void block_transform_pack(Block* blocks, int32_t* dc_coefficients, size_t num_blocks, int16_t* data, size_t data_width);

#ifdef __cplusplus
}
#endif
#endif //BLOCK_TRANSFORM_H
