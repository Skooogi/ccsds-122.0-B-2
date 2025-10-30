// Original copyright: Aalto University
// Modifications copyright: Huld Ltd.
// Project: EnVisS ASW (for Comet Interceptor mission)

#ifndef BITPLANE_ENCODER_H
#define BITPLANE_ENCODER_H

#include "segment_header.h"
//#include "image_data.h"
#include "common.h"

#ifdef __cplusplus
extern "C" {
#endif

#ifndef LIMIT_COMPRESSION_TO_SMALL_IMAGES
    #define BITPLANE_ENCODER_MAX_NUM_COEFFS (65536)
#else
    #define BITPLANE_ENCODER_MAX_NUM_COEFFS (1024)
#endif

void bitplane_encoder_encode(
    int32_t* data,
    SegmentHeader* headers,
    int32_t *dc_coefficients,
    Block *blocks,
    BlockString *block_strings);


#ifdef __cplusplus
}
#endif
#endif //BITPLANE_ENCODER_H
