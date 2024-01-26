#ifndef BITPLANE_ENCODER_H
#define BITPLANE_ENCODER_H

#include "segment_header.h"

#ifdef __cplusplus
extern "C" {
#endif

void bitplane_encoder_encode(int16_t* data, SegmentHeader* headers);

#ifdef __cplusplus
}
#endif
#endif //BITPLANE_ENCODER_H
