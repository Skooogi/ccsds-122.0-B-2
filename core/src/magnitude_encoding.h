#ifndef MAGNITUDE_ENCODING_H
#define MAGNITUDE_ENCODING_H

#include "common.h"

#ifdef __cplusplus
extern "C" {
#endif

void encode_ac_magnitudes(Block* blocks, size_t num_blocks, uint32_t bitAC_max, uint32_t q);
void encode_dc_magnitudes(int32_t* dc_coefficients, int32_t num_coeffs, int32_t bitDC, int32_t q);

#ifdef __cplusplus
}
#endif
#endif //MAGNITUDE_ENCODING_H
