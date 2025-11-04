// Original copyright: Aalto University
// Modifications copyright: Huld Ltd.
// Project: EnVisS ASW (for Comet Interceptor mission)

#ifndef SUBBAND_H
#define SUBBAND_H

#include "segment_header.h"
#include <stddef.h>

#ifdef	__cplusplus
extern "C" {
#endif

void subband_scale(SegmentHeader* headers, int32_t* data, size_t width, size_t height);

#ifdef __cplusplus
}
#endif
#endif //SUBBAND_H
