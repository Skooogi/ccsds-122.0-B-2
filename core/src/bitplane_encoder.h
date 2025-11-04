// Original copyright: Aalto University
// Modifications copyright: Huld Ltd.
// Project: EnVisS ASW (for Comet Interceptor mission)

#ifndef BITPLANE_ENCODER_H
#define BITPLANE_ENCODER_H

#include "segment_header.h"
#include "common.h"

#ifdef __cplusplus
extern "C" {
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
